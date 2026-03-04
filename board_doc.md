# Battleship Frontend Documentation (`board.py`)
## Overview
This module implements the **pygame-based frontend** for a two-player Battleship game.  
It handles:

- Window and grid rendering
- Ship selection and placement
- Mouse and keyboard interaction
- UI state transitions
- Communication triggers to the `backend` module

Dependencies:
- `pygame`
- `backend`
- `sys`
- `os`

---

# Global Constants
## Configuration Constants

| Name            | Type  | Description                                  |
|-----------------|-------|----------------------------------------------|
| `GRID_SIZE`     | `int` | Number of rows and columns per grid (10x10). |
| `CELL_SIZE`     | `int` | Pixel size of each grid cell.                |
| `LABEL_MARGIN`  | `int` | Spacing for coordinate labels.               |
| `GRID_PADDING`  | `int` | Padding around grid edges.                   |
| `WINDOW_WIDTH`  | `int` | Width of game window in pixels.              |
| `WINDOW_HEIGHT` | `int` | Height of game window in pixels.             |

---

## Color Constants
All are of type `Tuple[int, int, int]` (RGB):

- `BG_COLOR`
- `GRID_COLOR`
- `HOVER_COLOR`
- `RESET_COLOR`
- `SHIP_COLOR`

---

## Ship UI Constants

| Name              | Type  | Description                                    |
|-------------------|-------|------------------------------------------------|
| `SHIP_PADDING`    | `int` | Spacing for ship selection display.            |
| `SHIP_BLOCK_SIZE` | `int` | Size of each ship block (same as `CELL_SIZE`). |

---

## Button Rectangles

| Name                | Type          | Description                             |
|---------------------|---------------|-----------------------------------------|
| `LOCK_BUTTON_RECT`  | `pygame.Rect` | Rectangle defining LOCK button bounds.  |
| `RESET_BUTTON_RECT` | `pygame.Rect` | Rectangle defining RESET button bounds. |

---

## Runtime Global Variables

| Name                   | Type                | Description                                    |
|------------------------|---------------------|------------------------------------------------|
| `screen`               | `pygame.Surface`    | Main display surface.                          |
| `clock`                | `pygame.time.Clock` | Used to cap frame rate.                        |
| `ships`                | `List[Ship]`        | List of ship objects for placement.            |
| `top_grid_y`           | `int`               | Y coordinate of top grid.                      |
| `bottom_grid_y`        | `int`               | Y coordinate of bottom grid.                   |
| `top_grid`             | `List[Cell]`        | Cells for opponent board.                      |
| `bottom_grid`          | `List[Cell]`        | Cells for player board.                        |
| `all_cells`            | `List[Cell]`        | Combined list of both grids.                   |
| `player1_id`           | `int`               | ID for player 1.                               |
| `player2_id`           | `int`               | ID for player 2.                               |
| `opponent_id`          | `int`               | ID of opponent player.                         |
| `running`              | `bool`              | Main loop control flag.                        |
| `ships_selected`       | `bool`              | Tracks whether ship count is chosen.           |
| `started_running_game` | `bool`              | Ensures turn initialization only happens once. |

---

# Classes

---

## `Cell`

### Description
Represents a single grid cell in either the top or bottom grid.

### Constructor

```python
Cell(rect: pygame.Rect, grid_id: int, row: int, col: int)

## `Ship`

### Description
Represents a draggable ship during the ship placement phase.

A `Ship` object:

- Tracks its pixel position on screen
- Tracks its grid position in the backend
- Supports dragging with the mouse
- Supports rotation using the `R` key
- Snaps to grid cells when dropped
- Validates placement using backend logic
- Updates the backend grid when placed

---

### Constructor

```python
Ship(length: int, x: int, y: int)
