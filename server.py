#This file handles the server for Battleship
#server.py

import socket
import json
import threading

HOST = "0.0.0.0"
PORT = 5000

clients = []

# Game related memory
ships = []
player1_locked = False
player2_locked = False
p1_game_state = None
p2_game_state = None
player_turn = 1

GAME_OVER = False
winner = None

def send(conn, msg):
    conn.sendall((json.dumps(msg) + "\n").encode())

def handle_message(conn, player_index, message):
    opponent = clients[1 - player_index]

    global p1_game_state, p2_game_state, ships, player1_locked, player2_locked
    global GAME_OVER, p1_game_state, p2_game_state, ships, player1_locked, player2_locked

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
        send(conn,new_message)
        send(opponent,new_message)

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
            send(conn,all_locked_msg)
            send(opponent,all_locked_msg)

    elif message["type"] == "bomb":
        row = message["row"]
        col = message["col"]
        coord = (row,col)
        print(f"SERVER: Player {player_index} shoots opponent at {coord}")
        send(opponent,message)

    elif message["type"] == "hit_status":
        if message["all_sunk"] == True:
            GAME_OVER = True
        if message["status"] == False:
            changeTurn_msg = {
                "type": "change_turn"
            }
            send(opponent,changeTurn_msg)
            send(conn,changeTurn_msg)
        send(opponent,message)
    
    elif message["type"] == "game_over":
        global winner
        GAME_OVER = True
        winner = message["winner"]

        send(opponent,message)
        send(conn,message)

    else:
        print(f"Sends {message} to other player")
        send(opponent,message)


def handle_client(player_index):
    buffer = ""
    message = ""

    conn = clients[player_index]

    global p1_game_state, p2_game_state, ships, player1_locked, player2_locked
    global GAME_OVER, p1_game_state, p2_game_state, ships, player1_locked, player2_locked

    while True:
        try:
            data = conn.recv(4096).decode()
            if not data:
                print("SERVER ERROR: MESSAGE ERROR 1")
                break

            buffer += data

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                message = json.loads(line)
                print(f"Received from Player {player_index}: {message}")
                handle_message(conn, player_index, message)


        except Exception as e:
            print("SERVER: Client disconnected:", e)
            break

    conn.close()

def main():
    global clients

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(2)

    print("Server waiting for players...")

    # Accept two players
    for i in range(2):
        player_id = i+1
        conn, addr = server.accept()
        print(f"Player {player_id} connected from {addr}")
        clients.append(conn)

        # Send player ID to client
        msg = {
            "type": "player_id",
            "player": player_id
        }
        send(conn,msg)

    # Start a thread for each player
    threading.Thread(target=handle_client, args=(0,), daemon=True).start()
    threading.Thread(target=handle_client, args=(1,), daemon=True).start()

    start_msg = {
        "type": "start_game"
    }
    for conn in clients:
        send(conn,start_msg)

    print("Both players connected. Game starting.")

    # Keep server alive
    while True:
        pass