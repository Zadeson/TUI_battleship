import os
import random
import time
import winsound
from rich.console import Console
from rich.table import Table

# Constants
BOARD_SIZE = 10
SHIP_SIZES = {'C': 5, 'B': 4, 'R': 3, 'S': 3, 'D': 2}  # Carrier, Battleship, Cruiser, Submarine, Destroyer
HIT_SYMBOL = 'X'
MISS_SYMBOL = 'O'
EMPTY_SYMBOL = '.'
SHIP_SYMBOLS = SHIP_SIZES.keys()
COLUMN_LABELS = 'ABCDEFGHIJ'
SOUND_EFFECTS_ENABLED = True


def coordinate_to_position(coordinate):
    if len(coordinate) < 2 or not coordinate[0].isalpha() or not coordinate[1:].isdigit():
        return None
    col = COLUMN_LABELS.find(coordinate[0].upper())
    row = int(coordinate[1:]) - 1
    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
        return row, col
    return None


def beep_sound(frequency, duration):
    if SOUND_EFFECTS_ENABLED:
        try:
            winsound.Beep(frequency, duration)
        except:
            pass


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def safe_input(prompt, cast_type, validator=None):
    console = Console()
    while True:
        try:
            console.print(f"[bold yellow]{prompt}[/]", end='')
            value = cast_type(input())
            if validator and not validator(value):
                raise ValueError
            return value
        except ValueError:
            console.print("[bold red]Invalid input, please try again.[/]")


