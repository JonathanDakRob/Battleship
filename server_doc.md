# Battleship Server Documentation (`server.py`)

## Overview

This module implements the multiplayer server for the Battleship game.

It:

- Accepts two TCP client connections
- Assigns player IDs
- Relays messages between players
- Tracks game synchronization state
- Manages ship locking and game-over conditions
- Uses JSON-based newline-delimited messaging
- Runs each client connection in its own thread

Dependencies:

- `socket`
- `json`
- `threading`

---

# Global Configuration

## Network Configuration

| Name | Type | Description |
|------|------|------------|
| `HOST` | `str` | Server bind address (`"0.0.0.0"` = listen on all interfaces) |
| `PORT` | `int` | TCP port number (5000) |

---

# Global State Variables

## Connection Management

| Name | Type | Description |
|------|------|------------|
| `clients` | `List[socket.socket]` | List containing two connected client sockets |

---

## Game State Memory

| Name | Type | Description |
|------|------|------------|
| `ships` | `List` | Stores ship placements (last received placement) |
| `player1_locked` | `bool` | Whether Player 1 has locked ships |
| `player2_locked` | `bool` | Whether Player 2 has locked ships |
| `p1_game_state` | `Optional[str]` | Player 1's current frontend state |
| `p2_game_state` | `Optional[str]` | Player 2's current frontend state |
| `player_turn` | `int` | Current turn holder (1 or 2) |
| `GAME_OVER` | `bool` | Whether the game has ended |
| `winner` | `Optional[int]` | Winning player ID |

---

# Functions

---

## `send(conn: socket.socket, msg: dict) -> None`

### Description

Sends a JSON message to a client.

- Serializes `msg` using `json.dumps`
- Appends newline (`\n`) delimiter
- Sends via `conn.sendall()`

### Parameters

- `conn: socket.socket`  
  The client connection to send to.

- `msg: dict`  
  Dictionary message to transmit.

---

## `handle_message(conn: socket.socket, player_index: int, message: dict) -> None`

### Description

Processes a message received from a client and determines how it should be handled or forwarded.

### Parameters

- `conn: socket.socket`  
  Connection of the sender.

- `player_index: int`  
  Index in `clients` list (0 or 1).

- `message: dict`  
  Parsed JSON message from client.

---

## Supported Message Types

The server relays and/or processes the following message types:

| Type | Direction | Parameters | Purpose |
|------|----------|------------|----------|
| `"player_id"` | Server → Client | `player: int` | Assigns player number (1 or 2) upon connection |
| `"start_game"` | Server → Client | *(none)* | Indicates both players connected and game may begin |
| `"game_state"` | Client → Server | `sender: int`, `state: str` | Updates server with current client game state |
| `"ship_count"` | Client → Server | `count: int` | Sends selected number of ships |
| `"set_ship_count"` | Server → Both Clients | `count: int` | Synchronizes ship count between players |
| `"place_ships"` | Client → Server | `ships: List[List[Tuple[int,int]]]` | Sends finalized ship placement and locks player |
| `"all_ships_locked"` | Server → Both Clients | *(none)* | Indicates both players finished placing ships |
| `"bomb"` | Client → Server → Opponent | `row: int`, `col: int` | Sends attack coordinates |
| `"hit_status"` | Client → Server → Opponent | `row: int`, `col: int`, `status: bool`, `sunk: bool`, `ship_coords: List[Tuple[int,int]]`, `all_sunk: bool` | Reports result of a bomb |
| `"change_turn"` | Server → Both Clients | *(none)* | Toggles active turn after a miss |
| `"game_over"` | Client → Server → Both Clients | `winner: int` | Announces winner and ends match |

---

### Parameter Notes

- `status`  
  - `True` = hit  
  - `False` = miss  

- `sunk`  
  - `True` if the attacked ship was completely destroyed

- `all_sunk`  
  - `True` if all ships of the defending player are destroyed  

- `ship_coords`  
  - Included only when `sunk == True`  
  - Used to visually mark the entire sunk ship  

---

### Architecture Reminder

- The server does **not validate gameplay logic**.
- It acts as a **relay and synchronization authority**.
- Game rule enforcement (hit detection, sinking, win condition) occurs entirely in the backend.
- The server only coordinates:
  - Player assignment
  - Ship placement synchronization
  - Turn switching
  - Game termination broadcast

## `handle_client(player_index: int) -> None`

### Description

Handles continuous communication with a single client.

- Runs in its own thread
- Receives newline-delimited JSON messages
- Buffers incoming data
- Parses complete messages
- Passes each message to `handle_message()`

### Parameters

- `player_index: int`  
  Index of client in `clients` list (0 or 1).

---

### Behavior

- Reads data via `conn.recv(4096)`
- Splits messages by newline
- Parses JSON
- Gracefully closes connection on error/disconnect

---

## `main() -> None`

### Description

Initializes and runs the Battleship server.

### Behavior

1. Creates TCP socket
2. Binds to `HOST` and `PORT`
3. Listens for two players
4. Accepts exactly two connections
5. Assigns player IDs (1 and 2)
6. Starts a thread for each client
7. Sends `"start_game"` message to both players
8. Keeps server alive indefinitely

---

### Upon Player Connection

1. Player connects
2. Server sends:
   ```json
   {
     "type": "player_id",
     "player": 1 or 2
   }