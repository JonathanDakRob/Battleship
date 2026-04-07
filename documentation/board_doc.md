# backend.py Documentation

## Overview

`backend.py` is the **core logic engine** of the Battleship project.

While `board.py` is responsible for **rendering the game and handling user interaction**, `backend.py` is responsible for **enforcing the actual rules of the game** and maintaining the **authoritative game state**.

This file handles:

- Board creation and management
- Ship placement validation
- Attack resolution
- Hit / miss / sunk logic
- Turn management
- Special abilities (Multi-Bomb / Radar)
- Win / loss detection
- AI logic for single-player
- Multiplayer client communication
- Timer-related game state updates

In short:

> `backend.py` determines **what is true** in the game.

---

# Purpose of `backend.py`

The main responsibility of this file is to act as the **source of truth** for gameplay.

It should answer questions such as:

- Where are the ships?
- Is this placement valid?
- Did that attack hit?
- Is it the player’s turn?
- Has a ship been sunk?
- Has the game ended?
- Can this special ability still be used?
- What move should the AI make next?
- What state should be synchronized over multiplayer?

If `board.py` is the **visual shell**, `backend.py` is the **rules engine**.

---

# High-Level Responsibilities

`backend.py` is responsible for several major systems:

## 1. Game State Ownership
Stores and updates the current state of the match.

## 2. Board Logic
Creates, tracks, and modifies player and opponent boards.

## 3. Ship Management
Places ships, validates them, tracks damage, and determines when ships are sunk.

## 4. Turn Resolution
Processes attacks and controls whose turn it is.

## 5. Special Abilities
Implements custom rules for:
- Multi-Bomb
- Radar Scan

## 6. AI Behavior
Controls single-player enemy decision-making across difficulty levels.

## 7. Multiplayer Client Logic
Communicates with `server.py` when in multiplayer mode.

## 8. Game Outcome Logic
Determines when a game has been won or lost.

---

# Core Design Philosophy

A programmer working on this file should understand one important rule:

> `backend.py` should be the **authority**, and `board.py` should be the **display layer**.

That means:

- `backend.py` should decide whether a move is valid
- `backend.py` should decide whether a ship is sunk
- `backend.py` should decide whether a special ability can still be used
- `backend.py` should decide whether the game is over

The frontend can help prevent bad input, but it should not replace backend validation.

This separation is critical for:
- maintainability
- multiplayer correctness
- debugging
- future expansion

---

# Major Concepts in This File

# 1. Game State Model

At its core, `backend.py` likely stores the current state of the match using a collection of variables, lists, dictionaries, or class attributes.

Typical game state includes:

## Board Data
- Player board
- Opponent board / enemy board
- Shot history
- Ship locations

## Turn Data
- Current turn owner
- Whether input should be allowed
- Timeout state

## Special Ability State
- Whether Multi-Bomb is still available
- Whether Radar is still available

## Outcome State
- Whether the game is over
- Who won
- Which ships are sunk

## Multiplayer State
- Whether connected
- Player ID
- Opponent readiness
- Synced remote actions

## AI State (single-player)
- Difficulty mode
- AI memory of prior hits
- AI targeting state
- AI delay / behavior flags

## Why this matters
A lot of bugs happen when two pieces of state disagree.

For example:
- a ship is visually placed but not logically placed
- a move appears valid but backend rejects it
- a turn switches visually but backend still thinks it’s the other player’s turn

For future developers, **state consistency** is one of the most important concerns in this file.

---

# 2. Board Representation

One of the most important backend systems is how the boards are stored.

The game likely uses a **10x10 grid representation**, typically stored as:

- a 2D list
- a nested list of cells
- a list of coordinates
- or a dictionary keyed by positions

Each board cell may represent things like:

- empty water
- ship present
- hit
- miss
- sunk segment
- scanned area / revealed state

## Why this matters
Nearly every gameplay system depends on board representation, including:

- placement validation
- attack resolution
- radar scans
- AI target selection
- win detection

