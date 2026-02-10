#This file will handle the backend of our battleship game
# backend.py

import socket
import json

SERVER_IP = "127.0.0.1"
PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, PORT))

print("Connected to server")

def send_bomb(row, col):
    msg = {
        "type": "bomb",
        "row": row,
        "col": col
    }
    print(f"Bomb sent to {row},{col}")
    sock.sendall(json.dumps(msg).encode())