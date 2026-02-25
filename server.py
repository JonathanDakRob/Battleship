#This file handles the server for Battleship
#server.py

import socket
import json
import threading
import time

HOST = "0.0.0.0"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows for quick restarting
server.bind((HOST, PORT))
server.listen(2)

print("Server waiting for players...")

clients = []

"""
# JSON logic
clients = [None, None] # clients[0] = Player 1, clients[1] = Player 2
recv_buffers = [bytearray(), bytearray()] # Per-client buffers for newline JSON

# Game related memory
player1_locked = False
player2_locked = False

GAME_OVER = False
game_over_sent = False # Prevents spamming game_over every loop

def send_json(conn, msg):
    # Newline-delimited JSON prevents broken parsing when TCP splits/combines packets
    conn.sendall((json.dumps(msg) + "\n").encode("utf-8"))
    
def recv_json_lines(player_index):
    # Reads raw bytes and returns a list of complete JSON lines
    conn = clients[player_index]
    try:
        chunk = conn.recv(4096)
    except OSError:
        return []
    
    if not chunk:
        return []
    
    recv_buffers[player_index].extend(chunk)
    
    lines = []
    while True:
        idx = recv_buffers[player_index].find(b"\n")
        if idx == -1:
            break
        line = recv_buffers[player_index][:idx].decode("utf-8", errors="replace")
        del recv_buffers[player_index][:idx + 1]
        lines.append(line)
    
    return lines
"""
# Accept two players
for i in range(2):
    player_id = i+1
    conn, addr = server.accept()
    print(f"Player {player_id} connected from {addr}")
    clients.append(conn)

    # Send player ID to client
    conn.send(json.dumps({
        "type": "player_id",
        "player": player_id
    }).encode())

print("Both players connected. Game starting.")

# Game related memory
ships = []
player1_locked = False
player2_locked = False
p1_game_state = None
p2_game_state = None

player_turn = 1

GAME_OVER = False

def handle_client(player_index):
    global GAME_OVER, p1_game_state, p2_game_state, ships, player1_locked, player2_locked

    conn = clients[player_index]
    opponent = clients[1 - player_index]

    while True:
        try:
            if GAME_OVER:
                game_over_msg = {
                    "type": "game_over",
                    "status": True
                }
                conn.send(json.dumps(game_over_msg).encode())
                opponent.send(json.dumps(game_over_msg).encode())

            data = conn.recv(4096).decode()
            if not data:
                print("SERVER ERROR: MESSAGE ERROR 1")
                break

            message = json.loads(data)
            print(f"Received from Player {player_index}: {message}")

            if message["type"] == "game_state":
                state = message["state"]
                sender = message["sender"]
                if sender == 1:
                    p1_game_state = state
                else:
                    p2_game_state = message["state"]
                print(f"SERVER: Player {sender} reached state: {state}")

            elif message["type"] == "ship_count":
                new_message = {
                    "type": "set_ship_count",
                    "count": message["count"]
                }
                conn.send(json.dumps(new_message).encode())
                opponent.send(json.dumps(new_message).encode())

            elif message["type"] == "place_ships":
                print("Server: Ships Placed and Locked")
                ships = message["ships"]
                if player_index == 0:
                    player1_locked = True
                else:
                    player2_locked = True
                
                if player1_locked and player2_locked:
                    all_locked_msg = {
                        "type": "all_ships_locked"
                    }
                    conn.send(json.dumps(all_locked_msg).encode())
                    opponent.send(json.dumps(all_locked_msg).encode())

            elif message["type"] == "bomb":
                row = message["row"]
                col = message["col"]
                coord = (row,col)
                print(f"SERVER: Player {player_index} shoots opponent at {coord}")
                opponent.send(json.dump(message).encode())

            elif message["type"] == "hit_status":
                if message["all_sunk"] == True:
                    GAME_OVER = True
                opponent.send(json.dump(message).encode())

            else:
                print(f"Sends {message} to other player")
                opponent.send(json.dumps(message).encode())

        except:
            print(f"SERVER ERROR: MESSAGE ERROR 2")
            break

    conn.close()

"""
# handle_client V2
def handle_client(player_index):
    global GAME_OVER, game_over_sent, player1_locked, player2_locked
    
    conn = clients[player_index]
    opponent = clients[1 - player_index]
    
    while True:
        try:
            # If someone has lost, notify both clients once
            if GAME_OVER and not game_over_sent:
                game_over_sent = True
                msg = {"type": "game_over", "status": True}
                send_json(conn, msg)
                send_json(opponent, msg)
                
            # Read any complete JSON messages from this client
            lines = recv_json_lines(player_index)
            if not lines:
                time.sleep(0.01) # Avoid busy-looping
                continue
                
            for line in lines:
                if not line.strip():
                    continue
                    
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    print("SERVER ERROR: Invalid JSON received")
                    continue
                    
                print(f"Received from Player {player_index + 1}: {message}")
                
                # --- Ship count sync (Player 1 picks, both clients should receive) ---
                if message.get("type") == "ship_count":
                    new_message = {
                        "type": "set_ship_count",
                        "count": message.get("count")
                    }
                    send_json(conn, new_message)
                    send_json(opponent, new_message)
                    
                # --- Placement lock sync ---
                elif message.get("type") == "place_ships":
                    print("Server: Ships Placed and Locked")
                    
                    if player_index == 0:
                        player1_locked = True
                    else:
                        player2_locked = True
                        
                    # Once both players lock, notify both clients to proceed to RUNNING_GAME
                    if player1_locked and player2_locked:
                        all_locked_msg = {"type": "all_ships_locked"}
                        send_json(conn, all_locked_msg)
                        send_json(opponent, all_locked_msg)
                        
                # --- RUNNING_GAME: forward bomb to defender ---
                elif message.get("type") == bomb:
                    # Forward bomb to opponent, opponent will compute hit/miss and reply with hit_status
                    send_json(opponent, message)
                
                # --- RUNNING_GAME: forward hit_status back to shooter ---
                elif message.get("type") == "hit_status":
                    # If defender says all ships sunk, end match
                    if message.get("all_sunk") is True:
                        GAME_OVER = True
                        
                    send_json(opponent, message)
                    
                # --- Default: forward unknown messages to opponent (for development testing) ---
                else:
                    send_json(opponent, message)
        
        except Exception as e:
            print("SERVER ERROR:", e)
            break
    
    try:
        conn.close()
    except OSError:
        pass
"""
# Start a thread for each player
threading.Thread(target=handle_client, args=(0,), daemon=True).start()
threading.Thread(target=handle_client, args=(1,), daemon=True).start()


"""
# Keep server alive V2
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
        pass
finally:
    for c in clients:
        try:
            if c:
                c.close()
        except OSError:
            pass
    server.close()
"""

# Keep server alive
while True:
    pass