## Developer note
If a future developer changes the board structure, they will likely need to update:

- placement logic
- attack logic
- rendering assumptions in `board.py`
- AI logic
- multiplayer synchronization

This is a **high-impact system**.

---

# 3. Ship Representation

Ships are likely represented by one of the following:

- lists of coordinates
- objects / dictionaries containing:
  - size
  - position
  - orientation
  - hit count
  - sunk status

A ship system usually needs to answer:

- Where is the ship?
- How many cells does it occupy?
- Which cells have been hit?
- Is the ship sunk?

## Common ship properties
A developer working on this area should expect logic related to:

- ship length
- horizontal / vertical orientation
- occupied coordinates
- whether each segment has been hit
- whether the ship has been fully destroyed

## Why this matters
A ship is more than just “some filled cells” — it often needs metadata to support:

- sinking detection
- animations
- smoke effects
- AI target cleanup
- endgame detection

---

# Core Systems

# 4. Board Initialization

The backend must create a fresh board at the start of each game.

This typically includes:

- generating empty boards
- resetting hit/miss state
- clearing special ability usage
- resetting turn data
- resetting AI memory
- resetting multiplayer sync flags

## Developer note
Any time a “new game” or “restart” feature is added, this initialization logic must be complete.

## Common bug source
One of the easiest bugs in a game backend is **partial reset**, where some state is cleared but other state is accidentally preserved.

Examples:
- AI still remembers previous targets
- Multi-Bomb stays “used” across games
- old sunk ship state carries over
- multiplayer ready flags remain set

---

# 5. Ship Placement Validation

This is one of the most important gameplay systems.

The backend is responsible for validating whether a ship placement is legal.

Typical placement checks include:

- Is the ship fully inside the board?
- Does it overlap another ship?
- Is the orientation valid?
- Does the ship occupy the correct number of cells?

## Important design rule
Even if `board.py` visually prevents bad placements, `backend.py` should still validate them.

This matters because:
- frontend bugs happen
- multiplayer data should not be blindly trusted
- future automation / AI placement may call backend directly

## Typical placement workflow

1. Proposed coordinates are generated
2. Coordinates are checked for board bounds
3. Coordinates are checked for overlap
4. If valid, the ship is committed to board state

## Developer warning
Placement bugs can create extremely difficult-to-debug downstream problems later in the match.

A bad placement may not fail immediately — it may show up later as:
- invisible ships
- impossible hits
- incorrect sunk detection
- broken win logic

---

# 6. Attack Resolution

Attack resolution is one of the central jobs of `backend.py`.

When a player attacks a cell, the backend must determine:

- Was the move valid?
- Was the cell already attacked?
- Was it a hit or miss?
- Was a ship sunk?
- Did the attack end the game?
- Should the turn switch?

## Typical attack resolution flow

1. Receive target coordinate
2. Validate target is inside board
3. Check whether the cell has already been attacked
4. Determine whether a ship occupies the cell
5. Mark hit or miss
6. Update ship damage state
7. Check if ship is sunk
8. Check if all ships are sunk
9. Update turn state
10. Return result to frontend / network layer

## Why this matters
This is one of the most heavily reused gameplay systems, and it likely powers:

- normal attacks
- AI attacks
- multiplayer attacks
- Multi-Bomb sub-attacks

A bug here can affect almost everything.

---

# 7. Hit / Miss / Sunk Logic

Attack resolution usually relies on a lower-level rules system for evaluating shot results.

This logic typically determines:

## Hit
A valid attack lands on a ship segment.

## Miss
A valid attack lands on empty water.

## Sunk
A ship has had all of its segments hit.

## Game Over
All ships belonging to one side have been sunk.

## Important note
Sunk detection should not rely only on visual state.

It should be based on the backend’s internal ship data.

## Developer note
If another programmer wants to add:
- special effects
- scoring
- sound hooks
- achievements

this is often a good place to attach those events.

---

# 8. Turn Management

Turn logic determines whose action is allowed at any given time.

