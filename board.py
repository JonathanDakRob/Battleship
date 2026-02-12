#This file is for creating the interactive battleship board

#This file will handle the backend of our battleship game

import pygame
import sys

import backend

# ------------------ CONFIG ------------------
import os
os.environ['SDL_VIDEO_CENTERED'] = '1' 

GRID_SIZE = 10
CELL_SIZE = 30       # Shrinks the squares so the window isn't too tall
GRID_PADDING = 30    
WINDOW_WIDTH = GRID_SIZE * CELL_SIZE + 2 * GRID_PADDING + 150 
WINDOW_HEIGHT = (GRID_SIZE * CELL_SIZE * 2) + 4 * GRID_PADDING 

BG_COLOR = (30, 30, 30)
GRID_COLOR = (200, 200, 200)
HOVER_COLOR = (100, 180, 255)

SHIP_COLOR = (180, 180, 180)
SHIP_PADDING = 20
SHIP_BLOCK_SIZE = CELL_SIZE


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
        
        #Data to be sent to the backend
        if self.grid_id == 0:
            backend.send_bomb(self.row, self.col)


        print(f"Clicked Grid {self.grid_id}, Row {self.row}, Col {self.col}")
        return (self.grid_id, self.row, self.col)

# ------------------ SHIP CLASS ------------------
class Ship:
    def __init__(self, length, x, y):
        self.length = length
        self.x = x
        self.y = y
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
            

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect in self.get_rects():
                if rect.collidepoint(event.pos):
                    self.dragging = True
                    self.offset_x = self.x - event.pos[0]
                    self.offset_y = self.y - event.pos[1]
                    break

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                
                col = round((self.x - GRID_PADDING) / CELL_SIZE)
                row = round((self.y - GRID_PADDING) / CELL_SIZE)

                self.grid_col = col
                self.grid_row = row

                if backend.can_place_ship(backend.compute_ship_cells(row, col, self.length, self.orientation)):
                    self.x = GRID_PADDING + col * CELL_SIZE
                    self.y = GRID_PADDING + row * CELL_SIZE
                    self.placed = True
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

    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 36)

    title_text = font.render("Select Number of Ships (1 - 5)", True, (255, 255, 255))
    instruction_text = small_font.render("Press a number key 1, 2, 3, 4, or 5", True, (200, 200, 200))

    screen.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, WINDOW_HEIGHT // 3))
    screen.blit(instruction_text, (WINDOW_WIDTH // 2 - instruction_text.get_width() // 2, WINDOW_HEIGHT // 2))

    #pygame.display.flip()

def draw_backend_ships():
    """
    Draw ships stored in backend.ships onto the bottom grid.
    Assumes backend.ships is a list of lists of (row, col) tuples.
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
    ships.clear()

    ships_start_x = GRID_PADDING + GRID_SIZE * CELL_SIZE + SHIP_PADDING
    ships_start_y = GRID_PADDING

    for ship_length in range(1, num_ships + 1):
        ship = Ship(ship_length, ships_start_x, ships_start_y)
        ships.append(ship)

        ships_start_y += (ship_length * CELL_SIZE) + SHIP_PADDING

def draw_ship_placement():
    screen.fill(BG_COLOR)

    grid_start_x = GRID_PADDING
    grid_start_y = GRID_PADDING

    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(
                grid_start_x + col * CELL_SIZE,
                grid_start_y + row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )
            pygame.draw.rect(screen, GRID_COLOR, rect, 2)

    for ship in ships:
        ship.draw(screen)

    button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 70, WINDOW_HEIGHT - 60, 140, 40)
    pygame.draw.rect(screen, (50, 200, 50), button_rect)
    
    font = pygame.font.SysFont(None, 24)
    text = font.render("LOCK SHIPS", True, (255, 255, 255))
    screen.blit(text, (button_rect.centerx - text.get_width() // 2, button_rect.centery - text.get_height() // 2))

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

top_grid_y = GRID_PADDING
bottom_grid_y = GRID_PADDING * 2 + GRID_SIZE * CELL_SIZE

top_grid = create_grid(0, GRID_PADDING, top_grid_y)
bottom_grid = create_grid(1, GRID_PADDING, bottom_grid_y)

all_cells = top_grid + bottom_grid

# ------------------ DRAW LOCK BUTTON ------------------
def draw_lock_button(mouse_pos):
    # Place button at the bottom center
    button_rect = pygame.Rect(WINDOW_WIDTH // 2 - 70, WINDOW_HEIGHT - 60, 140, 40)
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


# ------------------ MAIN LOOP ------------------
running = True

while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ------------------ SHIP SELECTION STATE ------------------
        if backend.GAME_STATE == "SELECT_SHIPS":
            if backend.player_id == 0:
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
            elif backend.player_id == 1:
                print("Waiting for player 0 to choose ship count")
                while backend.GAME_STATE == "SELECT_SHIPS":
                    clock.tick(10)
                    ship_count = backend.ship_count
                    print(f"Player 0 selected {ship_count} ships")
                    create_ships(ship_count)

        # ------------------ SHIP PLACING STATE ------------------
        elif backend.GAME_STATE == "PLACE_SHIPS":
            for ship in ships:
                ship.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                lock_rect = pygame.Rect(WINDOW_WIDTH // 2 - 70, WINDOW_HEIGHT - 60, 140, 40)
                if lock_rect.collidepoint(event.pos):
                    print("Ships Locked! Sending to server...")
                    if lock_rect.collidepoint(event.pos):

                        all_valid = True

                        for ship in ships:
                            if not ship.placed:
                                all_valid = False
                                break

                        if all_valid:
                            for ship in ships:
                                backend.place_ship(
                                    ship.grid_row,
                                    ship.grid_col,
                                    ship.length,
                                    ship.orientation
                                )

                    backend.submit_placement() # Calls your existing backend function
                    backend.GAME_STATE = "RUNNING_GAME" # Moves to the shooting phase        

        # ------------------ RUNNING GAME STATE ------------------
        elif backend.GAME_STATE == "RUNNING_GAME":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for cell in all_cells:
                    if cell.rect.collidepoint(mouse_pos):
                        cell.handle_click()

    # ------------------ DRAWING ------------------
    if backend.GAME_STATE == "SELECT_SHIPS":
        draw_ship_selection()
    
    elif backend.GAME_STATE == "PLACE_SHIPS":
        draw_ship_placement()
        draw_lock_button(mouse_pos)

    elif backend.GAME_STATE == "RUNNING_GAME":
        screen.fill(BG_COLOR)
        for cell in all_cells:
            cell.draw(screen, mouse_pos)
        
        # Draw backend ships on bottom grid
        draw_backend_ships()

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()