import os
import random
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from art import text2art

BOARD_SIZE = 10
SHIP_SIZES = {'C': 5, 'B': 4, 'R': 3, 'S': 3, 'D': 2}
HIT_SYMBOL = 'X'
MISS_SYMBOL = 'O'
EMPTY_SYMBOL = '.'
SHIP_SYMBOLS = SHIP_SIZES.keys()
COLUMN_LABELS = 'ABCDEFGHIJ'
DEBUG_MODE = False

def debug_log(message, console, level="info"):
    if DEBUG_MODE:
        style = "bold green" if level == "info" else "bold red"
        text = Text(f"[{level.upper()}] {message}", style=style)
        console.print(Panel(text))

def clear_screen():
    print("\033[H", end='')

def actual_clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_instructions(console):
    instructions = [
        "1. The game is played on a 10 x 10 grid, where you place your fleet of ships.",
        "2. The fleet includes different ships: Carrier (C), Battleship (B), Cruiser (R), Submarine (S), and Destroyer (D).",
        "3. You can place your ships either horizontally or vertically, but they cannot overlap or be placed diagonally.",
        "4. Once all ships are placed, you take turns with the AI to attack each other's fleet by calling out the coordinates.",
        "5. The game continues until one player's fleet is entirely sunk.",
        "6. Enter coordinates in the format 'LetterNumber', e.g., 'A1', 'B5', etc.",
        "7. After each turn, the board is updated showing hits (X), misses (O), and unknown areas (.)."
    ]
    console.print("Battleship Game Instructions:", style="bold underline")
    for instruction in instructions:
        console.print(instruction)
    console.print("Good luck and have fun!", style="bold green")

def coordinate_to_position(coordinate):
    if len(coordinate) < 2 or not coordinate[0].isalpha() or not coordinate[1:].isdigit():
        return None
    col = COLUMN_LABELS.find(coordinate[0].upper())
    row = int(coordinate[1:]) - 1
    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
        return row, col
    return None

def safe_input(prompt, input_type, validation_func):
    while True:
        try:
            user_input = input_type(input(prompt))
            if validation_func(user_input):
                return user_input
            else:
                print("Invalid input. Please try again.")
        except ValueError:
            print("Invalid input. Please try again.")

class Board:
    def __init__(self):
        self.grid = [[EMPTY_SYMBOL for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.ships = {symbol: size for symbol, size in SHIP_SIZES.items()}
        self.ship_hits = {symbol: 0 for symbol in SHIP_SIZES.keys()}

    def display(self, console, show_ships=True):
        table = self._create_table()
        for row_index, row in enumerate(self.grid):
            table.add_row(*self._format_row(row_index, row, show_ships))
            if row_index < BOARD_SIZE - 1:
                table.add_row(*([" "] * (BOARD_SIZE + 1)))
        console.print(table)

    def is_valid_placement(self, size, row, col, horizontal):
        if horizontal:
            return col + size <= BOARD_SIZE and all(self.grid[row][col + i] == EMPTY_SYMBOL for i in range(size))
        else:
            return row + size <= BOARD_SIZE and all(self.grid[row + i][col] == EMPTY_SYMBOL for i in range(size))

    def place_ship(self, symbol, size, row, col, horizontal):
        for i in range(size):
            self._place_ship_part(symbol, row, col, i, horizontal)

    def _place_ship_part(self, symbol, row, col, index, horizontal):
        if horizontal:
            self.grid[row][col + index] = symbol
        else:
            self.grid[row + index][col] = symbol

    def receive_attack(self, row, col):
        if self.grid[row][col] in [HIT_SYMBOL, MISS_SYMBOL]:
            return None
        return self._process_attack(row, col)

    def _process_attack(self, row, col):
        cell = self.grid[row][col]
        if cell in SHIP_SYMBOLS:
            self._update_hit(row, col, cell)
            return True
        else:
            self.grid[row][col] = MISS_SYMBOL
            return False

    def _update_hit(self, row, col, cell):
        self.grid[row][col] = HIT_SYMBOL
        self.ship_hits[cell] += 1

    def has_ships_remaining(self):
        return any(cell in SHIP_SYMBOLS for row in self.grid for cell in row)

    def is_adjacent(self, row, col):
        return any(self._is_ship_adjacent(row, col, dr, dc) for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)])

    def _create_table(self):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column(" ")
        for label in COLUMN_LABELS:
            table.add_column(f"[bold cyan]{label}[/]", justify="center")
        return table

    def _format_row(self, row_index, row, show_ships):
        cells = [f"[bold cyan]{row_index + 1}[/]"]
        for cell in row:
            cells.append(self._format_cell(cell, show_ships))
        return cells

    def _format_cell(self, cell, show_ships):
        display_cell = EMPTY_SYMBOL if (cell in SHIP_SYMBOLS and not show_ships) else cell
        cell_style = self._get_cell_style(display_cell)
        return f"[{cell_style}] {display_cell} [/]"

    def _get_cell_style(self, cell):
        if cell in SHIP_SYMBOLS:
            return "bright_black on bright_black"
        elif cell == HIT_SYMBOL:
            return "bright_red on black"
        elif cell == MISS_SYMBOL:
            return "bright_blue on black"
        return "grey on black"
    
    def _is_ship_adjacent(self, row, col, dr, dc):
        r, c = row + dr, col + dc
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.grid[r][c] in SHIP_SYMBOLS

    def place_ship_with_validation(self, symbol, size, row, col, horizontal):
        if not self.is_valid_placement(size, row, col, horizontal) or self._is_placement_adjacent(size, row, col, horizontal):
            return False
        self.place_ship(symbol, size, row, col, horizontal)
        return True

    def _is_placement_adjacent(self, size, row, col, horizontal):
        for i in range(size):
            if horizontal and self.is_adjacent(row, col + i):
                return True
            if not horizontal and self.is_adjacent(row + i, col):
                return True
        return False