This system is responsible for:

- starting the correct player
- alternating turns
- preventing illegal actions out of turn
- handling skipped turns
- handling timeouts

## Why this matters
Turn bugs are especially dangerous in multiplayer because they can cause desync between players.

## Common turn-related problems
- both players think it’s their turn
- neither player thinks it’s their turn
- turn changes before animation finishes
- timeout triggers but turn doesn’t switch
- AI acts twice

## Developer warning
Turn changes often interact with:
- animation timing
- networking
- timeout logic
- special abilities

This makes it one of the more sensitive systems in the file.

---

# 9. Special Ability System

This project includes custom gameplay mechanics beyond standard Battleship.

These are important because they introduce **non-standard game rules** that future developers must understand clearly.

---

# 10. Multi-Bomb Logic

Multi-Bomb is a one-time special ability that attacks a **3x3 region** instead of a single cell.

## Backend responsibilities
The backend must:

- verify the player still has Multi-Bomb available
- determine the 3x3 affected cells
- ignore out-of-bounds cells safely
- resolve each valid sub-cell attack
- avoid duplicate or illegal state changes
- mark Multi-Bomb as used
- return enough information for frontend animation / display

## Important implementation detail
Multi-Bomb is not just “one attack.”

It is effectively a **batch of coordinated attacks** that must still obey game rules.

## Developer warning
This feature can create bugs if not carefully handled, especially with:

- edge-of-board targeting
- repeated cells
- already-hit cells
- sunk ship updates
- win condition checks mid-resolution

## Recommended design principle
Treat Multi-Bomb as a wrapper around the normal attack system rather than reimplementing all attack logic separately.

That way:
- one attack engine stays authoritative
- fewer rule inconsistencies occur

---

# 11. Radar Scan Logic

Radar is a one-time special ability that scans a **3x3 region** without dealing damage.

Instead of attacking, it reveals whether **at least one ship** exists in the scanned area.

## Backend responsibilities
The backend must:

- verify Radar is still available
- compute the 3x3 scan region
- ignore out-of-bounds cells safely
- inspect whether any ship occupies those cells
- return a result to the frontend
- mark Radar as used

## Important note
Radar should not mutate attack / hit state unless explicitly designed to do so.

Its role is informational, not damaging.

## Developer warning
Radar is easy to accidentally implement incorrectly if it shares too much code with attack logic.

A programmer working on this should make sure:
- scans do not mark hits
- scans do not trigger sunk logic
- scans do not alter win conditions

---

# 12. Ability Usage Tracking

Both special abilities are likely one-time use.

That means the backend must track:

- whether Multi-Bomb has been used
- whether Radar has been used

## Why this matters
This state must be reliable across:
- single-player
- multiplayer
- frontend refreshes
- game restarts

## Common bug source
A very common bug is when the frontend disables the ability visually, but the backend still allows it — or vice versa.

This is another reason the backend should be the authority.

---

# Single-Player Systems

# 13. AI Architecture

One of the most significant systems in `backend.py` is the single-player AI.

This file likely contains the logic that determines how the enemy behaves in single-player mode.

The AI probably handles:

- selecting targets
- reacting to hits
- deciding whether to use abilities
- changing strategy based on difficulty

## Important concept
The AI is not just “random shot generation.”

At higher difficulties, it likely maintains **stateful targeting behavior**.

That means it may remember:
- prior hits
- candidate follow-up cells
- possible ship orientation
- cells already ruled out

This makes the AI more realistic and more challenging.

---

# 14. Easy AI

Easy mode likely behaves with minimal intelligence.

Typical behavior:
- random valid shots
- little or no follow-up strategy
- no serious targeting optimization

## Why this matters
Easy mode should still:
- obey all game rules
- avoid invalid repeat shots
- remain deterministic enough to debug

Even “simple” AI still needs to be correct.

---

# 15. Medium AI

Medium mode likely uses a hybrid strategy.

