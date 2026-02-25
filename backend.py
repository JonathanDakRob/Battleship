# This file will handle the backend of our battleship game
# backend.py

import socket
import json
import threading
import time

SERVER_IP = "127.0.0.1"
PORT = 5000
BOARD_SIZE = 10

############################################################################# Server Communication #############################################################################
# Connection to server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
while True:
    try:
        sock.connect((SERVER_IP, PORT))
        break
    except ConnectionRefusedError:
        print("Waiting for server...")
        time.sleep(1)

print("Connected to server")

_recv_buffer = bytearray()

# Networking Helpers
def _send(msg):
    sock.sendall((json.dumps(msg)+ "\n").encode())

############################################################################# Memory #############################################################################
# Local Game State

# 10x10 grid representation
# "." = empty
# "S" = ship
# "X" = hit
# "O" = miss
grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
target_grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

ship_count = 0
# Ships stored as arrays of coordinate tuples
# For example: [[(0,0)], [(2,3),(2,4)], [(5,1),(6,1),(7,1)]]
ships = []

# Identity and match state
player_id = None
your_turn = False
game_over = False
ships_locked = False
all_ships_locked = False

# Game state
# SELECT_SHIPS -> PLACE_SHIPS -> WAITING_FOR_OPPONENT -> RUNNING_GAME
GAME_STATE = "SELECT_SHIPS"

# Track shot outcomes (for UI & debugging)
shots_received_hit = []
shots_received_miss = []
shots_sent_hit = []
shots_sent_miss = []

# Prevent firing multiple shots before the server replies with hit_status
# pending_shot = False # Commented out for simplicity. Keeping things simple and clean for now

############################################################################# Pre-game Functions #############################################################################
# Utility Functions
def in_bounds(row, col):
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

def compute_ship_cells(row, col, size, orientation):
    cells = []
    for i in range(size):
        if orientation == "H":
            r, c = row, col + i
        else:
            r, c = row + i, col
        cells.append((r, c))
    return cells

def is_straight_and_contiguous(cells, size):
    if size <= 1:
        return True

    rows = [r for (r, _) in cells]
    cols = [c for (_, c) in cells]

    same_row = all(r == rows[0] for r in rows)
    same_col = all(c == cols[0] for c in cols)

    if not (same_row or same_col):
        return False

    if same_row:
        sorted_cols = sorted(cols)
        return sorted_cols == list(range(sorted_cols[0], sorted_cols[0] + size))

    sorted_rows = sorted(rows)
    return sorted_rows == list(range(sorted_rows[0], sorted_rows[0] + size))

def can_place_ship(cells):
    for r, c in cells:
        if not in_bounds(r, c):
            return False
        if grid[r][c] == "S":
            return False
    return True

def remove_ship_from_grid(cells):
    # Clears old ship footprint when a ship is moved
    global grid
    for r, c in cells:
        if in_bounds(r, c) and grid[r][c] == "S":
            grid[r][c] = "."

def update_game_state(new_state):
    global GAME_STATE
    GAME_STATE = new_state

    # This keeps both clients stage-synced during development.
    message = {
        "type": "game_state",
        "state": GAME_STATE,
        "sender": player_id # Sender
    }
    _send(message)

def update_ship_count(count):
    # Player 1 selects ship count; server forwards to both clients.
    if not (1 <= count <= 5):
        print("ship count must be 1-5")
        return False
    
    message = {
        "type": "ship_count",
        "count": count
    }
    _send(message)
    return True

def set_ship_count(count):
    global ship_count
    ship_count = count

############################################################################# Ship Placement #############################################################################
def place_ship(row, col, size, orientation):
    # Place a ship locally and store coordinates in ships array.
    orientation = (orientation or "").strip().upper()

    if size > 1 and orientation not in ("H", "V"):
        print("Invalid orientation. Use 'H' or 'V'.")
        return False

    if size <= 1:
        orientation = "H"

    cells = compute_ship_cells(row, col, size, orientation)

    if not is_straight_and_contiguous(cells, size):
        print("Invalid ship placement (must be straight and contiguous).")
        return False

    if not can_place_ship(cells):
        print("Invalid ship placement.")
        return False

    for r, c in cells:
        grid[r][c] = "S" # Marks ship presence on the board

    ships.append(cells) # Saves ship cells for later hit/sunk logic
    print(f"Ship of size {size} placed at {cells}")
    return True

def submit_placement():
    global ships_locked

    # Send ship coordinate arrays to server so opponent can start after both lock.
    payload = [{"cells": [[r, c] for (r, c) in ship]} for ship in ships]

    msg = {
        "type": "place_ships",
        "ships": payload
    }
    
    ships_locked = True
    print("Submitting ship placement to server")
    _send(msg)

############################################################################# In-game Functions #############################################################################
# Bombing Logic
def can_send_bomb(row, col):
    # Prevents repeats and out-of-bounds shots on opponent grid.
    if not in_bounds(row, col):
        return False
    if (row, col) in shots_sent_hit:
        return False
    if (row, col) in shots_sent_miss:
        return False
    return True

