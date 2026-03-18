#This file is for creating the interactive battleship board
#This file will handle the frontend of our battleship game

import pygame
import sys
import os
import backend
import math
import time

# ------------------ CONFIG ------------------
os.environ['SDL_VIDEO_CENTERED'] = '1' 

GRID_SIZE = 10
CELL_SIZE = 20     # Shrinks the squares so the window isn't too tall
LABEL_MARGIN = 20
GRID_PADDING = 40
WINDOW_WIDTH = (GRID_SIZE * CELL_SIZE) + (2 * GRID_PADDING) + 150 
WINDOW_HEIGHT = (GRID_SIZE * CELL_SIZE * 2) + 180

BG_COLOR = (30, 30, 30)
GRID_COLOR = (200, 200, 200)
HOVER_COLOR = (100, 180, 255)


SHIP_COLOR = (180, 180, 180)
SHIP_PADDING = 20
SHIP_BLOCK_SIZE = CELL_SIZE

LOCK_BUTTON_RECT = pygame.Rect(WINDOW_WIDTH // 2 - 90, WINDOW_HEIGHT - 50, 80, 30)
RESET_BUTTON_RECT = pygame.Rect(WINDOW_WIDTH // 2 + 10, WINDOW_HEIGHT - 50, 80, 30)

SINGLE_PLAYER_RECT = pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 80, 300, 60)
MULTI_PLAYER_RECT = pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 20, 300, 60)

button_rect_width = 80
button_rect_height = 30
BUTTON_RECT = pygame.Rect(WINDOW_WIDTH//2 - button_rect_width//2,
                          WINDOW_HEIGHT - (button_rect_height + 20),
                          button_rect_width,
                          button_rect_height)

EASY_RECT   = pygame.Rect(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 90, 200, 50)
MEDIUM_RECT = pygame.Rect(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 20, 200, 50)
HARD_RECT   = pygame.Rect(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 50, 200, 50)

# ------------------ INIT ------------------
pygame.init() # Initialize pygame
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Battleship Game")
clock = pygame.time.Clock()

# ------------------ ANIMATIONS ------------------
animations = [] # Stores active animations
font_big = pygame.font.SysFont("arial", 60, bold=True)

# ------------------ CELL CLASS ------------------
class Cell:
    def __init__(self, rect, grid_id, row, col):
        self.rect = rect
        self.grid_id = grid_id
        self.row = row
        self.col = col

    def draw(self, surface, mouse_pos):
        color = HOVER_COLOR if self.rect.collidepoint(mouse_pos) else GRID_COLOR
        pygame.draw.rect(surface, color, self.rect, 2)

    def handle_click(self):
        letters = "ABCDEFGHIJ"
        coord = f"{letters[self.row]}{self.col + 1}"

        print(f"Clicked Grid {self.grid_id} at {coord} (Row {self.row}, Col {self.col})")
        return self.grid_id, self.row, self.col
    
    def get_coords(self):
         return self.row, self.col

