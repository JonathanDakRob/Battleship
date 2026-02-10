#This file handles the server for Battleship
#server.py

import socket
import json

HOST = "0.0.0.0"   # listen on all interfaces
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(2)

print("Server waiting for players...")

clients = []

# Accept exactly two players
for i in range(2):
    conn, addr = server.accept()
    print(f"Player {i} connected from {addr}")
    clients.append(conn)

print("Both players connected. Game starting.")