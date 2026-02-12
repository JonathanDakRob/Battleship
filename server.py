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
    conn, addr = server.accept()
    print(f"Player {i} connected from {addr}")
    clients.append(conn)

    # Send player ID to client
    conn.send(json.dumps({
        "type": "player_id",
        "player": i
    }).encode())

print("Both players connected. Game starting.")


def handle_client(player_index):
    conn = clients[player_index]
    opponent = clients[1 - player_index]

    while True:
        try:
            data = conn.recv(4096).decode()
            if not data:
                print("SERVER ERROR: MESSAGE ERROR 1")
                break

            message = json.loads(data)
            print(f"Received from Player {player_index}: {message}")

            # Forward message to opponent
            opponent.send(json.dumps(message).encode())

        except:
            print("SERVER ERROR: MESSAGE ERROR 2")
            break

    conn.close()


# Start a thread for each player
threading.Thread(target=handle_client, args=(0,), daemon=True).start()
threading.Thread(target=handle_client, args=(1,), daemon=True).start()

# Keep server alive
while True:
    pass