def player_place_ships(board, console):
    global DEBUG_MODE
    console.print("Do you want to place your ships manually or automatically? (Type 'manual' or 'auto')")
    placement_choice = input().lower().strip()
    if placement_choice == 'auto':
        actual_clear()
        ai_place_ships(board)
        return
    elif placement_choice == 'debug':
        actual_clear()
        DEBUG_MODE = True
        ai_place_ships(board)
        return
    actual_clear()
    board.display(console)

    for symbol, size in SHIP_SIZES.items():
        while True:
            console.print(f"Placing {symbol} (Size: {size})")
            coordinate = safe_input("Enter starting coordinate (e.g., A3): ", str, lambda x: coordinate_to_position(x) is not None)
            direction = safe_input("Enter direction (h for horizontal, v for vertical): ", str, lambda x: x in ['h', 'v'])
            row, col = coordinate_to_position(coordinate)
            if board.place_ship_with_validation(symbol, size, row, col, direction == 'h'):
                actual_clear()
                board.display(console)
                break
            else:
                console.print("Invalid placement. Try again.")

def ai_place_ships(board):
    for symbol, size in SHIP_SIZES.items():
        while True:
            row = random.randint(0, BOARD_SIZE - 1)
            col = random.randint(0, BOARD_SIZE - 1)
            horizontal = random.choice([True, False])
            if board.place_ship_with_validation(symbol, size, row, col, horizontal):
                break

def move_cursor_up(lines=1):
    print(f"\033[{lines}A", end='')
def clear_line():
    print("\033[K", end='')

def player_turn(opponent_board, console):
    console.print("Your turn! Enter a coordinate (e.g., B4):")
    if DEBUG_MODE:
        return
    while True:
        coordinate = input().strip()
        position = coordinate_to_position(coordinate)
        if position is None:
            move_cursor_up(1)
            clear_line()
            move_cursor_up(1)
            clear_line()
            console.print("Invalid coordinate. Please try again.")
            continue

        row, col = position
        result = opponent_board.receive_attack(row, col)
        if result is None:
            move_cursor_up(1)
            clear_line()
            move_cursor_up(1)
            clear_line()
            console.print("You've already attacked this coordinate. Choose a different target.", style="bold red")
        else:
            move_cursor_up(1)
            clear_line()
            move_cursor_up(1)
            clear_line()
            break

