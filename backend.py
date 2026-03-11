# This file will handle the backend of our battleship game
# backend.py

import socket
import json
import threading
import time

SERVER_IP = "127.0.0.1"
PORT = 5000
BOARD_SIZE = 10

############################################################################# Memory #############################################################################
# Local Game State

# 10x10 grid representation
# "." = empty
# "S" = ship
# "X" = hit
# "O" = miss
# "D" = sunk
grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
target_grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

ship_count = 0
# Ships stored as arrays of coordinate tuples
# For example: [[(0,0)], [(2,3),(2,4)], [(5,1),(6,1),(7,1)]]
ships = []

# Identity and match state
player_id = None
your_turn = False
winner = False
ships_locked = False
all_ships_locked = False
opponent_ships_sunk = 0

# Game mode: Single or Multi-player
# Single Player: 1
# Multi-Playter: 2
GAME_MODE = 0

# Game state
# WAITING_FOR_PLAYERS_TO_CONNECT -> SELECT_SHIPS -> PLACE_SHIPS -> WAITING_FOR_OPPONENT -> RUNNING_GAME
GAME_STATE = "MAIN_MENU"

# Track shot outcomes (for UI & debugging)
shots_received_hit = []
shots_received_miss = []
shots_sent_hit = []
shots_sent_miss = []


####################################################################### AI Components #######################################################################################

# Coming Soon: AI Components

class ai_opponent:
    def __init__(self):
        self.ai_ships = None
        self.difficulty = None
        self.ai_turn = False

    # Places 'ship_count' number of ships
    def ai_generate_ships(self, ship_count):
        pass

    # When it is the AI's turn, it will generate a shot
    def ai_generate_shot(self):
        if self.difficulty == "easy":
            pass
        elif self.difficulty == "medium":
            pass
        elif self.difficulty == "hard":
            global ships
            pass
    
    # Handling the reception of a shot from player
    def ai_receive_shot(self):
        return

############################################################################# Server Communication #############################################################################
sock = None

# Networking Helpers
def _send(msg):
    if GAME_MODE == 2:
        sock.sendall((json.dumps(msg)+ "\n").encode())
        # print(f"{msg["type"]} message sent")
    else:
        print("Cannot send message to server. Game in Single Player Mode")

############################################################################# Variable Updates #############################################################################
def update_game_mode(mode):
    global GAME_MODE
    if mode in range(1,3):
        GAME_MODE = mode
    else:
        print("INVALID GAME MODE")

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

def compute_multi_bomb_cells(center_row, center_col):
    # Build the 3x3 area centered on the clicked grid cell.
    # Any cells that would go out of bounds are ignored.
    cells = []

    for r in range(center_row - 1, center_row + 2):
        for c in range(center_col - 1, center_col + 2):
            if in_bounds(r, c):
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

def can_send_multi_bomb(cells):
    # Allow the attack if at least one square in the 3x3 area
    # has not already been targeted before.
    for row, col in cells:
        if (row, col) not in shots_sent_hit and (row, col) not in shots_sent_miss:
            return True
        return False

def send_bomb(row, col):
    global your_turn, GAME_STATE

    # This is the main gate: only shoot during RUNNING_GAME.
    if GAME_STATE != "RUNNING_GAME":
        print("BOMB FAILED: Not in RUNNING_GAME.")
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

def send_multi_bomb(row, col):
    global your_turn, GAME_STATE

    # Only allow multi-bomb during the real gameplay phase.
    if GAME_STATE != "RUNNING_GAME":
        print("MULTI-BOMB FAILED: Not in RUNNING_GAME.")
        return

    # Only the current player can fire.
    if not your_turn:
        print("MULTI-BOMB FAILED: Not your turn.")
        return

    # Convert one clicked square into a valid 3x3 attack area.
    cells = compute_multi_bomb_cells(row, col)

    # Block the attack if the whole area was already used before.
    if not can_send_multi_bomb(cells):
        print("MULTI-BOMB FAILED: Entire 3x3 area was already targeted.")
        return

    # Send both the center point and the full list of target cells.
    # The server forwards this to the defender.
    msg = {
        "type": "multi_bomb",
        "center_row": row,
        "center_col": col,
        "cells": [[r, c] for (r, c) in cells]
    }

    _send(msg)
    print(f"MULTI-BOMB SENT: center=({row}, {col}) cells={cells}")

def get_ship_index(row, col):
    # Returns the ship index containing (row, col), or -1 if no ship occupies it.
    target = (row, col)
    print(f"BACKEND: get_ship_index - {target}")
    for i in range(0,len(ships)):
        print(f"BACKEND: Checking index {i}, ship {ships[i]} for {target}")
        if target in ships[i]:
            print("FOUND!")
            return i
        else:
            print("NOT FOUND.")
    return -1

def get_ship_coords(ship_index):
    global ships

    ship = ships[ship_index]
    return ship

