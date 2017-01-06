'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Game Viewer
'''

import pygame
import threading
import time

# Color Definitions
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Table Properies
CELL_WIDTH = 20
CELL_HEIGHT = 20
CELL_MARGIN = 5

class GeneralsViewer(object):
	def __init__(self):
		self._receivedUpdate = False

	def updateGrid(self, grid, armies):
		self._grid = grid
		self._armies = armies
		self._receivedUpdate = True

	def _initViewier(self):
		pygame.init()

		# Set Window Size
		window_height = len(self._grid) * (CELL_HEIGHT + CELL_MARGIN) + CELL_MARGIN
		window_width = len(self._grid[0]) * (CELL_WIDTH + CELL_MARGIN) + CELL_MARGIN
		self._window_size = [window_width, window_height]
		self._screen = pygame.display.set_mode(self._window_size)

		pygame.display.set_caption("Generals IO Bot")
		self._font = pygame.font.SysFont('Arial', CELL_HEIGHT-10)

		self._clock = pygame.time.Clock()

	def mainViewerLoop(self):
		while not self._receivedUpdate: # Wait for first update
			time.sleep(0.5)

		self._initViewier()

		done = False
		while not done:
			for event in pygame.event.get(): # User did something
				if event.type == pygame.QUIT: # User clicked quit
					done = True # Flag done
				elif event.type == pygame.MOUSEBUTTONDOWN: # Mouse Click
					pos = pygame.mouse.get_pos()
					
					# Convert screen to grid coordinates
					column = pos[0] // (CELL_WIDTH + CELL_MARGIN)
					row = pos[1] // (CELL_HEIGHT + CELL_MARGIN)
					
					print("Click ", pos, "Grid coordinates: ", row, column)

			if (self._receivedUpdate):
				self._drawGrid()
				self._receivedUpdate = False

			time.sleep(0.2)

		pygame.quit() # Done. Quit pygame.

	def _drawGrid(self):
		self._screen.fill(BLACK) # Set BG Color
	 
		# Draw Grid
		for row in range(len(self._grid)):
			for column in range(len(self._grid[row])):
				# Determine Color
				color = WHITE
				if self._grid[row][column] == 1:
					color = GREEN
				elif self._grid[row][column] > 1:
					color = RED

				# Draw Rect
				pos_left = (CELL_MARGIN + CELL_WIDTH) * column + CELL_MARGIN
				pos_top = (CELL_MARGIN + CELL_HEIGHT) * row + CELL_MARGIN
				pygame.draw.rect(self._screen, color, [pos_left, pos_top, CELL_WIDTH, CELL_HEIGHT])

				# Draw Value
				self._screen.blit(self._font.render(str(self._armies[row][column]), True, BLACK), (pos_left+2, pos_top+2))
	 
		# Limit to 60 frames per second
		self._clock.tick(60)
 
		# Go ahead and update the screen with what we've drawn.
		pygame.display.flip()

'''def _create_thread(f):
	t = threading.Thread(target=f)
	#t.daemon = True
	t.start()

def _fakeUpdates():
	viewer.updateGrid(grid,grid)
	time.sleep(1)
	grid[1][8] = 2
	viewer.updateGrid(grid,grid)

grid = []
for row in range(10):
	grid.append([])
	for column in range(10):
		grid[row].append(0)  # Append a cell
 
grid[1][5] = 1
grid[1][7] = 2

viewer = GeneralsViewer()
_create_thread(_fakeUpdates)
viewer.mainViewerLoop()'''
