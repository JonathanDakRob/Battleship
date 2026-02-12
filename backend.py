# This file will handle the backend of our battleship game
# backend.py

import socket
import json
import threading

SERVER_IP = "127.0.0.1"
PORT = 5000
BOARD_SIZE = 10

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

# Local Game State

# 10x10 grid representation
# "." = empty
# "S" = ship
# "X" = hit
# "O" = miss
grid = [["." for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

# Ships stored as arrays of coordinate tuples
# For example: [[(0,0)], [(2,3),(2,4)], [(5,1),(6,1),(7,1)]]
ship_count = 0
ships = []

# Player ID
player_id = None

# Game state
GAME_STATE = "SELECT_SHIPS"

# Track shots received
shots_received = []

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

def can_place_ship(cells):
    for r, c in cells:
        if not in_bounds(r, c):
            return False
        if grid[r][c] == "S":
            return False
    return True

# Server Communication
# handle_server_message --> This function handles json messages passed to it by the servergit 
def handle_server_message(message):
    global player_id
    global GAME_STATE
    global ship_count

    if message["type"] == "player_id":
        player_id = message["player"]
        print(f"You are Player {player_id}")

    elif message["type"] == "bomb":
        row = message["row"]
        col = message["col"]
        receive_shot(row, col)

    elif message["type"] == "game_state":
        GAME_STATE = message["state"]

    elif message["type"] == "ship_count":
        ship_count = message["count"]

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

def update_game_state(new_state):
    global GAME_STATE
    GAME_STATE = new_state

    message = {
        "type": "game_state",
        "state": GAME_STATE,
        "player": player_id # Sender
    }

    sock.send(json.dumps(message).encode())

def update_ship_count(ship_count):
    
    message = {
        "type": "ship_count",
        "count": ship_count
    }

    sock.send(json.dumps(message).encode())

# Ship Placement
def place_ship(row, col, size, orientation):
    # Place a ship locally and store coordinates in ships array.
    cells = compute_ship_cells(row, col, size, orientation)

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
    payload = []

    for ship in ships:
        payload.append({
            "cells": [[r, c] for (r, c) in ship]
        })

    msg = {
        "type": "place_ships",
        "ships": payload
    }

    print("Submitting ship placement to server")
    sock.sendall(json.dumps(msg).encode())

# Bombing Logic

def send_bomb(row, col):
    msg = {
        "type": "bomb",
        "row": row,
        "col": col
    }
    print(f"Bomb sent to {row},{col}")
    sock.sendall(json.dumps(msg).encode())

# Shot Handling (Local)

def receive_shot(row, col):
    # Update local board when opponent fires at you.
    if (row, col) in shots_received:
        print("Repeat shot received.")
        return

    shots_received.append((row, col))

    if grid[row][col] == "S":
        grid[row][col] = "X"
        print("Your ship was hit!")
    else:
        grid[row][col] = "O"
        print("Opponent missed.")

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