class Board:
    def __init__(self):
        self.grid = [[EMPTY_SYMBOL for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.ships = {symbol: size for symbol, size in SHIP_SIZES.items()}
        self.ai_hits = []
        self.ship_hits = {symbol: 0 for symbol in SHIP_SIZES}

    def display(self, console, show_ships=True):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column(" ")
        for i in COLUMN_LABELS:
            table.add_column(f"[bold cyan]{i}[/]", justify="center")

        for i, row in enumerate(self.grid):
            cells = [f"[bold cyan]{i + 1}[/]"]
            for j, cell in enumerate(row):
                display_cell = EMPTY_SYMBOL if (cell in SHIP_SYMBOLS and not show_ships) else cell
                cell_style = "white on black"

                # Style for ship cells
                if display_cell in SHIP_SYMBOLS:
                    cell_style = "white on green"

                # Styles for hit and miss
                if display_cell == HIT_SYMBOL:
                    cell_style = "bold red on black"
                elif display_cell == MISS_SYMBOL:
                    cell_style = "bold blue on black"

                cells.append(f"[{cell_style}] {display_cell} [/]")

            table.add_row(*cells)
            if i < BOARD_SIZE - 1:
                table.add_row(*([" "] * (BOARD_SIZE + 1)))

        console.print(table)

    def is_valid_placement(self, size, row, col, horizontal):
        if horizontal:
            return col + size <= BOARD_SIZE and all(self.grid[row][col + i] == EMPTY_SYMBOL for i in range(size))
        else:
            return row + size <= BOARD_SIZE and all(self.grid[row + i][col] == EMPTY_SYMBOL for i in range(size))

    def place_ship(self, symbol, size, row, col, horizontal):
        for i in range(size):
            if horizontal:
                self.grid[row][col + i] = symbol
            else:
                self.grid[row + i][col] = symbol

    def receive_attack(self, row, col):
        if self.grid[row][col] in [HIT_SYMBOL, MISS_SYMBOL]:
            return None
        cell = self.grid[row][col]
        if cell in SHIP_SYMBOLS:
            self.grid[row][col] = HIT_SYMBOL
            self.ship_hits[cell] += 1  # Update hit count
            beep_sound(1000, 500)
            return True
        else:
            self.grid[row][col] = MISS_SYMBOL
            beep_sound(400, 500)
            return False

    def is_ship_sunk(self, ship_symbol):
        return self.ship_hits[ship_symbol] == SHIP_SIZES[ship_symbol]
    
    def check_if_sunk(self, hit_ship):
        return all(self.grid[row][col] == HIT_SYMBOL for row in range(BOARD_SIZE) for col in range(BOARD_SIZE) if self.grid[row][col] == hit_ship)

    def has_ships_remaining(self):
        return any(cell in SHIP_SYMBOLS for row in self.grid for cell in row)

    def is_adjacent(self, row, col):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.grid[r][c] in SHIP_SYMBOLS:
                return True
        return False

    def place_ship_with_validation(self, symbol, size, row, col, horizontal):
        if not self.is_valid_placement(size, row, col, horizontal):
            return False
        if horizontal:
            for i in range(size):
                if self.is_adjacent(row, col + i):
                    return False
        else:
            for i in range(size):
                if self.is_adjacent(row + i, col):
                    return False
        self.place_ship(symbol, size, row, col, horizontal)
        return True


def player_place_ships(board, console):
    console.print("Do you want to place your ships manually or automatically? (Type 'manual' or 'auto')")
    placement_choice = input().lower().strip()
    if placement_choice == 'auto':
        ai_place_ships(board)
        return

    # Display the empty board
    clear_screen()
    board.display(console)

    for symbol, size in SHIP_SIZES.items():
        while True:
            console.print(f"Placing {symbol} (Size: {size})")
            # Ask for a single coordinate input
            coordinate = safe_input("Enter starting coordinate (e.g., A3): ", str, lambda x: coordinate_to_position(x) is not None)
            direction = safe_input("Enter direction (h for horizontal, v for vertical): ", str, lambda x: x in ['h', 'v'])
            
            row, col = coordinate_to_position(coordinate)

            if board.place_ship_with_validation(symbol, size, row, col, direction == 'h'):
                clear_screen()
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


def player_turn(opponent_board, console):
    console.print("Your turn! Enter a coordinate (e.g., B4):")
    while True:
        coordinate = input().strip()
        position = coordinate_to_position(coordinate)
        if position is None:
            console.print("Invalid coordinate. Please try again.")
            continue
        row, col = position
        result = opponent_board.receive_attack(row, col)
        if result is None:
            console.print("You've already attacked this cell. Try again.")
        else:
            console.print("Hit!" if result else "Miss!")
            break


def get_ship_orientation(ai_hits):
    if len(ai_hits) >= 2:
        return 'horizontal' if ai_hits[0][0] == ai_hits[1][0] else 'vertical'
    return None

def get_target_cells(last_hit, orientation, board):
    row, col = last_hit
    target_cells = []
    if orientation == 'horizontal':
        directions = [(0, -1), (0, 1)]  # Left, Right
    else:
        directions = [(-1, 0), (1, 0)]  # Up, Down

    for dr, dc in directions:
        r, c = row + dr, col + dc
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board.grid[r][c] not in [HIT_SYMBOL, MISS_SYMBOL]:
            target_cells.append((r, c))
    return target_cells


def get_adjacent_cells(hit, board):
    row, col = hit
    adjacent_cells = []
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
    for dr, dc in directions:
        r, c = row + dr, col + dc
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
            adjacent_cells.append((r, c))
    return adjacent_cells


def ai_turn(player_board, console):
    console.print("AI is thinking...")
    time.sleep(1)

    # Remove hits related to sunk ships and reset targeting if necessary
    targeted_ships = {player_board.grid[hit[0]][hit[1]] for hit in player_board.ai_hits if player_board.grid[hit[0]][hit[1]] in SHIP_SYMBOLS}
    for ship in targeted_ships:
        if player_board.check_if_sunk(ship):
            player_board.ai_hits = [hit for hit in player_board.ai_hits if player_board.grid[hit[0]][hit[1]] != ship]
            console.print(f"AI has sunk your {ship}, moving to a new target.")
            # If all hits related to a ship are removed, break to ensure a new strategy
            if not player_board.ai_hits:
                break

    # If the AI has previous hits, it tries to follow up on them
    if player_board.ai_hits:
        # Determine ship orientation if we have enough hits
        orientation = get_ship_orientation(player_board.ai_hits)
        console.print(f"orientation: {orientation}" if orientation else "orientation not known")

        # If we know the orientation, focus on that axis
        if orientation:
            for hit in player_board.ai_hits:
                target_cells = get_target_cells(hit, orientation, player_board)
                for row, col in target_cells:
                    if player_board.grid[row][col] not in [HIT_SYMBOL, MISS_SYMBOL]:
                        console.print(f"AI is attacking {row+1}, {col+1}")
                        input("Press Enter to continue...")
                        result = player_board.receive_attack(row, col)
                        if result:
                            player_board.ai_hits.append((row, col))
                        return  # End the turn after one attack attempt

        # If orientation is not known, check adjacent cells
        else:
            last_hit = player_board.ai_hits[-1]
            adjacent_cells = get_adjacent_cells(last_hit, player_board)
            for row, col in adjacent_cells:
                if player_board.grid[row][col] not in [HIT_SYMBOL, MISS_SYMBOL]:
                    console.print(f"AI is attacking {row+1}, {col+1}")
                    input("Press Enter to continue...")
                    result = player_board.receive_attack(row, col)
                    if result:
                        player_board.ai_hits.append((row, col))
                    return  # End the turn after one attack attempt

    # Random guess if no hits to follow up on
    while True:
        row = random.randint(0, BOARD_SIZE - 1)
        col = random.randint(0, BOARD_SIZE - 1)
        if player_board.grid[row][col] not in [HIT_SYMBOL, MISS_SYMBOL]:
            console.print(f"AI is attacking {row+1}, {col+1} randomly")
            input("Press Enter to continue...")
            result = player_board.receive_attack(row, col)
            if result:
                player_board.ai_hits.append((row, col))
            return  # End the turn after one attack attempt


def setup_game():
    console = Console()
    player_board = Board()
    ai_board = Board()
    console.print("Welcome to Battleship!")
    player_place_ships(player_board, console)
    ai_place_ships(ai_board)
    return player_board, ai_board, console


def game_loop(player_board, ai_board, console):
    while player_board.has_ships_remaining() and ai_board.has_ships_remaining():
        clear_screen()
        console.print("Enemy Board:")
        ai_board.display(console, show_ships=False)
        console.print("Your Board:")
        player_board.display(console)

        player_turn(ai_board, console)
        clear_screen()
        console.print("Enemy Board:")
        ai_board.display(console, show_ships=False)
        console.print("Your Board:")
        player_board.display(console)
        if not ai_board.has_ships_remaining():
            console.print("You win!")
            break

        ai_turn(player_board, console)
        clear_screen()
        console.print("Enemy Board:")
        ai_board.display(console, show_ships=False)
        console.print("Your Board:")
        if not player_board.has_ships_remaining():
            console.print("AI wins!")
            break


def main():
    player_board, ai_board, console = setup_game()
    game_loop(player_board, ai_board, console)


if __name__ == "__main__":
    main()