def ai_turn(player_board, console, ai_state):
    debug_log(f"Starting AI turn. Current AI state: {ai_state}", console)

    time.sleep(1)

    if ai_state['mode'] == 'target':
        handle_ai_target_mode(player_board, console, ai_state)
    elif ai_state['mode'] == 'hunt':
        handle_ai_hunt_mode(player_board, console, ai_state)

    debug_log(f"AI turn complete. Updated AI state: {ai_state}", console)
    if DEBUG_MODE and ai_state['mode'] == 'target':
        input()
    return ai_state

def handle_ai_hunt_mode(player_board, console, ai_state):
    while True:
        row, col = random.randint(0, BOARD_SIZE - 1), random.randint(0, BOARD_SIZE - 1)
        if (row + col) % 2 == 0 and player_board.grid[row][col] not in [HIT_SYMBOL, MISS_SYMBOL]:
            result = player_board.receive_attack(row, col)
            if result:
                ai_state['mode'] = 'target'
                ai_state['last_hit'] = [(row, col)]
                ai_state['direction'] = None
                debug_log(f"AI made a hit on {ai_state['last_hit']}", console)
                debug_log(f"Switching to 'target' mode.", console)
            break

def handle_ai_target_mode(player_board, console, ai_state):
    if len(ai_state['last_hit']) > 1:
        determine_ai_ship_direction(ai_state, console)
        attack_positions = calculate_ai_attack_positions(ai_state, player_board, console)

        if not attack_positions:
            switch_to_hunt_mode(ai_state, console)
        else:
            attack_ai_target_positions(attack_positions, player_board, ai_state, console)

    elif len(ai_state['last_hit']) == 1:
        attack_surrounding_cells(ai_state, player_board, console)

def determine_ai_ship_direction(ai_state, console):
    if ai_state['last_hit'][0][0] == ai_state['last_hit'][1][0]:
        ai_state['direction'] = 'horizontal'
    else:
        ai_state['direction'] = 'vertical'
    debug_log(f"Ship direction determined: {ai_state['direction']}", console)

def calculate_ai_attack_positions(ai_state, player_board, console):
    attack_positions = []
    if ai_state['direction'] == 'horizontal':
        leftmost, rightmost = get_extreme_hits(ai_state, key=lambda x: x[1])
        debug_log(f"Determined leftmost and rightmost hits: {leftmost}, {rightmost}", console)
        attack_positions = get_horizontal_attack_positions(leftmost, rightmost, player_board)

    elif ai_state['direction'] == 'vertical':
        topmost, bottommost = get_extreme_hits(ai_state, key=lambda x: x[0])
        debug_log(f"Determined topmost and bottommost hits: {topmost}, {bottommost}", console)
        attack_positions = get_vertical_attack_positions(topmost, bottommost, player_board)

    debug_log(f"[Debug] Generated attack positions: {attack_positions}", console)
    return attack_positions

def get_horizontal_attack_positions(leftmost, rightmost, player_board):
    attack_positions = []
    if leftmost[1] > 0 and player_board.grid[leftmost[0]][leftmost[1] - 1] not in [HIT_SYMBOL, MISS_SYMBOL]:
        attack_positions.append((leftmost[0], leftmost[1] - 1))
    if rightmost[1] < BOARD_SIZE - 1 and player_board.grid[rightmost[0]][rightmost[1] + 1] not in [HIT_SYMBOL, MISS_SYMBOL]:
        attack_positions.append((rightmost[0], rightmost[1] + 1))
    return attack_positions

def get_vertical_attack_positions(topmost, bottommost, player_board):
    attack_positions = []
    if topmost[0] > 0 and player_board.grid[topmost[0] - 1][topmost[1]] not in [HIT_SYMBOL, MISS_SYMBOL]:
        attack_positions.append((topmost[0] - 1, topmost[1]))
    if bottommost[0] < BOARD_SIZE - 1 and player_board.grid[bottommost[0] + 1][bottommost[1]] not in [HIT_SYMBOL, MISS_SYMBOL]:
        attack_positions.append((bottommost[0] + 1, bottommost[1]))
    return attack_positions

