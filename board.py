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

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for cell in all_cells:
                if cell.rect.collidepoint(mouse_pos):
                    cell.handle_click()
                    # You could enqueue this info, call game logic, etc.

    screen.fill(BG_COLOR)

    for cell in all_cells:
        cell.draw(screen, mouse_pos)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()