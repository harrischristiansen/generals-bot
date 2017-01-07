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
BLACK = (0,0,0)
GRAY_DARK = (110,110,110)
GRAY = (160,160,160)
WHITE = (255,255,255)
PLAYER_COLORS = [(0,255,0), (255,0,0), (0,0,255), (255,255,10), (255,10,255), (170,0,170), (0,0,220), (5,190,190)]

# Table Properies
CELL_WIDTH = 20
CELL_HEIGHT = 20
CELL_MARGIN = 5

class GeneralsViewer(object):
	def __init__(self):
		self._receivedUpdate = False

	def updateGrid(self, grid, armies, cities, generals):
		self._grid = grid
		self._armies = armies
		self._cities = cities
		self._generals = generals
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
				# Determine BG Color
				color = WHITE
				if self._grid[row][column] == -2: # Mountain
					color = BLACK
				elif self._grid[row][column] == -3: # Fog
					color = GRAY
				elif self._grid[row][column] == -4: # Obstacle
					color = GRAY_DARK
				elif self._grid[row][column] >= 0: # Player
					color = PLAYER_COLORS[self._grid[row][column]]

				pos_left = (CELL_MARGIN + CELL_WIDTH) * column + CELL_MARGIN
				pos_top = (CELL_MARGIN + CELL_HEIGHT) * row + CELL_MARGIN
				if ((row,column) in self._cities or (row,column) in self._generals): # City
					# Draw Circle
					pos_left_circle = pos_left + (CELL_WIDTH/2)
					pos_top_circle = pos_top + (CELL_HEIGHT/2)
					pygame.draw.circle(self._screen, color, [pos_left_circle, pos_top_circle], CELL_WIDTH/2)
				else:
					# Draw Rect
					pygame.draw.rect(self._screen, color, [pos_left, pos_top, CELL_WIDTH, CELL_HEIGHT])

				# Draw Text Value
				if (self._grid[row][column] >= -2 and self._armies[row][column] != 0): # Don't draw on fog
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
	viewer.updateGrid(grid,grid,[],[])
	time.sleep(1)
	grid[1][8] = 2
	viewer.updateGrid(grid,grid,[],[])

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
