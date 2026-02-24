#This file handles the server for Battleship
#server.py

import socket
import json
import threading

HOST = "0.0.0.0"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(2)

print("Server waiting for players...")

clients = []

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

def handle_client(player_index):
    conn = clients[player_index]
    opponent = clients[1 - player_index]


    global p1_game_state, p2_game_state, ships, player1_locked, player2_locked

    while True:
        try:
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

            elif message["type"] == "shoot":
                coord = message["coord"]
                print(f"SERVER: Player {player_index} shoots opponent at {coord}")
                opponent.send(json.dump(message).encode())

            elif message["type"] == "hit_status":
                opponent.send(json.dump(message).encode())

            else:
                print(f"Sends {message} to other player")
                opponent.send(json.dumps(message).encode())

        except:
            print(f"SERVER ERROR: MESSAGE ERROR 2")
            break

    conn.close()


# Start a thread for each player
threading.Thread(target=handle_client, args=(0,), daemon=True).start()
threading.Thread(target=handle_client, args=(1,), daemon=True).start()

# Keep server alive
while True:
    pass