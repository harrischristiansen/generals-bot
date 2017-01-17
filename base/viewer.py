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
PLAYER_COLORS = [(255,0,0), (0,0,255), (0,128,0), (128,0,0), (0,128,128), (128,0,128), (0,70,0), (255,165,0), (30,250,30)]

# Table Properies
CELL_WIDTH = 20
CELL_HEIGHT = 20
CELL_MARGIN = 5

class GeneralsViewer(object):
	def __init__(self, name=None):
		self._name = name
		self._receivedUpdate = False

	def updateGrid(self, update):
		self._grid = update._tile_grid
		self._armies = update._army_grid
		self._cities = update._visible_cities
		self._generals = update._visible_generals
		self._turn = update.turn
		self._receivedUpdate = True
		if "path" in dir(update):
			self._path = [(path.x, path.y) for path in update.path]
		else:
			self._path = []
		if "collect_path" in dir(update):
			self._collect_path = [(path.x, path.y) for path in update.collect_path]
		else:
			self._collect_path = None

	def _initViewier(self):
		pygame.init()

		# Set Window Size
		window_height = len(self._grid) * (CELL_HEIGHT + CELL_MARGIN) + CELL_MARGIN + 25
		window_width = len(self._grid[0]) * (CELL_WIDTH + CELL_MARGIN) + CELL_MARGIN
		self._window_size = [window_width, window_height]
		self._screen = pygame.display.set_mode(self._window_size)

		window_title = "Generals IO Bot"
		if (self._name != None):
			window_title += " - " + str(self._name)
		pygame.display.set_caption(window_title)
		self._font = pygame.font.SysFont('Arial', CELL_HEIGHT-10)
		self._fontLrg = pygame.font.SysFont('Arial', CELL_HEIGHT)

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

		# Draw Score
		self._screen.blit(self._fontLrg.render("Turn: "+str(self._turn), True, WHITE), (10, self._window_size[1]-25))
		
	 
		# Draw Grid
		for row in range(len(self._grid)):
			for column in range(len(self._grid[row])):
				# Determine BG Color
				color = WHITE
				color_font = WHITE
				if self._grid[row][column] == -2: # Mountain
					color = BLACK
				elif self._grid[row][column] == -3: # Fog
					color = GRAY
				elif self._grid[row][column] == -4: # Obstacle
					color = GRAY_DARK
				elif self._grid[row][column] >= 0: # Player
					color = PLAYER_COLORS[self._grid[row][column]]
				else:
					color_font = BLACK

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
					textVal = str(self._armies[row][column])
					self._screen.blit(self._font.render(textVal, True, color_font), (pos_left+2, pos_top+2))

				# Draw Path
				if (self._path != None and (column,row) in self._path):
					self._screen.blit(self._fontLrg.render("*", True, color_font), (pos_left+3, pos_top+3))
				if (self._collect_path != None and (column,row) in self._collect_path):
					self._screen.blit(self._fontLrg.render("*", True, PLAYER_COLORS[8]), (pos_left+6, pos_top+6))
	 
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