def attack_ai_target_positions(attack_positions, player_board, ai_state, console):
    for row, col in attack_positions:
        if player_board.grid[row][col] not in [HIT_SYMBOL, MISS_SYMBOL]:
            result = player_board.receive_attack(row, col)
            
            if result:
                ai_state['last_hit'].append((row, col))
                if not player_board.has_ships_remaining():
                    switch_to_hunt_mode(ai_state, console)
            break

def get_extreme_hits(ai_state, key):
    return min(ai_state['last_hit'], key=key), max(ai_state['last_hit'], key=key)

def switch_to_hunt_mode(ai_state, console):
    ai_state['mode'] = 'hunt'
    ai_state['last_hit'] = []
    ai_state['direction'] = None
    debug_log("No more attack positions. Ship confirmed sunk. Switching to Hunt mode.", console)

def attack_surrounding_cells(ai_state, player_board, console):
    for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
        r, c = ai_state['last_hit'][0][0] + dr, ai_state['last_hit'][0][1] + dc
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and player_board.grid[r][c] not in [HIT_SYMBOL, MISS_SYMBOL]:
            debug_log(f"Attacking Surrounding Cells: ({r}, {c})", console)
            result = player_board.receive_attack(r, c)
            if result:
                ai_state['last_hit'].append((r, c))
            return ai_state

def setup_game():
    console = Console()
    player_board, ai_board = Board(), Board()
    message, styles = text2art("\n" + r"Welcome to Battleship!" + "\n"), "dark_turquoise"
    message = Text(message)
    console.print(message, style=styles)
    display_instructions(console)
    input("...")
    player_place_ships(player_board, console)
    ai_place_ships(ai_board)
    return player_board, ai_board, console

def show_summary_screen(console, player_board, ai_board, player_won):
    display_end_game_message(console, player_won)
    display_game_statistics(console, player_board, ai_board)

def display_end_game_message(console, player_won):
    if player_won:
        message, styles = text2art("You Win!"), "bold yellow"
    else:
        message, styles = text2art("You Lose!"), "bold red"
    message = Text(message)
    console.print(message, style=styles)

def display_game_statistics(console, player_board, ai_board):
    player_hits, ai_hits = sum(cell == HIT_SYMBOL for row in ai_board.grid for cell in row), sum(cell == HIT_SYMBOL for row in player_board.grid for cell in row)
    player_misses, ai_misses = sum(cell == MISS_SYMBOL for row in ai_board.grid for cell in row), sum(cell == MISS_SYMBOL for row in player_board.grid for cell in row)

    stats_table = Table(title="Game Statistics", show_header=True, header_style="bold green")
    stats_table.add_column("Player", style="bold magenta")
    stats_table.add_column("Hits", justify="right")
    stats_table.add_column("Misses", justify="right")

    stats_table.add_row("You", str(player_hits), str(player_misses))
    stats_table.add_row("AI", str(ai_hits), str(ai_misses))

    console.print(stats_table)

def game_loop(player_board, ai_board, console):
    ai_state = {'mode': 'hunt', 'last_hit': []}
    while player_board.has_ships_remaining() and ai_board.has_ships_remaining():
        clear_screen()
        if DEBUG_MODE: 
            actual_clear()
        display_boards(console, player_board, ai_board, show_ships=False)

        player_turn(ai_board, console)
        clear_screen()
        if DEBUG_MODE: 
            actual_clear()
        display_boards(console, player_board, ai_board, show_ships=False)
        if not ai_board.has_ships_remaining():
            break

        ai_state = ai_turn(player_board, console, ai_state)
        clear_screen()
        if DEBUG_MODE: 
            actual_clear()
        display_boards(console, player_board, ai_board, show_ships=False)
        if not player_board.has_ships_remaining():
            break

    player_won = not ai_board.has_ships_remaining()
    show_summary_screen(console, player_board, ai_board, player_won)

def display_boards(console, player_board, ai_board, show_ships):
    console.print("Enemy Board:" + " " * 30), ai_board.display(console, show_ships=show_ships)
    console.print("Your Board:" + " " * 30), player_board.display(console)


player_board, ai_board, console = setup_game()
game_loop(player_board, ai_board, console)