def check_ship_sunk(ship_index):
    # True if every cell in this ship has been hit ("X").
    print(f"BACKEND: Checking ship {ship_index} index")
    if ship_index < 0 or ship_index >= len(ships):
        return False
    ship = ships[ship_index]
    for r, c in ship:
        print(f"Ship {r}, {c} = {grid[r][c]}")
        if grid[r][c] != "X":
            return False
    return True

def all_ships_sunk():
    # True if all ships are sunk; used for loss condition.
    global ships
    for ship in ships:
        for r, c in ship:
            if not grid[r][c] == "D":
                return False
    return True

def sink_opp_ship(ship_coords):
    global target_grid, opponent_ships_sunk

    for r, c in ship_coords:
        target_grid[r][c] = "D"
        print(f"Grid ({r},{c}) = {target_grid[r][c]}")

    opponent_ships_sunk += 1

def sink_own_ship(ship_index):
    global ships, grid
    ship = ships[ship_index]

    for r, c in ship:
        grid[r][c] = "D"
        print(f"Grid ({r},{c}) = {grid[r][c]}")

def get_num_ships_sunk():
    global ships

    num_sunk = len(ships)
    for ship in ships:
        for r, c in ship:
            if grid[r][c] != "D":
                num_sunk = num_sunk - 1
                break
    
    return num_sunk

# Shot Handling (Local)
def receive_shot(row, col):
    # Applies opponent shot to our grid and sends hit_status back for their UI.
    global shots_received_hit, shots_received_miss, grid

    if (row, col) in shots_received_hit or (row, col) in shots_received_miss:
        print("Repeat shot received.")
        return

    hit = (grid[row][col] == "S")
    print(f"Hit: {hit}")
    ship_index = get_ship_index(row, col)
    print(f"Ship Index: {ship_index}")
    sunk = False
    all_sunk = False
    ship_coords = None

    if hit:
        grid[row][col] = "X" # Mark damage on our ship
        shots_received_hit.append((row,col))
        print("Your ship was hit!")
        sunk = check_ship_sunk(ship_index) # True if this hit finished the ship
        print(f"Sunk: {sunk}")
        
        if sunk:
            sink_own_ship(ship_index)
            print(f"Ship sunk {row}, {col}")
            ship_coords = get_ship_coords(ship_index)
            all_sunk = all_ships_sunk() # True if we have no ships left
            print("Your ship was sunk!")
            
    else:
        grid[row][col] = "O" # Mark opponent miss on the board
        shots_received_miss.append((row,col))
        print("Opponent missed.")
    
    print(f"BACKEND: Receiving shot ({row},{col}) - Hit: {hit}, Index: {ship_index}, Sunk: {sunk}, All Sunk: {all_sunk}")

    msg = {
        "type": "hit_status",
        "row": row,
        "col": col,
        "status": hit, # Shooter expects boolean hit/miss
        "sunk": sunk,
        "ship_coords": ship_coords,
        "all_sunk": all_sunk
    }
    _send(msg)

def receive_multi_bomb(cells):
    # This function is called on the defending player's side.
    # It applies the full 3x3 attack to the local board and
    # sends one combined result message back to the attacker.
    global shots_received_hit, shots_received_miss, grid

    results = []
    sunk_ships = []
    sunk_indexes = []

    for row, col in cells:
        # If a square was already attacked before, record it as a repeat
        # so the attacker still gets a full response for all 3x3 cells.
        if (row, col) in shots_received_hit or (row, col) in shots_received_miss:
            results.append({
                "row": row,
                "col": col,
                "status": "repeat"
            })
            continue

        hit = (grid[row][col] == "S")
        ship_index = get_ship_index(row, col)

        if hit:
            # Mark this board square as damaged.
            grid[row][col] = "X"
            shots_received_hit.append((row,col))

            # Check whether this hit completed an entire ship.
            sunk = check_ship_sunk(ship_index)

            if sunk:
                # Convert that whole ship from X to D to show it is sunk.
                sink_own_ship(ship_index)

                # Avoid adding the same sunk ship multiple times
                # if several cells from that ship were hit in the 3x3 area.
                if ship_index not in sunk_indexes:
                    sunk_indexes.append(ship_index)
                    sunk_ships.append(get_ship_coords(ship_index))

            results.append({
                "row": row,
                "col": col,
                "status": "hit"
            })

        else:
            # Mark misses on the defending board.
            grid[row][col] = "O"
            shots_received_miss.append((row,col))
            results.append({
                "row": row,
                "col": col,
                "status": "miss"
            })

    # After all 3x3 cells are processed, check if the defender has lost.
    all_sunk = all_ships_sunk()

    # Send one combined result back to the attacker.
    msg = {
        "type": "multi_bomb_result",
        "results": results,
        "sunk_ships": sunk_ships,
        "all_sunk": all_sunk
    }
    _send(msg)

def handle_hit_status(status, row, col, sunk, ship_coords, all_sunk):
    coord = (row,col)

    if status:
        shots_sent_hit.append(coord)
        if sunk:
            sink_opp_ship(ship_coords)
            print("You sunk a battleship!")
        else:
            target_grid[row][col] = "X"
            print("Your shot hit!")
    else:
        shots_sent_miss.append(coord)
        target_grid[row][col] = "O"
    
    if all_sunk:
        global player_id
        game_over_msg = {
            "type": "game_over",
            "winner": player_id
        }
        _send(game_over_msg)