def send_bomb(row, col):
    global your_turn, GAME_STATE, game_over

    # This is the main gate: only shoot during RUNNING_GAME.
    if GAME_STATE != "RUNNING_GAME":
        print("BOMB FAILED: Not in RUNNING_GAME.")
        return

    # Game over blocks interaction.
    if game_over:
        print("BOMB FAILED: Game is over.")
        return

    # Turn-based gating prevents both players shooting at once.
    if not your_turn:
        print("BOMB FAILED: Not your turn.")
        return

    # Prevent double-click spam until hit_status arrives.
    # if pending_shot:
    #     print("BOMB FAILED: Waiting for shot result.")
    #     return

    if not can_send_bomb(row, col):
        print("BOMB FAILED: Invalid bomb (repeat or out of bounds).")
        return

    # pending_shot = True # Lock out extra shots until result message comes back
    # your_turn = False # End turn locally; server/game rules can refine later

    msg = {
        "type": "bomb",
        "row": row,
        "col": col
    }

    _send(msg)
    print(f"BOMB SENT: {row},{col}")

def get_ship_index(row, col):
    # Returns the ship index containing (row, col), or -1 if no ship occupies it.
    target = (row,col)
    for i, ship in enumerate(ships):
        if target in ship:
            return i
    return -1

def check_ship_sunk(ship_index):
    # True if every cell in this ship has been hit ("X").
    if ship_index < 0 or ship_index >= len(ships):
        return False
    ship = ships[ship_index]
    for r, c in ship:
        if grid[r][c] != "X":
            return False
    return True

def all_ships_sunk():
    # True if all ships are sunk; used for loss condition.
    for i in range(len(ships)):
        if not check_ship_sunk(i):
            return False
    return True

# Shot Handling (Local)
def receive_shot(row, col):
    # Applies opponent shot to our grid and sends hit_status back for their UI.
    global shots_received_hit, shots_received_miss, grid

    if (row, col) in shots_received_hit or (row, col) in shots_received_miss:
        print("Repeat shot received.")
        return

    hit = (grid[row][col] == "S")

    if hit:
        grid[row][col] = "X" # Mark damage on our ship
        shots_received_hit.append((row,col))
        print("Your ship was hit!")
    else:
        grid[row][col] = "O" # Mark opponent miss on the board
        shots_received_miss.append((row,col))
        print("Opponent missed.")
    
    ship_index = get_ship_index(row,col)
    sunk = check_ship_sunk(ship_index) # True if this hit finished the ship
    all_sunk = all_ships_sunk() # True if we have no ships left

    msg = {
        "type": "hit_status",
        "row": row,
        "col": col,
        "status": hit, # Shooter expects boolean hit/miss
        "sunk": sunk,
        "all_sunk": all_sunk
    }
    _send(msg)

# Helper: hit counts per ship
def ship_hit_counts():
    # Returns list like [hits_on_ship1, hits_on_ship2, ...]
    counts = []
    for ship in ships:
        hits = 0
        for r, c in ship:
            if grid[r][c] == "X":
                hits += 1
        counts.append(hits)
    return counts

def reset_game():
    global grid, target_grid, ships
    global shots_received_hit, shots_received_miss, shots_sent_hit, shots_sent_miss
    global ship_count, your_turn, game_over, GAME_STATE
    global ships_locked, all_ships_locked

    grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    target_grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    ships = []
    shots_received_hit = []
    shots_received_miss = []
    shots_sent_hit = []
    shots_sent_miss = []

    ship_count = 0
    your_turn = False
    # pending_shot = False
    game_over = False
    GAME_STATE = "SELECT_SHIPS"
    ships_locked = False
    all_ships_locked = False

    print("Game has been reset.")
    return True

############################################################################# Message Handling #############################################################################

# handle_server_message --> This function handles JSON messages passed to it by the servergit
def handle_server_message(message):
    global player_id, GAME_STATE, ship_count, ships_locked, all_ships_locked, your_turn

    mtype = message["type"]

    if mtype == "player_id":
        player_id = message["player"]
        print(f"You are Player {player_id}")

    elif mtype == "set_ship_count":
        set_ship_count(message["count"])

    elif mtype == "all_ships_locked":
        all_ships_locked = True

    elif mtype == "bomb":
        # When opponent fires a bomb at us, we respond with a hit_status message
        row = message["row"]
        col = message["col"]
        receive_shot(row, col)

    elif mtype == "hit_status":
        # This message is received after sending a bomb
        # "status": True/False if the bomb was a hit/miss
        coord = (message["row"], message["col"])
        if message["status"] == True:
            shots_sent_hit.append(coord)
        elif message["status"] == False:
            shots_sent_miss.append(coord)

    elif mtype == "change_turn":
        if your_turn:
            print("BACKEND: Opponent's Turn Now")
            your_turn = False
        else:
            print("BACKEND: Your Turn Now")
            your_turn = True

    elif mtype == "game_over":
        game_over == True
        print("BACKEND: GAME OVER!")

    else:
        print(f"Unknown Message: {message}")

def listen_to_server():
    while True:
        try:
            data = sock.recv(4096).decode()
            if data:
                message = json.loads(data)
                handle_server_message(message)
        except:
            break

print("BACKEND: Listening To Server...")
threading.Thread(target=listen_to_server, daemon=True).start() # Thread that constantly listens for messages