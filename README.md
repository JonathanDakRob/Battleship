# Networked Battleship (Local Multiplayer Game)

## Overview

This project is a **networked Battleship game** built in Python using:

- `socket` for TCP networking  
- `threading` for concurrency  
- `json` for message serialization  

The system is structured to resemble a real online multiplayer architecture, with:

- A **Server** that coordinates communication  
- Two **Clients** (each running a frontend + backend)  
- A clear separation between:
  - UI logic  
  - Game logic  
  - Networking logic  

The goal of this project was to model how a real client-server multiplayer game might be structured, rather than to create a production-ready deployment.

---

## License and Usage

This project is **completely free to use**.  
Anyone is welcome to take code, ideas, or concepts from this project at no cost.

**Please provide credit** if you use this work in your own projects, tutorials, or demonstrations.  
No formal license is required, but acknowledgment is appreciated as a courtesy.

---

## Architecture

The project consists of three main components:

### 1. Server (`server.py`)
- Accepts two client connections
- Assigns player IDs
- Relays messages between players
- Synchronizes turn changes and game start/end
- Does **not** enforce gameplay rules

### 2. Backend (`backend.py`)
- Contains all game logic
- Maintains board state
- Validates ship placement
- Handles bomb resolution (hit/miss/sunk)
- Tracks win conditions
- Communicates with the server via JSON messages
- Automatically starts the server if one is not already running

### 3. Frontend (`board.py`)
- Handles user interaction
- Displays game boards
- Sends player actions to the backend
- Initiates the networking connection

---

## How It Works

1. Running `board.py` the first time:
   - Starts the server automatically (if it is not already running)
   - Connects the first client
2. Running `board.py` a second time:
   - Connects the second client to the same server
3. Once both clients are connected:
   - Players select ship counts and place ships
   - When both lock ships, the match begins
4. Players take turns sending bomb coordinates.
5. The backend determines hit/miss/sunk conditions.
6. When all ships of one player are destroyed, the game ends.

The server acts purely as a **relay and synchronizer**.  
All rule enforcement happens on each client’s backend.

---

## Important Note About Local Execution

This project is currently designed to run **locally on a single machine**.

- Both clients connect to `127.0.0.1`
- The server is automatically started by the first client instance
- All processes run on the same machine

Yes — this technically conflicts with the secret-information nature of Battleship.

Because both clients and the server run locally:
- Game state exists in memory on the same system
- A determined user could inspect memory or logs to see opponent ship data
- A player could just screen-look

This project is **not intended to be launched or deployed publicly**.

It is a **learning and architectural exercise**, demonstrating:

- Client-server structure
- Multiplayer synchronization
- JSON-based message protocols
- Threaded networking in Python
- Clean separation of concerns

---

## Running the Project

To play locally:

1. Run `board.py`
2. Run `board.py` again in a second terminal window
3. Play

No manual server startup is required.

---

## Educational Purpose

This project demonstrates:

- TCP socket programming
- Concurrent client handling
- Game state synchronization
- Turn-based protocol design
- Clean modular architecture

It is best viewed as a **networked game architecture prototype**, not a production-ready Battleship implementation.
