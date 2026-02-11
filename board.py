#This file is for creating the interactive battleship board

#This file will handle the backend of our battleship game

import pygame
import sys

import backend

# ------------------ CONFIG ------------------
GRID_SIZE = 10
CELL_SIZE = 40
GRID_PADDING = 40
WINDOW_WIDTH = GRID_SIZE * CELL_SIZE + 2 * GRID_PADDING
WINDOW_HEIGHT = (GRID_SIZE * CELL_SIZE * 2) + 3 * GRID_PADDING

BG_COLOR = (30, 30, 30)
GRID_COLOR = (200, 200, 200)
HOVER_COLOR = (100, 180, 255)

SHIP_COLOR = (180, 180, 180)
SHIP_PADDING = 20
SHIP_BLOCK_SIZE = CELL_SIZE

GAME_STATE = "SELECT_SHIPS"

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
        self.block_size = CELL_SIZE
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0

    def get_rects(self):
        rects = []
        for i in range(self.length):
            rects.append(
                pygame.Rect(
                    self.x,
                    self.y + i * self.block_size,
                    self.block_size,
                    self.block_size
                )
            )
        return rects

    def draw(self, surface):
        for rect in self.get_rects():
            pygame.draw.rect(surface, SHIP_COLOR, rect)
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
            self.dragging = False

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

    pygame.display.flip()

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

    pygame.display.flip()

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


# ------------------ MAIN LOOP ------------------
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ------------------ SHIP SELECTION STATE ------------------
        if GAME_STATE == "SELECT_SHIPS":
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

                    # You can send this to backend if needed
                    # backend.send_ship_count(ship_count)
                    create_ships(ship_count)

                    GAME_STATE = "PLACE_SHIPS"
        # ------------------ SHIP PLACING STATE ------------------
        elif GAME_STATE == "PLACE_SHIPS":
            for ship in ships:
                ship.handle_event(event)            
                

        # ------------------ GAME STATE ------------------
        elif GAME_STATE == "RUNNING_GAME":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for cell in all_cells:
                    if cell.rect.collidepoint(mouse_pos):
                        cell.handle_click()

    # ------------------ DRAWING ------------------

    if GAME_STATE == "SELECT_SHIPS":
        draw_ship_selection()
    
    elif GAME_STATE == "PLACE_SHIPS":
        draw_ship_placement()

    elif GAME_STATE == "RUNNING_GAME":
        screen.fill(BG_COLOR)
        for cell in all_cells:
            cell.draw(screen, mouse_pos)

        pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()