Typical behavior:
- hunt randomly until it scores a hit
- once a hit is found, target nearby cells
- attempt to finish ships more intelligently than Easy mode

## Common internal structures
A medium AI often tracks:
- “hit queue” or target queue
- neighboring candidate cells
- prior successful hit clusters

## Developer note
This difficulty is usually the best place to expand if another programmer wants to make the AI feel more human.

---

# 16. Hard AI

Hard mode likely uses significantly stronger targeting logic.

Typical behavior may include:
- near-perfect target selection
- strong ship-finishing behavior
- strategic move ordering
- highly efficient follow-up targeting

Depending on implementation, this may feel close to “cheating” if too strong.

## Developer warning
If modifying Hard AI, balance matters.

An AI that is too perfect can become frustrating rather than fun.

## Good developer question
When improving Hard AI, ask:

> “Does this make the AI smarter, or just less enjoyable?”

That distinction matters for game design.

---

# 17. AI Turn Resolution

The backend likely contains logic for executing the AI’s turn.

This usually includes:

1. determine AI target
2. resolve attack
3. apply results
4. possibly queue follow-up logic
5. return results to frontend for display

## Important note
AI actions should ideally use the **same attack engine** as human actions.

That keeps behavior consistent and avoids duplicated rule logic.

---

# Multiplayer Systems

# 18. Multiplayer Client Role

In multiplayer mode, `backend.py` likely acts as the **client-side network logic** for the player.

This means it is responsible for:

- connecting to `server.py`
- sending local actions to the server
- receiving opponent actions from the server
- updating local state from remote messages

## Important architecture note
`backend.py` is not the multiplayer server.

It is the **client-side authority** for this player’s local game state.

---

# 19. Network Configuration

The file likely includes values such as:

- `SERVER_IP`
- `PORT`

These define where the multiplayer client connects.

## Developer note
If another programmer wants to support:
- LAN play
- internet hosting
- configurable server entry
- UI-based IP entry

this is one of the first places they’ll need to modify.

---

# 20. Socket Communication

The multiplayer system likely uses Python sockets for communication.

The backend probably handles:

- opening a socket connection
- sending structured messages
- receiving messages asynchronously
- parsing message types
- applying remote state changes

## Likely message types
A future developer should expect message categories such as:

- player joined
- ready state
- ship placement complete
- attack
- radar use
- multi-bomb use
- timeout
- turn switch
- game over

## Developer warning
Networking bugs often appear as “game logic bugs” even when the logic itself is correct.

If multiplayer behaves strangely, the problem may actually be:
- dropped / malformed message
- ordering issue
- frontend/backend desync
- state update race condition

---

# 21. Message Processing

A key backend responsibility is converting raw network messages into game state updates.

This may include logic like:

- parsing JSON payloads
- dispatching by message type
- applying attacks to local board
- syncing turn state
- syncing special ability usage
- syncing win/loss state

## Why this matters
This is the layer where multiplayer becomes “real.”

If this system is fragile, multiplayer will feel inconsistent or broken.

## Developer recommendation
Keep message handling as centralized and predictable as possible.

If a programmer expands multiplayer later, avoid scattering message-handling logic across unrelated functions.

---

# 22. Timeout Handling

The game includes a turn timer, and `backend.py` likely contains logic related to timeout resolution.

Possible responsibilities include:

- tracking turn start time
- determining whether a player has timed out
- skipping a turn when time expires
- notifying the frontend
- notifying the multiplayer server

## Important distinction
The frontend may display the timer, but the backend should be trusted for **actual timeout consequences**.

## Developer warning
Timer bugs often interact badly with:
- multiplayer sync
- turn switching
- AI turns
- animation delays

---

# 23. Win / Loss Detection

The backend must determine when the match has ended.

This usually occurs when:
- all ships belonging to one side are sunk

## Backend responsibilities
- detect endgame correctly
- stop further gameplay actions
- return / broadcast winner state
- preserve final board state for display

## Developer warning
Win detection should happen after **every action that can cause damage**, including:

- normal attacks
- Multi-Bomb
- possibly AI actions
- multiplayer remote attacks

It is easy to accidentally forget to check win conditions in non-standard attack paths.

---

# Integration with `board.py`

This is one of the most important relationships in the codebase.

`board.py` depends heavily on `backend.py`, but they should still have a clean division of responsibility.

## `backend.py` should provide
- board state
- turn state
- move validity
- attack results
- ability availability
- game-over state
- multiplayer updates
- AI move outcomes

## `board.py` should provide
- visuals
- input
- menus
- animations
- user interaction flow

## Important design rule
The frontend should not need to “guess” game truth if the backend already knows it.

Examples:
- if backend knows a ship is sunk, frontend should display that state
- if backend knows a move is invalid, frontend should not override it
- if backend knows Radar is used, frontend should reflect that

This is essential for maintainability.

---

# Important Developer Workflows

This section explains where a future programmer should look depending on what they want to change.

---

## If you want to change game rules
Look in:
- attack logic
- turn logic
- placement validation
- win/loss checks
- special ability rules

---

## If you want to change AI behavior
Look in:
- difficulty-specific targeting logic
- target selection helpers
- AI memory / state
- AI turn execution flow

---

## If you want to change multiplayer behavior
Look in:
- socket connection setup
- message send / receive functions
- JSON parsing / message handling
- sync flags / readiness logic

---

## If you want to add a new special ability
Look in:
- ability state tracking
- action validation
- attack / scan helper systems
- multiplayer message synchronization
- frontend integration expectations

---

## If you want to debug strange gameplay behavior
Check:
- board representation
- ship data consistency
- attack resolution path
- turn switching
- frontend/backend assumptions

---

# Common Maintenance Risks

This file is one of the highest-risk files in the project because it combines:

- rules logic
- state mutation
- AI
- networking
- special mechanics
- turn progression

A small bug here can have large consequences.

## High-risk areas
The most likely regression-prone systems are:

- ship placement validation
- attack resolution
- Multi-Bomb logic
- AI follow-up targeting
- multiplayer synchronization
- timeout handling

---

# Recommended Testing Checklist

Any developer making changes to `backend.py` should test the following flows:

---

## Board / Placement
- valid placement
- overlap rejection
- edge-of-board placement
- full game reset

---

## Combat
- normal hit
- normal miss
- repeated shot rejection
- sunk ship detection
- full win detection

---

## Multi-Bomb
- center-board use
- edge-of-board use
- already-hit overlap
- sinking via area attack
- game-ending via area attack

---

## Radar
- valid scan
- edge-of-board scan
- scan result correctness
- one-time use enforcement

---

## AI
- Easy mode valid attacks
- Medium mode follow-up targeting
- Hard mode consistency
- no invalid repeat AI shots

---

## Multiplayer
- connect successfully
- both players ready
- attack synchronization
- ability synchronization
- timeout synchronization
- game-over synchronization

---

# Suggested Refactoring Opportunities

If this project grows, `backend.py` would likely benefit from being broken into smaller modules.

## Recommended future refactors

### 1. Extract Board Logic
Could move to:
- `board_logic.py`

### 2. Extract Ship Logic
Could move to:
- `ships.py`

### 3. Extract AI
Could move to:
- `ai.py`

### 4. Extract Multiplayer Client
Could move to:
- `network_client.py`

### 5. Extract Special Abilities
Could move to:
- `abilities.py`

This would reduce complexity and make debugging easier.

---

# Summary

`backend.py` is the **gameplay brain** of the Battleship project.

It is responsible for:

- enforcing Battleship rules
- maintaining board state
- validating actions
- processing attacks
- tracking ships and victory
- running AI
- synchronizing multiplayer actions
- managing special abilities

For any programmer working on this project, the most important thing to remember is:

> `backend.py` should remain the **authoritative source of truth** for gameplay state and rules.

Keeping that boundary clear will make the game easier to maintain, expand, and debug.