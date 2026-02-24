# This file will handle the backend of our battleship game
# backend.py

import socket
import json
import threading

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
        import time
        time.sleep(1)

print("Connected to server")

# Networking Helpers
def _send(msg):
    #sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
    sock.send(json.dumps(msg).encode())

# def _recv_lines():
#     try:
#         chunk = sock.recv(4096)
#     except OSError:
#         return []
#     if not chunk:
#         return []

#     _recv_buffer.extend(chunk)

#     lines = []

#     while True:
#         idx = _recv_buffer.find(b"\n")
#         if idx == -1:
#             break
#         line = _recv_buffer[:idx].decode("utf-8", errors="replace")
#         del _recv_buffer[:idx + 1]
#         lines.append(line)
#     return lines


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
stage = "WAIT_FOR_CONFIG" # server-authoritative
your_turn = False
battle_started = False
game_over = False
# last_message = ""
ships_locked = False
all_ships_locked = False

# Game state
GAME_STATE = "SELECT_SHIPS"

# Track shots received and sent
shots_received_hit = []
shots_received_miss = []
shots_sent_hit = []
shots_sent_miss = []

_recv_buffer = bytearray()

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
    global grid
    for r, c in cells:
        if in_bounds(r, c) and grid[r][c] == "S":
            grid[r][c] = "."

def update_game_state(new_state):
    global GAME_STATE
    GAME_STATE = new_state

    message = {
        "type": "game_state",
        "state": GAME_STATE,
        "sender": player_id # Sender
    }

    _send(message)
    # sock.send(json.dumps(message).encode())

def update_ship_count(ship_count):
    if not (1 <= ship_count <= 5):
        print("ship count must be 1-5")
        return False
    
    message = {
        "type": "ship_count",
        "count": ship_count
    }
    _send(message)
    return True

# Config / Ship Count (Player 0 chooses)
def set_ship_count(count):
    global ship_count
    ship_count = count

# def send_config(n):
#     msg = {
#         "type": "config",
#         "ship_count": n
#     }
#     print(f"Sending ship_count={n} to server")
#     _send(msg)

# Ship Placement
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

    # Mark ship on grid
    for r, c in cells:
        grid[r][c] = "S"

    # Save ship coordinates
    ships.append(cells)

    print(f"Ship of size {size} placed at {cells}")
    return True

def submit_placement():
    # Send ship coordinate arrays to server
    global ships_locked
    payload = []

    for ship in ships:
        payload.append({
            "cells": [[r, c] for (r, c) in ship]
        })

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
    if not in_bounds(row, col):
        return False
    if (row, col) in shots_sent_hit:
        return False
    if (row, col) in shots_sent_miss:
        return False
    return True

def send_bomb(row, col):
    if stage != "BATTLE":
        print("BOMB FAILED: Not in battle stage.")
        return

    if game_over:
        print("BOMB FAILED: Game is over.")
        return

    if not your_turn:
        print("BOMB FAILED: Not your turn.")
        return

    if not can_send_bomb(row, col):
        print("BOMB FAILED: Invalid bomb (repeat or out of bounds).")
        return

    msg = {
        "type": "bomb",
        "row": row,
        "col": col
    }

    _send(msg)
    print(f"BOMB SENT: {row},{col}")
    

# Shot Handling (Local)
def receive_shot(row, col):
    # Update local board when opponent fires at you.
    if (row, col) in shots_received_hit:
        print("Repeat shot received.")
        return
    if (row, col) in shots_received_miss:
        print("Repeat shot received.")
        return

    status = ""

    if grid[row][col] == "S":
        grid[row][col] = "X"
        status = "hit"
        shots_received_hit.append((row,col))
        print("Your ship was hit!")
    else:
        grid[row][col] = "O"
        status = "miss"
        shots_received_miss.apend((row,col))
        print("Opponent missed.")
    
    ship_index = get_ship_index(row,col)
    sunk = check_ship_sunk(ship_index)
    all_sunk = all_ships_sunk()

    msg = {
        "type": "hit_status",
        "row": row,
        "col": col,
        "status": status,
        "sunk": sunk,
        "all_sunk": all_sunk
    }

    _send(msg)

def get_ship_index(row, col):
    # This function returns the ship index of a ship when passed one of its coordinates
    # Returns -1 if no ship has that coordinate
    target = (row,col)
    index = next(
        (i for i, ship in enumerate(ships) if target in ship),
        None
    )
    if target is None:
        return -1
    return index

def check_ship_sunk(ship_index):
    # Check if a specific ship is sunk.
    ship = ships[ship_index]
    for r, c in ship:
        if grid[r][c] != "X":
            return False
    return True