def handle_multi_bomb_result(results, sunk_ships, all_sunk):
    # This function runs on the attacking player's side.
    # It updates the attacker's target grid using the combined 3x3 result.
    for result in results:
        row = result["row"]
        col = result["col"]
        status = result["status"]

        if status == "hit":
            # Record this square as a successful hit on the opponent board.
            if (row, col) not in shots_sent_hit:
                shots_sent_hit.append((row,col))
            target_grid[row][col] = "X"

        elif status == "miss":
            # Record this square as a miss on the opponent board.
            if (row, col) not in shots_sent_miss:
                shots_sent_miss.append((row,col))
            target_grid[row][col] = "O"

    # If any full ships were sunk by the 3x3 attack,
    # mark all of those ship coordinates as D on the target grid.
    for ship_coords in sunk_ships:
        sink_opp_ship(ship_coords)

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

def handle_game_over(winner_id):
    global winner, player_id, GAME_STATE
    GAME_STATE = "GAME_OVER"
    if winner_id == player_id:
        winner = True
        print("GAME OVER! YOU WIN!")
    else:
        winner = False
        print("GAME OVER! YOU LOSE.")

def reset_game():
    global grid, target_grid, ships, player_id, winner, opponent_ships_sunk, sock
    global shots_received_hit, shots_received_miss, shots_sent_hit, shots_sent_miss
    global ship_count, your_turn, GAME_STATE, GAME_MODE
    global ships_locked, all_ships_locked

    grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    target_grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    ships = []
    shots_received_hit = []
    shots_received_miss = []
    shots_sent_hit = []
    shots_sent_miss = []
    player_id = None
    winner = False
    opponent_ships_sunk = 0

    ship_count = 0
    your_turn = False

    GAME_MODE = 0
    GAME_STATE = "MAIN_MENU"
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
    
    elif mtype == "start_game":
        GAME_STATE = "SELECT_SHIPS"

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
        status = message["status"]
        row = message["row"]
        col = message["col"]
        sunk = message["sunk"]
        ship_coords = message["ship_coords"]
        all_sunk = message["all_sunk"]

        handle_hit_status(status,row,col,sunk,ship_coords,all_sunk)

    elif mtype == "multi_bomb":
        # Defender receives the full 3x3 target area from the attacker.
        cells = []
        for pair in message["cells"]:
            cells.append((pair[0], pair[1]))
        receive_multi_bomb(cells)

    elif mtype == "multi_bomb_result":
        # Attacker receives the final combined outcome of the 3x3 attack.
        results = message["results"]
        sunk_ships = message["sunk_ships"]
        all_sunk = message["all_sunk"]

        handle_multi_bomb_result(results,sunk_ships,all_sunk)

        # If the defender has no ships left after the multi-bomb,
        # notify the server that this player won.
        if all_sunk:
            game_over_msg = {
                "type": "game_over",
                "winner": player_id,
            }
            _send(game_over_msg)

    elif mtype == "change_turn":
        if your_turn:
            print("BACKEND: Opponent's Turn Now")
            your_turn = False
        else:
            print("BACKEND: Your Turn Now")
            your_turn = True

    elif mtype == "game_over":
        winner_id = message["winner"]
        handle_game_over(winner_id)

    else:
        print(f"Unknown Message: {message}")

def listen_to_server():
    buffer = ""
    message = ""
    while True:
        try:
            data = sock.recv(4096).decode()
            buffer += data
            if data:
                message = json.loads(data)
                
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    message = json.loads(line)
                    handle_server_message(message)
        except:
            break


"""
The following functions work as follows:
    board.py runs init_network():
        Try to connect to server
            if the server is not started yet
                start the server
            else
                connect to the server

This allows board.py to be be the only file needing to be run
The first client that runs it hosts the server and is player 1
"""
def start_local_server():
    global server_host
    if server_host:
        return
    try:
        import server
        threading.Thread(target=server.main, daemon=True).start()
        server_host = True
    except OSError:
        print("BACKEND: Another server instance started")
        pass  # another instance started it first

server_started = False
server_host = False # True if this instance is hosting the server
def connect_to_server():
    global sock, server_started
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            sock.connect((SERVER_IP, PORT))
            print("Connected to server.")
            return sock

        except ConnectionRefusedError:
            if not server_started:
                print("Server not running. Starting local server...")
                start_local_server()
                time.sleep(1) # Giving server time to bind
                server_started = True
            else:
                print("Waiting for server...")
                time.sleep(1)

def init_network():
    global sock
    sock = connect_to_server()
    threading.Thread(target=listen_to_server, daemon=True).start()
    print("Connected to server")

def disconnect_from_server():
    global sock, server_started, server_host
    if sock:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        sock.close()
        sock = None

    if server_host:
        import server
        server.running = False
        server_host = False