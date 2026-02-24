#This file is for creating the interactive battleship board

#This file will handle the frontend of our battleship game

import pygame
import sys

import backend

# ------------------ CONFIG ------------------
import os
os.environ['SDL_VIDEO_CENTERED'] = '1' 

GRID_SIZE = 10
CELL_SIZE = 20     # Shrinks the squares so the window isn't too tall
LABEL_MARGIN= 20
GRID_PADDING = 40
WINDOW_WIDTH = (GRID_SIZE * CELL_SIZE) + (2 * GRID_PADDING) + 150 
WINDOW_HEIGHT = (GRID_SIZE * CELL_SIZE * 2) + 180

BG_COLOR = (30, 30, 30)
GRID_COLOR = (200, 200, 200)
HOVER_COLOR = (100, 180, 255)
RESET_COLOR = (200, 50, 50)

SHIP_COLOR = (180, 180, 180)
SHIP_PADDING = 20
SHIP_BLOCK_SIZE = CELL_SIZE

LOCK_BUTTON_RECT = pygame.Rect(WINDOW_WIDTH // 2 - 90, WINDOW_HEIGHT - 50, 80, 30)
RESET_BUTTON_RECT = pygame.Rect(WINDOW_WIDTH // 2 + 10, WINDOW_HEIGHT - 50, 80, 30)


# ------------------ INIT ------------------

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Two 10x10 Grids")
clock = pygame.time.Clock()

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
        
        #Data to be sent to the backend
        if self.grid_id == 0:
            backend.send_bomb(self.row, self.col)


        print(f"Clicked Grid {self.grid_id} at {coord} (Row {self.row}, Col {self.col})")
        return (self.grid_id, self.row, self.col)

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
        self.placed= False # Visual feedback: turns green when successfully placed
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

                    if self.placed:
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

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.x = event.pos[0] + self.offset_x
                self.y = event.pos[1] + self.offset_y

    
# ------------------ SHIP SELECTION ------------------
def draw_ship_selection():
    screen.fill(BG_COLOR)

    font = pygame.font.SysFont(None, 32)
    small_font = pygame.font.SysFont(None, 24)

    title_text = font.render("Select Number of Ships (1 - 5)", True, (255, 255, 255))
    instruction_text = small_font.render("Press a number key 1, 2, 3, 4, or 5", True, (200, 200, 200))

    screen.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, WINDOW_HEIGHT // 3))
    screen.blit(instruction_text, (WINDOW_WIDTH // 2 - instruction_text.get_width() // 2, WINDOW_HEIGHT // 2))

    #pygame.display.flip()

def draw_backend_ships():
    """
    Draw ships stored in backend.ships onto the bottom grid.
    Assumes backend.ships is a list of lists of (row, col) tuples.

    Meant for the RUNNING_GAME state
    """

    for ship in backend.ships:
        for (row, col) in ship:

            x = GRID_PADDING + col * CELL_SIZE
            y = bottom_grid_y + row * CELL_SIZE

            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

            pygame.draw.rect(screen, (0, 200, 0), rect)
            pygame.draw.rect(screen, (50, 50, 50), rect, 2)

# ------------------ SHIP PLACEMENT ------------------
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

def draw_waiting_for_player(number, message):
    screen.fill(BG_COLOR)

    font = pygame.font.SysFont(None, 30)
    small_font = pygame.font.SysFont(None, 20)

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

# ------------------ CONFIG UPDATES ------------------
LABEL_MARGIN = 20  # Space for letters and numbers
# Adjust GRID_PADDING if needed to ensure labels fit on screen
GRID_PADDING = 40 

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
    # Lock Button
    pygame.draw.rect(screen, (50, 200, 50), LOCK_BUTTON_RECT)
    
    # Reset Button
    pygame.draw.rect(screen, RESET_COLOR, RESET_BUTTON_RECT)
    
    font = pygame.font.SysFont(None, 18)
    lock_text = font.render("LOCK", True, (255, 255, 255))
    reset_text = font.render("RESET", True, (255, 255, 255))
    
    screen.blit(lock_text, (LOCK_BUTTON_RECT.centerx - lock_text.get_width() // 2, LOCK_BUTTON_RECT.centery - lock_text.get_height() // 2))
    screen.blit(reset_text, (RESET_BUTTON_RECT.centerx - reset_text.get_width() // 2, RESET_BUTTON_RECT.centery - reset_text.get_height() // 2))
    
    return LOCK_BUTTON_RECT, RESET_BUTTON_RECT

    """
def draw_lock_button(mouse_pos):
    # Place button at the bottom center
    button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 70, WINDOW_HEIGHT - 50, 140, 35)
    if button_rect.collidepoint(mouse_pos):
        color = (70, 230, 70)  
       
        pygame.draw.rect(screen, (255, 255, 255), button_rect.inflate(4, 4), 2)
    else:
        color = (50, 200, 50)  
    pygame.draw.rect(screen, (50, 200, 50), button_rect)
    
    font = pygame.font.SysFont(None, 24)
    text = font.render("LOCK SHIPS", True, (255, 255, 255))
    screen.blit(text, (button_rect.centerx - text.get_width() // 2, button_rect.centery - text.get_height() // 2))
    return button_rect

"""
# ------------------ MAIN LOOP ------------------
# Please use these player_id variables when printing sending/printing things like: "Waiting For Player X"
player1_id = 1 
player2_id = 2
opponent_id = -1
if backend.player_id == 1:
    opponent_id = 2
else:
    opponent_id = 1

running = True
ships_selected = False # Used to move on from ship selection stage

print(f"You Are Player {backend.player_id}")

while running:
    mouse_pos = pygame.mouse.get_pos()

    #print(f"GAME STATE: {backend.GAME_STATE}")

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ------------------ SHIP SELECTION STATE ------------------
        if backend.GAME_STATE == "SELECT_SHIPS":
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
        elif backend.GAME_STATE == "PLACE_SHIPS":
            for ship in ships:
                ship.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if RESET_BUTTON_RECT.collidepoint(event.pos):
                    print("Resetting Ships...")
                    # Clear the backend grid
                    backend.grid = [["." for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
                    for ship in ships:
                        ship.placed = False
                        ship.x, ship.y = ship.orig_x, ship.orig_y # Back to tray
                        ship.grid_row, ship.grid_col = None, None

                elif LOCK_BUTTON_RECT.collidepoint(event.pos):
                    all_valid = all(s.placed for s in ships)
                    if all_valid:
                        backend.ships.clear()
                        for s in ships:
                            backend.ships.append(backend.compute_ship_cells(s.grid_row, s.grid_col, s.length, s.orientation)) #
                        backend.submit_placement() #
                        backend.update_game_state("WAITING_FOR_OPPONENT")

        # ------------------ WAITING FOR OTHER PLAYER STATE ------------------
        elif backend.GAME_STATE == "WAITING_FOR_OPPONENT":
            print(f"Player {backend.player_id} Locked: {backend.ships_locked}")
            print(f"All Ships Locked: {backend.all_ships_locked}")
            if backend.all_ships_locked:
                backend.update_game_state("RUNNING_GAME")

        # ------------------ RUNNING GAME STATE ------------------
        elif backend.GAME_STATE == "RUNNING_GAME":
            #TODO: Create Gameplay Loop
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for cell in all_cells:
                    if cell.rect.collidepoint(mouse_pos):
                        cell.handle_click()


    # ------------------ DRAWING ------------------
    if backend.GAME_STATE == "SELECT_SHIPS":
        if backend.player_id == player1_id:
            draw_ship_selection()
        if backend.player_id == player2_id:
            draw_waiting_for_player(player1_id, f"Player {player1_id} will select 1-5 ships")
    
    elif backend.GAME_STATE == "PLACE_SHIPS":
        draw_ship_placement()
        draw_coordinates(GRID_PADDING, GRID_PADDING)
        draw_control_buttons(mouse_pos)
        
    
    elif backend.GAME_STATE == "WAITING_FOR_OPPONENT":
        draw_waiting_for_player(opponent_id, f"Player {opponent_id} is still placing their ships")

    elif backend.GAME_STATE == "RUNNING_GAME":
        screen.fill(BG_COLOR)
        draw_coordinates(GRID_PADDING, top_grid_y)
        draw_coordinates(GRID_PADDING, bottom_grid_y)
        for cell in all_cells:
            cell.draw(screen, mouse_pos)
        
        # Draw backend ships on bottom grid
        draw_backend_ships()

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()