def all_ships_sunk():
    # Return True if every ship is sunk.
    for i in range(len(ships)):
        if not check_ship_sunk(i):
            return False
    return True

# Helper: hit counts per ship
def ship_hit_counts():
    counts = []
    for ship in ships:
        hits = 0
        for r, c in ship:
            if grid[r][c] == "X":
                hits += 1
        counts.append(hits)
    return counts

def reset_game():
    global grid, target_grid, ships, shots_received_hit, shot_received_miss, shots_sent_hit, shots_sent_miss
    global ship_count, your_turn, battle_started, game_over, last_message, stage

    grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    target_grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    ships = []
    shots_received_hit = []
    shot_received_miss = []
    shots_sent_hit = []
    shots_sent_miss = []

    ship_count = 0
    your_turn = False
    battle_started = False
    game_over = False
    stage = "WAIT_FOR_CONFIG"

    print("Game has been reset.")
    return True


############################################################################# Message Handling #############################################################################

# handle_server_message --> This function handles json messages passed to it by the servergit 
def handle_server_message(message):
    global player_id, GAME_STATE, ship_count, ships_locked, all_ships_locked

    if message["type"] == "player_id":
        player_id = message["player"]
        print(f"You are Player {player_id}")

    elif message["type"] == "set_ship_count":
        set_ship_count(message["count"])
    
    elif message["type"] == "all_ships_locked":
        all_ships_locked = True

    elif message["type"] == "bomb":
        row = message["row"]
        col = message["col"]
        receive_shot(row, col)

    elif message["type"] == "hit_status":
        # This message is received after sending a bomb
        # "status": True/False if the bomb was a hit/miss
        coord = (message["row"], message["col"])
        if message["status"] == True:
            shots_sent_hit.append(coord)
        elif message["status"] == False:
            shots_sent_miss.append(coord)
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

threading.Thread(target=listen_to_server, daemon=True).start() # Thread that constantly listens for messages


# Server Message Handling V2? Potential whole addition to server message handling; needs testing.
"""
def handle_server_message(message):
    global player_id, ship_count, stage, your_turn, battle_started, game_over, last_message

    mtype = message.get("type")

    if mtype == "player_id":
        player_id = message.get("player")
        last_message = f"You are Player {player_id}"
        print(last_message)

    elif mtype == "stage":
        stage = message.get("stage", stage)
        battle_started = (stage == "BATTLE")
        game_over = (stage == "GAME_OVER")
        your_turn = False
        last_message = f"Stage: {stage}"
        print(last_message)

    elif mtype == "status":
        # Meant for UI side panel; for 'stage' messaging for transitions
        pass

    elif mtype == "config":
        ship_count = int(message.get("ship_count", 0))
        last_message = f"Ship count set to {ship_count} (sizes 1..{ship_count})"
        print(last_message)

    elif mtype == "config_ok":
        last_message = f"Server accepted ship_count={message.get('ship_count')}"
        print(last_message)

    elif mtype == "placement_ok":
        last_message = "Server accepted ship placement. Waiting for opponent..."
        print(last_message)

    elif mtype == "start_battle":
        # Meant for compatibility purposes
        stage = "BATTLE"
        battle_started = True
        your_turn = False
        last_message = "Battle started!"
        print(last_message)
        
    elif mtype == "your_turn":
        your_turn = True
        last_message = "Your turn."
        print(last_message)
        
    elif mtype == "bomb_result":
        r = int(message.get("row", -1))
        c = int(message.get("col", -1))
        hit = bool(message.get("hit"))
        sunk = bool(message.get("sunk"))
        
        target_grid[r][c] = "X" if hit else "O"
        your_turn = False
        
        if message.get("game_over"):
            winner = message.get("winner")
            last_message = "You win!" if winner == player_id else "You lost."
        else:
            if hit and sunk:
                last_message = "Hit and sunk a ship!"
            elif hit:
                last_message = "Hit!"
            else:
                last_message = "Miss."
        
        print(last_message)
        
    elif mtype == "incoming_shot":
        r = int(message.get("row", -1))
        c = int(message.get("col", -1))
        hit = bool(message.get("hit"))
        
        receive_shot(r, c)
        
        if message.get("game_over"):
            winner = message.get("winner")
            last_message = "You win!" if winner == player_id else "You lost."
        else:
            last_message = "Opponent hit you!" if hit else "Opponent missed."
        
        print(last_message)
        
    elif mtype == "game_over":
        winner = message.get("winner")
        last_message = "You win!" if winner == player_id else "You lost."
        print(last_message)
        
    elif mtype == "error":
        last_message = "Server error: " + str(message.get("message", ""))
        print(last_message)
    
    elif mtype == "info":
        last_message = str(message.get("message", ""))
        print(last_message)
"""