# ------------------ SHIP CLASS ------------------
class Ship:
    def __init__(self, length, x, y):
        self.length = length
        self.x = x
        self.y = y
        self.orig_x = x
        self.orig_y = y
        self.orig_row = None
        self.orig_col = None
        self.orig_orientation = "V"
        self.last_valid_orientation = "V"
        self.orientation= "V" # Default to Vertical
        self.block_size = CELL_SIZE
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        self.placed = False # Visual feedback: turns green when successfully placed
        self.grid_row = None
        self.grid_col = None

    def get_rects(self):
        rects = []
        for i in range(self.length):
            # If Horizontal, move X; if Vertical, move Y
            curr_x = self.x + (i * CELL_SIZE if self.orientation == "H" else 0)
            curr_y = self.y + (i * CELL_SIZE if self.orientation == "V" else 0)
            rects.append(pygame.Rect(curr_x, curr_y, CELL_SIZE, CELL_SIZE))
        return rects

    def draw(self, surface):
        for rect in self.get_rects():
            color = (0, 255, 0) if self.placed else SHIP_COLOR
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (50, 50, 50), rect, 2)

    def handle_event(self, event): #handles events related to dragging and placing a ship on a grid
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect in self.get_rects():
                if rect.collidepoint(event.pos):
                    self.dragging = True
                    self.orig_x = self.x
                    self.orig_y = self.y
                    self.orig_row = self.grid_row
                    self.orig_col = self.grid_col
                    self.orig_orientation = self.orientation

                    if self.placed and self.grid_row is not None and self.grid_col is not None:
                        cells = backend.compute_ship_cells(self.grid_row, self.grid_col, self.length, self.orientation)
                        backend.remove_ship_from_grid(cells)
                        self.placed = False
                    self.offset_x = self.x - event.pos[0]
                    self.offset_y = self.y - event.pos[1]
                    break

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                
                #Snapping
                col = round((self.x - GRID_PADDING) / CELL_SIZE)
                row = round((self.y - GRID_PADDING) / CELL_SIZE)

                cells = backend.compute_ship_cells(row, col, self.length, self.orientation)

                if backend.can_place_ship(cells):
                    self.x = GRID_PADDING + col * CELL_SIZE
                    self.y = GRID_PADDING + row * CELL_SIZE
                    self.grid_col = col
                    self.grid_row = row
                    self.placed = True
                    for r, c in cells:
                        backend.grid[r][c] = "S"
                else:
                    print("Invalid spot! Snapping back...")
                    self.x = self.orig_x
                    self.y = self.orig_y
                    self.grid_row = self.orig_row
                    self.grid_col = self.orig_col
                    self.orientation = self.orig_orientation
                
                    if self.grid_row is not None:
                        self.placed = True
                        old_cells = backend.compute_ship_cells(self.grid_row, self.grid_col, self.length, self.orientation)
                        for r, c in old_cells:
                            backend.grid[r][c] = "S"
                    else:
                        self.placed = False

        elif event.type == pygame.KEYDOWN and self.dragging:
            # Press 'R' while dragging to rotate
            if event.key == pygame.K_r:
                self.orientation = "H" if self.orientation == "V" else "V"

        elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.x = event.pos[0] + self.offset_x
                self.y = event.pos[1] + self.offset_y


# ------------------ SHIP CREATION ------------------
ships = []
def create_ships(num_ships):
    global ships
    ships.clear()

    ships_start_x = GRID_PADDING + GRID_SIZE * CELL_SIZE + 20
    ships_start_y = top_grid_y

    for ship_length in range(1, num_ships + 1):
        ship = Ship(ship_length, ships_start_x, ships_start_y)
        ships.append(ship)

        ships_start_y += (ship_length * CELL_SIZE) + 10

def reset_local_ui_state():
    global ships_selected, started_running_game, multi_bomb_mode, ships
    ships_selected = False
    started_running_game = False
    multi_bomb_mode = False
    ships.clear()

'''
PyGame Drawing Functions:
The following functions use PyGame to draw the frontend/UI of the game.
They are called during the main gameplay loop and draw things depending on the Game State.
'''
def draw_main_menu(mouse_pos):
    font = pygame.font.SysFont(None, 60)
    button_font = pygame.font.SysFont(None, 40)

    # single_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 - 80, 300, 60)
    # multi_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, WINDOW_HEIGHT//2 + 20, 300, 60)

    sp_color = (70,130,180)
    mp_color = (70,130,180)

    if SINGLE_PLAYER_RECT.collidepoint(mouse_pos):
        sp_color = (100,160,210)
        pygame.draw.rect(screen, (255, 255, 255), SINGLE_PLAYER_RECT.inflate(-6, -6), 2)

    if MULTI_PLAYER_RECT.collidepoint(mouse_pos):
        mp_color = (100,160,210)
        pygame.draw.rect(screen, (255, 255, 255), MULTI_PLAYER_RECT.inflate(-6, -6), 2)

    screen.fill(BG_COLOR)

    title = font.render("Battleship", True, (255,255,255))
    screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, WINDOW_HEIGHT//4))

    pygame.draw.rect(screen, sp_color, SINGLE_PLAYER_RECT)
    pygame.draw.rect(screen, mp_color, MULTI_PLAYER_RECT)

    single_text = button_font.render("Single Player", True, (255,255,255))
    multi_text = button_font.render("Multi-Player", True, (255,255,255))

    screen.blit(single_text, (SINGLE_PLAYER_RECT.centerx - single_text.get_width()//2,
                                SINGLE_PLAYER_RECT.centery - single_text.get_height()//2))

    screen.blit(multi_text, (MULTI_PLAYER_RECT.centerx - multi_text.get_width()//2,
                                MULTI_PLAYER_RECT.centery - multi_text.get_height()//2))
    
    return SINGLE_PLAYER_RECT, MULTI_PLAYER_RECT

def draw_difficulty_selection(mouse_pos):
    screen.fill(BG_COLOR)
    font       = pygame.font.SysFont(None, 40)
    btn_font   = pygame.font.SysFont(None, 32)
    title      = font.render("Select Difficulty", True, (255, 255, 255))
    screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, WINDOW_HEIGHT//4))

    for rect, label, base_color in [
        (EASY_RECT,   "Easy",   (60, 160, 60)),
        (MEDIUM_RECT, "Medium", (70, 130, 180)),
        (HARD_RECT,   "Hard",   (180, 50, 50)),
    ]:
        color = tuple(min(c + 30, 255) for c in base_color) if rect.collidepoint(mouse_pos) else base_color
        pygame.draw.rect(screen, color, rect)
        text = btn_font.render(label, True, (255, 255, 255))
        screen.blit(text, (rect.centerx - text.get_width()//2, rect.centery - text.get_height()//2))


def draw_message(message):
    screen.fill(BG_COLOR)
    font = pygame.font.SysFont(None, 30)
    title = font.render(message,True,(255,255,255))

    screen.blit(
        title,
        (WINDOW_WIDTH // 2 - title.get_width() // 2,
         WINDOW_HEIGHT // 2 - title.get_height())
    )

def draw_button(mouse_pos, text="Back", color=(180, 50, 50), border_rad=0):
    font = pygame.font.SysFont(None, 20)

    # Draw button
    if BUTTON_RECT.collidepoint(mouse_pos):
        color = (230,100,100)
        pygame.draw.rect(screen, (255, 255, 255), BUTTON_RECT.inflate(4, 4), 2, border_radius=border_rad)
    else:
        pygame.draw.rect(screen, color, BUTTON_RECT, border_radius=border_rad)

    # Draw text
    text = font.render(text, True, (255, 255, 255))
    screen.blit(text, (BUTTON_RECT.centerx - text.get_width()//2, BUTTON_RECT.centery - text.get_height()//2))

def draw_waiting_for_player(message, number=0):
    screen.fill(BG_COLOR)

    font = pygame.font.SysFont(None, 30)
    small_font = pygame.font.SysFont(None, 20)
    
    if number == 0:
        title = font.render(f"Waiting for Other Player...", True, (255, 255, 255))
    else:
        title = font.render(f"Waiting for Player {number}...", True, (255, 255, 255))
    subtitle = small_font.render(message, True, (180, 180, 180))

    screen.blit(
        title,
        (WINDOW_WIDTH // 2 - title.get_width() // 2,
         WINDOW_HEIGHT // 2 - title.get_height())
    )

    screen.blit(
        subtitle,
        (WINDOW_WIDTH // 2 - subtitle.get_width() // 2,
         WINDOW_HEIGHT // 2 + 10)
    )

def draw_ship_selection():
    screen.fill(BG_COLOR)

    font = pygame.font.SysFont(None, 32)
    small_font = pygame.font.SysFont(None, 24)

    title_text = font.render("Select Number of Ships (1 - 5)", True, (255, 255, 255))
    instruction_text = small_font.render("Press a number key 1, 2, 3, 4, or 5", True, (200, 200, 200))

    screen.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, WINDOW_HEIGHT // 3))
    screen.blit(instruction_text, (WINDOW_WIDTH // 2 - instruction_text.get_width() // 2, WINDOW_HEIGHT // 2))

    pygame.display.flip()

def draw_game_over(winner):
    screen.fill(BG_COLOR)

    font = pygame.font.SysFont(None, 30)
    small_font = pygame.font.SysFont(None, 20)

    title = title = font.render(f"GAME OVER", True, (255, 255, 255))
    subtitle = ""

    if winner:
        subtitle = small_font.render("Victory!!!", True, (180, 180, 180))
    else:
        subtitle = small_font.render("Defeat...", True, (180, 180, 180))

    screen.blit(
        title,
        (WINDOW_WIDTH // 2 - title.get_width() // 2,
         WINDOW_HEIGHT // 2 - title.get_height())
    )

    screen.blit(
        subtitle,
        (WINDOW_WIDTH // 2 - subtitle.get_width() // 2,
         WINDOW_HEIGHT // 2 + 10)
    )

def draw_loading_circle(angle):
    """
    surface: pygame surface to draw on
    center: (x, y)
    radius: circle radius
    angle: current rotation angle
    """
    screen.fill(BG_COLOR)

    center = (WINDOW_WIDTH//2, WINDOW_HEIGHT//2)
    radius = 15
    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    rect.center = center

    start_angle = angle
    end_angle = angle + math.pi / 2   # length of arc

    pygame.draw.arc(screen, (255, 255, 255), rect, start_angle, end_angle, 4)

def draw_ship_placement():
    screen.fill(BG_COLOR)

    draw_coordinates(GRID_PADDING, GRID_PADDING)

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(
                GRID_PADDING + col * CELL_SIZE,
                GRID_PADDING + row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(screen, GRID_COLOR, rect, 2)
   
    active_ship = None
    for ship in ships:
        if ship.dragging:
            active_ship = ship
        else:
            ship.draw(screen)
    
    if active_ship:
        active_ship.draw(screen)

    #pygame.display.flip()

# ------------------ GRID CREATION ------------------
def create_grid(grid_id, start_x, start_y):
    cells = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(
                start_x + col * CELL_SIZE,
                start_y + row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            cells.append(Cell(rect, grid_id, row, col))
    return cells

top_grid_y = GRID_PADDING + 10
bottom_grid_y = top_grid_y + (GRID_SIZE * CELL_SIZE) + 30

top_grid = create_grid(0, GRID_PADDING, top_grid_y)
bottom_grid = create_grid(1, GRID_PADDING, bottom_grid_y)

all_cells = top_grid + bottom_grid

# ------------------ COORDINATE DRAWING ------------------
def draw_coordinates(start_x, start_y):
    font = pygame.font.SysFont("monospace", 15, bold=True)
    letters = "ABCDEFGHIJ"
    
    for i in range(GRID_SIZE):
        # --- Draw Numbers (Horizontal: 1-10) ---
        # Centered above each column
        num_text = font.render(str(i + 1), True, (255, 255, 255))
        num_x = start_x + (i * CELL_SIZE) + (CELL_SIZE // 2 - num_text.get_width() // 2)
        num_y = start_y - LABEL_MARGIN
        screen.blit(num_text, (num_x, num_y))
        
        # --- Draw Letters (Vertical: A-J) ---
        # Centered to the left of each row
        let_text = font.render(letters[i], True, (255, 255, 255))
        let_x = start_x - LABEL_MARGIN
        let_y = start_y + (i * CELL_SIZE) + (CELL_SIZE // 2 - let_text.get_height() // 2)
        screen.blit(let_text, (let_x, let_y))

# ------------------ DRAW LOCK AND RESET BUTTON ------------------
def draw_control_buttons(mouse_pos):
    lock_color = (50, 200, 50)
    reset_color = (200, 50, 50)

    # Lock Button
    if LOCK_BUTTON_RECT.collidepoint(mouse_pos):
        lock_color = (70, 230, 70)  
        pygame.draw.rect(screen, (255, 255, 255), LOCK_BUTTON_RECT.inflate(4, 4), 2)
    else:
        pygame.draw.rect(screen, lock_color, LOCK_BUTTON_RECT)

    # Reset Button
    if RESET_BUTTON_RECT.collidepoint(mouse_pos):
        reset_color = (220, 80, 70)
        pygame.draw.rect(screen, (255, 255, 255), RESET_BUTTON_RECT.inflate(4, 4), 2)
    else:
        pygame.draw.rect(screen, reset_color, RESET_BUTTON_RECT)
 
    
    font = pygame.font.SysFont(None, 18)
    lock_text = font.render("LOCK", True, (255, 255, 255))
    reset_text = font.render("RESET", True, (255, 255, 255))
    
    screen.blit(lock_text, (LOCK_BUTTON_RECT.centerx - lock_text.get_width() // 2, LOCK_BUTTON_RECT.centery - lock_text.get_height() // 2))
    screen.blit(reset_text, (RESET_BUTTON_RECT.centerx - reset_text.get_width() // 2, RESET_BUTTON_RECT.centery - reset_text.get_height() // 2))
    
    return LOCK_BUTTON_RECT, RESET_BUTTON_RECT

# ------------------ RUNNING_GAME DRAW HELPERS ------------------
def draw_backend_ships():
    # Draw ships stored in backend.ships onto the bottom grid.
    # Assumes backend.ships is a list of lists of (row, col) tuples.
    # Meant for the RUNNING_GAME state
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if backend.grid[row][col] == "S":
                x = GRID_PADDING + col * CELL_SIZE
                y = bottom_grid_y + row * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, (0, 200, 0), rect)
                pygame.draw.rect(screen, (50, 50, 50), rect, 2)

def draw_mark_cell(cell_value, origin_y, row, col):
    # Only draw for hit/miss cells.
    if cell_value not in ("X", "O", "D"):
        return

    x = GRID_PADDING + col * CELL_SIZE
    y = origin_y + row * CELL_SIZE
    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

    # Red = hit, Blue = miss, Dark red = sunk
    color = None
    if cell_value == "X":
        color = (220, 80, 80)
    elif cell_value == "O":
        color = (225, 225, 220)
    elif cell_value == "D":
        color = (125, 40, 40)
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, (50, 50, 50), rect, 2)

def draw_marks():
    # Draw opponent board marks (top) and your board marks (bottom) in one pass.
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            draw_mark_cell(backend.target_grid[r][c], top_grid_y, r, c)  # Your shots
            draw_mark_cell(backend.grid[r][c], bottom_grid_y, r, c)  # Opponent shots

def draw_multi_bomb_preview(mouse_pos):
    # When multi-bomb mode is armed, show the player
    # which 3x3 area will be attacked before they click.
    if not multi_bomb_mode:
        return

    for cell in top_grid:
        if cell.rect.collidepoint(mouse_pos):
            center_row, center_col = cell.get_coords()
            cells = backend.compute_multi_bomb_cells(center_row, center_col)

            # Highlight every valid cell in the 3x3 area.
            for r, c in cells:
                x = GRID_PADDING + c * CELL_SIZE
                y = top_grid_y + r * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, (240, 220, 80), rect, 3)

def draw_status_panel():
    # Simple UI panel to explain state during demo
    panel_x = GRID_PADDING + GRID_SIZE * CELL_SIZE + 15
    panel_y = 30

    font = pygame.font.SysFont(None, 20)

    if backend.multi_bomb_used:
        multi_bomb_status = "USED"
    elif multi_bomb_mode:
        multi_bomb_status = "ARMED"
    else:
        multi_bomb_status = "READY"

    if backend.GAME_MODE == 2:
        player_label = str(backend.player_id)
    else:
        player_label = "Single Player"

    lines = [
        f"Player: {player_label}",
        f"Your turn: {backend.your_turn}",
        f"Multi-bomb: {multi_bomb_status}",
        f"Press M: Toggle",
        f"Ships sunk: {backend.get_num_ships_sunk()}/{len(backend.ships)}",
        f"Enemy ships sunk: {backend.opponent_ships_sunk}/{len(backend.ships)}",
        f"Shots hit: {len(backend.shots_sent_hit)}",
        f"Shots missed: {len(backend.shots_sent_miss)}",
        f"Hits recv: {len(backend.shots_received_hit)}",
        f"Miss recv: {len(backend.shots_received_miss)}",
    ]

    for i, text in enumerate(lines):
        surf = font.render(text, True, (230, 230, 230))
        screen.blit(surf, (panel_x, panel_y + i * 22))

def draw_lock_button(mouse_pos):
    # Place button at the bottom center
    button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 70, WINDOW_HEIGHT - 50, 140, 35)
    if button_rect.collidepoint(mouse_pos):
        color = (70, 230, 70)  
        pygame.draw.rect(screen, (255, 255, 255), button_rect.inflate(4, 4), 2)
    else:
        color = (50, 200, 50)  
    pygame.draw.rect(screen, color, button_rect)
    
    font = pygame.font.SysFont(None, 24)
    text = font.render("LOCK SHIPS", True, (255, 255, 255))
    screen.blit(text, (button_rect.centerx - text.get_width() // 2, button_rect.centery - text.get_height() // 2))
    return button_rect

def draw_animations(screen):
    """
    Draws animations on top of the current screen.
    
    Args:
        screen (pygame.Surface): The current display surface.
        font (pygame.font.Font): The font used to render text.
    """
    font = font_big
    global animations
    current_time = time.time()
    fade_duration = 1.5  # seconds

    # We'll remove animations that have expired
    remaining_animations = []

    for anim in animations:
        elapsed = current_time - anim['start']
        if elapsed < fade_duration:
            # Compute alpha (opacity)
            alpha = max(0, 255 * (1 - elapsed / fade_duration))
            
            # Render the text surface
            text_surface = font.render("HIT!", True, (255, 0, 0))
            text_surface.set_alpha(int(alpha))
            
            # Calculate top-left from center location
            text_rect = text_surface.get_rect(center=anim['loc'])
            
            # Blit onto the screen
            screen.blit(text_surface, text_rect)

            # Keep animation in the list
            remaining_animations.append(anim)

    # Update global list to remove finished animations
    animations = remaining_animations

# ------------------ ANIMATIONS ------------------
def trigger_animation(num, loc):
    print("Adding Animation")
    animations.append({
        "type": num,
        "loc": loc,
        "start": time.time()
    })

# ------------------ START SERVER FUNCTION ------------------
import threading
def start_network():
    backend.init_network()
    backend.update_game_state("WAITING_FOR_PLAYERS_TO_CONNECT")

# ------------------ MAIN LOOP ------------------
# Please use these player_id variables when printing sending/printing things like: "Waiting For Player X"
player1_id = 1 
player2_id = 2
opponent_id = None
loading_angle = 0.0

running = True
ships_selected = False # Used to move on from ship selection stage
started_running_game = False # True if the game has fully started
multi_bomb_mode = False
game_mode = 0

# ------------------------------------ GAMEPLAY LOOP ------------------------------------
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    if backend.player_id != None:
        opponent_id = (backend.player_id % 2) + 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        game_state = backend.GAME_STATE
        
        # ------------------ MAIN MENU STATE ------------------
        if game_state == "MAIN_MENU":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if SINGLE_PLAYER_RECT.collidepoint(event.pos):
                    reset_local_ui_state()
                    backend.multi_bomb_used = False
                    backend.update_game_mode(1)
                    backend.update_game_state("SELECT_DIFFICULTY")

                if MULTI_PLAYER_RECT.collidepoint(event.pos):
                    backend.update_game_state("LOADING")
                    backend.update_game_mode(2)

                    threading.Thread(target=start_network, daemon=True).start()

        # ------------------ LOADING STATE ------------------
        elif game_state == "LOADING":
            pass

        # ------------------ WAITING FOR PLAYERS TO CONNECT STATE ------------------
        elif game_state == "WAITING_FOR_PLAYERS_TO_CONNECT":
            pass

        # ------------------ SHIP SELECTION STATE ------------------
        elif game_state == "SELECT_SHIPS":
            if backend.player_id == player1_id:
                if event.type == pygame.KEYDOWN:
                    if event.key in [
                        pygame.K_1,
                        pygame.K_2,
                        pygame.K_3,
                        pygame.K_4,
                        pygame.K_5,
                    ]:
                        ship_count = int(event.unicode)
                        print(f"Selected {ship_count} ships")

                        create_ships(ship_count)
                        backend.update_ship_count(ship_count)
                        backend.update_game_state("PLACE_SHIPS")

            if backend.player_id == player2_id:
                ship_count = backend.ship_count
                if ship_count > 0 and ships_selected == False:
                    ships_selected = True
                    print(f"Player {player1_id} selected {ship_count} ships")
                    print(f"SHIP COUNT: {ship_count}")
                    create_ships(ship_count)

                    backend.update_game_state("PLACE_SHIPS")

        # ------------------ SHIP PLACING STATE ------------------
        elif game_state == "PLACE_SHIPS":
            for ship in ships:
                ship.handle_event(event)    

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if RESET_BUTTON_RECT.collidepoint(event.pos):
                    print("Resetting Ships...")
                    # Clear the backend grid
                    backend.grid = [["." for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    for ship in ships:
                        create_ships(len(ships))

                elif LOCK_BUTTON_RECT.collidepoint(event.pos):
                    all_valid = all(s.placed for s in ships)
                    if all_valid:
                        backend.ships.clear()
                        for s in ships:
                            backend.ships.append(backend.compute_ship_cells(s.grid_row, s.grid_col, s.length, s.orientation)) #
                        backend.submit_placement()
                        backend.update_game_state("WAITING_FOR_OPPONENT")

        # ------------------ WAITING FOR OTHER PLAYER STATE ------------------
        elif game_state == "WAITING_FOR_OPPONENT":
            if backend.all_ships_locked:
                backend.update_game_state("RUNNING_GAME")

        # ------------------ RUNNING GAME STATE ------------------
        elif game_state == "RUNNING_GAME":
            # Initialize turn rule once when the match begins
            if not started_running_game:
                started_running_game = True

                # This gives Player 1 the first move without needing server logic yet.
                backend.your_turn = (backend.player_id == player1_id)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    # Only allow multibomb mode if it has not already been used.
                    if backend.multi_bomb_used:
                        print("MULTI-BOMB already used this game.")
                        multi_bomb_mode = False
                    else:
                        # Press M to toggle multi-bomb mode on or off.
                        multi_bomb_mode = not multi_bomb_mode
                        print(f"MULTI-BOMB MODE: {multi_bomb_mode}")

                if event.key == pygame.K_a:
                    trigger_animation(1, (WINDOW_WIDTH//2, WINDOW_HEIGHT//2))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Gate input so only the active player can fire
                # if backend.your_turn:
                    # Only allow shots on the opponent grid (top grid)

                for cell in top_grid:
                    if cell.rect.collidepoint(mouse_pos):
                        cell.handle_click()
                        click_row, click_col = cell.get_coords()

                        # Can only send bomb if it is your turn
                        if backend.your_turn:
                            if multi_bomb_mode:
                                # If multi-bomb mode is armed, send one 3x3 attack
                                # instead of a normal single-cell bomb.
                                print(f"FRONTEND: Sending MULTI-BOMB to {click_row, click_col}")
                                backend.send_multi_bomb(click_row, click_col)

                                # Turn off the mode after one use so the player must
                                # intentionally arm it again next time.
                                multi_bomb_mode = False
                            else:
                                print(f"FRONTEND: Sending Bomb to {click_row, click_col}")
                                backend.send_bomb(click_row, click_col)
                        break

        # ------------------ GAME OVER STATE ------------------
        elif game_state == "GAME_OVER":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if BUTTON_RECT.collidepoint(mouse_pos):
                    ships_selected = False
                    started_running_game = False
                    multi_bomb_mode = False
                    game_mode = 0
                    backend.disconnect_from_server()
                    backend.reset_game()

        # ======================================== SINGLE PLAYER =======================================
        elif game_state == "SELECT_DIFFICULTY":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if EASY_RECT.collidepoint(event.pos):
                    backend.ai_difficulty = "easy"
                    backend.update_game_state("SELECT_SHIPS_SP")
        
                elif MEDIUM_RECT.collidepoint(event.pos):
                    backend.ai_difficulty = "medium"
                    backend.update_game_state("SELECT_SHIPS_SP")
        
                elif HARD_RECT.collidepoint(event.pos):
                    backend.ai_difficulty = "hard"
                    backend.update_game_state("SELECT_SHIPS_SP")

        elif game_state == "SELECT_SHIPS_SP":
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                    ship_count = int(event.unicode)
                    backend.set_ship_count(ship_count)
                    create_ships(ship_count)
                    backend.update_game_state("PLACE_SHIPS_SP")

        elif game_state == "PLACE_SHIPS_SP":
            for ship in ships:
                ship.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if RESET_BUTTON_RECT.collidepoint(event.pos):
                    backend.grid = [["." for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    create_ships(len(ships))

                elif LOCK_BUTTON_RECT.collidepoint(event.pos):
                    all_valid = all(s.placed for s in ships)
                    if all_valid:
                        backend.ships.clear()
                        for s in ships:
                            backend.ships.append(
                                backend.compute_ship_cells(s.grid_row, s.grid_col, s.length, s.orientation)
                        )
                        backend.ai_place_ships(len(ships))
                        backend.your_turn = True
                        backend.update_game_state("RUNNING_GAME_SP")

        elif game_state == "RUNNING_GAME_SP":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    # Only allow multi-bomb mode if it has not already been used.
                    if backend.multi_bomb_used:
                        print("MULTI-BOMB already used this game.")
                        multi_bomb_mode = False
                    else:
                        multi_bomb_mode = not multi_bomb_mode
                        print(f"MULTI-BOMB MODE: {multi_bomb_mode}")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if backend.your_turn:
                    for cell in top_grid:
                        if cell.rect.collidepoint(mouse_pos):
                            r, c = cell.get_coords()

                            if multi_bomb_mode:
                                print(f"FRONTEND: Sending SINGLE-PLAYER MULTI-BOMB to {(r, c)}")
                                used_successfully, all_sunk = backend.player_multi_bomb_ai(r, c)

                                # Only disable the mode after a successful use.
                                if used_successfully:
                                    multi_bomb_mode = False

                                    if all_sunk:
                                        backend.winner = True
                                        backend.update_game_state("GAME_OVER")
                                    else:
                                        # Multi-bomb always ends the player's turn in single-player.
                                        backend.your_turn = False
                                break

                            else:
                                if (r, c) not in backend.shots_sent_hit and (r, c) not in backend.shots_sent_miss:
                                    hit, sunk, all_sunk = backend.player_shoot_ai(r, c)
                                    if all_sunk:
                                        backend.winner = True
                                        backend.update_game_state("GAME_OVER")
                                    else:
                                        if not hit:
                                            backend.your_turn = False
                                break

    if backend.GAME_STATE == "RUNNING_GAME_SP" and not backend.your_turn:
        pygame.time.wait(500)
        row, col, hit, sunk, all_sunk = backend.ai_take_turn()
        if all_sunk:
            backend.winner = False
            backend.update_game_state("GAME_OVER")
        else:
            backend.your_turn = True

    # ------------------ DRAWING ------------------
    if len(animations) > 0:
        draw_animations(screen)

    if game_state == "MAIN_MENU":
        draw_main_menu(mouse_pos)

    elif game_state == "WAITING_FOR_PLAYERS_TO_CONNECT":
        draw_waiting_for_player(f"Waiting for opponent to connect...", opponent_id)
        
    elif game_state == "LOADING":
        draw_loading_circle(loading_angle)
        loading_angle += 0.1
    
    elif game_state == "SELECT_SHIPS":
        if backend.player_id == player1_id:
            draw_ship_selection()
        if backend.player_id == player2_id:
            draw_waiting_for_player(f"Player {player1_id} will select 1-5 ships", player1_id)
    
    elif game_state == "PLACE_SHIPS":
        draw_ship_placement()
        draw_coordinates(GRID_PADDING, GRID_PADDING)
        draw_control_buttons(mouse_pos)
    
    elif game_state == "WAITING_FOR_OPPONENT":
        draw_waiting_for_player(f"Player {opponent_id} is still placing their ships", opponent_id)

    elif game_state == "RUNNING_GAME":
        screen.fill(BG_COLOR)
        draw_coordinates(GRID_PADDING, top_grid_y)
        draw_coordinates(GRID_PADDING, bottom_grid_y)
        for cell in all_cells:
            cell.draw(screen, mouse_pos)
        
        # Draw backend ships and hit/miss overlays on bottom grid
        draw_backend_ships()
        draw_multi_bomb_preview(mouse_pos)
        draw_status_panel()
        draw_marks()
    
    elif game_state == "GAME_OVER":
        draw_game_over(backend.winner)
        draw_button(mouse_pos, color=(0,255,0), text="Main Menu")
    
    elif game_state == "SINGLE_PLAYER":
        draw_message("Single player construction in progress")
        draw_button(mouse_pos)

    elif game_state == "SELECT_DIFFICULTY":
        draw_difficulty_selection(mouse_pos)

    elif game_state == "SELECT_SHIPS_SP":
        draw_ship_selection()

    elif game_state == "PLACE_SHIPS_SP":
        draw_ship_placement()
        draw_coordinates(GRID_PADDING, GRID_PADDING)
        draw_control_buttons(mouse_pos)

    elif game_state == "RUNNING_GAME_SP":
        screen.fill(BG_COLOR)
        draw_coordinates(GRID_PADDING, top_grid_y)
        draw_coordinates(GRID_PADDING, bottom_grid_y)
        for cell in all_cells:
            cell.draw(screen, mouse_pos)
        draw_backend_ships()
        draw_multi_bomb_preview(mouse_pos)
        draw_status_panel()
        draw_marks()        

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()