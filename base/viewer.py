'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Game Viewer
'''

import logging
import pygame
import threading
import time

from .client.constants import *

# Color Definitions
BLACK = (0,0,0)
GRAY_DARK = (110,110,110)
GRAY = (160,160,160)
WHITE = (255,255,255)
GOLD = (217, 163, 0)
PLAYER_COLORS = [(255,0,0), (0,0,255), (0,128,0), (128,0,128), (0,128,128), (0,70,0), (128,0,0), (255,165,0), (30,250,30)]

# Table Properies
CELL_WIDTH = 20
CELL_HEIGHT = 20
CELL_MARGIN = 5
SCORES_ROW_HEIGHT = 28
ACTIONBAR_ROW_HEIGHT = 25
TOGGLE_GRID_BTN_WIDTH = 75
TOGGLE_EXIT_BTN_WIDTH = 65
ABOVE_GRID_HEIGHT = ACTIONBAR_ROW_HEIGHT

class GeneralsViewer(object):
	def __init__(self, name=None, moveEvent=None):
		self._runPygame = True
		self._name = name
		self._moveEvent = moveEvent					# self._moveEvent([source_x, source_y], [target_x, target_y])
		self._receivedUpdate = False
		self._showGrid = True
		self._clicked = None

	def mainViewerLoop(self):
		while not self._receivedUpdate: # Wait for first update
			time.sleep(0.5)

		self._initViewier()

		while self._runPygame:
			for event in pygame.event.get(): # User did something
				if event.type == pygame.QUIT: # User clicked quit
					self._runPygame = False # Flag done
				elif event.type == pygame.MOUSEBUTTONDOWN: # Mouse Click
					self._handleClick(pygame.mouse.get_pos())
				elif event.type == pygame.KEYDOWN: # Key Press Down
					self._handleKeypress(event.key)

			if self._receivedUpdate:
				self._drawViewer()
				self._receivedUpdate = False

			time.sleep(0.2)

		pygame.quit() # Done. Quit pygame.

	''' ======================== Call to update viewer with new map state ======================== '''

	def updateGrid(self, update):
		updateDir = dir(update)
		self._map = update
		self._scores = sorted(update.scores, key=lambda general: general['total'], reverse=True) # Sort Scores
		self._receivedUpdate = True
		if "bottomText" in updateDir:
			self._bottomText = update.bottomText
		if "path" in updateDir:
			self._path = [(path.x, path.y) for path in update.path]
		else:
			self._path = []
		if "collect_path" in updateDir:
			self._collect_path = [(path.x, path.y) for path in update.collect_path]
		else:
			self._collect_path = None

		return self

	''' ======================== PRIVATE METHODS - Viewer Init - PRIVATE METHODS ======================== '''

	def _initViewier(self):
		pygame.init()

		# Set Window Size
		self._grid_height = self._map.rows * (CELL_HEIGHT + CELL_MARGIN) + CELL_MARGIN
		window_height = ACTIONBAR_ROW_HEIGHT + self._grid_height + SCORES_ROW_HEIGHT
		window_width = self._map.cols * (CELL_WIDTH + CELL_MARGIN) + CELL_MARGIN
		self._window_size = [window_width, window_height]
		self._screen = pygame.display.set_mode(self._window_size)

		window_title = "Generals IO Bot"
		if self._name != None:
			window_title += " - " + str(self._name)
		pygame.display.set_caption(window_title)
		self._font = pygame.font.SysFont('Arial', CELL_HEIGHT-10)
		self._fontLrg = pygame.font.SysFont('Arial', CELL_HEIGHT)
		self._bottomText = ""

		self._clock = pygame.time.Clock()

	''' ======================== Handle Clicks ======================== '''

	def _handleClick(self, pos):
		if pos[1] < ABOVE_GRID_HEIGHT:
			if pos[0] < TOGGLE_GRID_BTN_WIDTH: # Toggle Grid
				self._toggleGrid()
			elif pos[0] < TOGGLE_GRID_BTN_WIDTH+TOGGLE_EXIT_BTN_WIDTH: # Toggle Exit on Game Over
				self._map.exit_on_game_over = not self._map.exit_on_game_over
			self._receivedUpdate = True
		elif self._showGrid and pos[1] > ABOVE_GRID_HEIGHT and pos[1] < (self._window_size[1] - SCORES_ROW_HEIGHT): # Click inside Grid
			column = pos[0] // (CELL_WIDTH + CELL_MARGIN)
			row = (pos[1] - ABOVE_GRID_HEIGHT) // (CELL_HEIGHT + CELL_MARGIN)
			self._clicked = (column, row)
			logging.debug("Click %s, Grid Coordinates: %s" % (pos, self._clicked))

	def _toggleGrid(self):
		self._showGrid = not self._showGrid
		window_height = ACTIONBAR_ROW_HEIGHT + SCORES_ROW_HEIGHT
		if self._showGrid:
			window_height += self._grid_height
		self._window_size[1] = window_height
		self._screen = pygame.display.set_mode(self._window_size)

	''' ======================== Handle Keypresses ======================== '''

	def _handleKeypress(self, key):
		if self._clicked == None or self._moveEvent == None:
			return False
		column = self._clicked[0]
		row = self._clicked[1]

		target = None
		if key == pygame.K_LEFT:
			if column > 0:
				target = (column-1, row)
		elif key == pygame.K_RIGHT:
			if column < self._map.cols - 1:
				target = (column+1, row)
		elif key == pygame.K_UP:
			if row > 0:
				target = (column, row-1)
		elif key == pygame.K_DOWN:
			if row < self._map.rows - 1:
				target = (column, row+1)

		if target != None:
			self._moveEvent(self._clicked, target)
			self._clicked = target

	''' ======================== Viewer Drawing ======================== '''

	def _drawViewer(self):
		self._screen.fill(BLACK) # Set BG Color
		self._drawActionbar()
		if self._showGrid:
			self._drawGrid()
		self._drawScores()

		self._clock.tick(60) # Limit to 60 FPS
		pygame.display.flip() # update screen with new drawing

	def _drawActionbar(self):
		# Toggle Grid Button
		pygame.draw.rect(self._screen, (0,80,0), [0, 0, TOGGLE_GRID_BTN_WIDTH, ACTIONBAR_ROW_HEIGHT])
		self._screen.blit(self._font.render("Toggle Grid", True, WHITE), (10, 5))

		# Toggle Exit on Game Over Button
		pygame.draw.rect(self._screen, (0,100,0) if self._map.exit_on_game_over else (90,0,0), [TOGGLE_GRID_BTN_WIDTH, 0, TOGGLE_EXIT_BTN_WIDTH, ACTIONBAR_ROW_HEIGHT])
		self._screen.blit(self._font.render("Auto Quit", True, WHITE), (TOGGLE_GRID_BTN_WIDTH+10, 5))

		# Info Text
		self._screen.blit(self._fontLrg.render("Turn: %d" % self._map.turn, True, WHITE), (self._window_size[0]-200, 5))
		self._screen.blit(self._font.render("%s" % self._bottomText, True, WHITE), (self._window_size[0]-90, 12))

	def _drawScores(self):
		pos_top = self._window_size[1]-SCORES_ROW_HEIGHT
		score_width = self._window_size[0] / len(self._scores)
		for i, score in enumerate(self._scores):
			score_color = PLAYER_COLORS[int(score['i'])]
			if score['dead'] == True:
				score_color = GRAY_DARK
			pygame.draw.rect(self._screen, score_color, [score_width*i, pos_top, score_width, SCORES_ROW_HEIGHT])
			self._screen.blit(self._font.render(self._map.usernames[int(score['i'])], True, WHITE), (score_width*i+3, pos_top+1))
			self._screen.blit(self._font.render(str(score['total'])+" on "+str(score['tiles']), True, WHITE), (score_width*i+3, pos_top+1+self._font.get_height()))

	def _drawGrid(self):
		for row in range(self._map.rows):
			for column in range(self._map.cols):
				tile = self._map.grid[row][column]
				# Determine BG Color
				color = WHITE
				color_font = WHITE
				if tile.tile == TILE_MOUNTAIN: # Mountain
					color = BLACK
				elif tile.tile == TILE_FOG: # Fog
					color = GRAY
				elif tile.tile == TILE_OBSTACLE: # Obstacle
					color = GRAY_DARK
				elif tile.tile >= 0: # Player
					color = PLAYER_COLORS[tile.tile]
				else:
					color_font = BLACK

				pos_left = (CELL_MARGIN + CELL_WIDTH) * column + CELL_MARGIN
				pos_top = (CELL_MARGIN + CELL_HEIGHT) * row + CELL_MARGIN + ABOVE_GRID_HEIGHT
				if tile.isCity or tile.isGeneral: # City/General
					# Draw Circle
					pos_left_circle = int(pos_left + (CELL_WIDTH/2))
					pos_top_circle = int(pos_top + (CELL_HEIGHT/2))
					if tile in self._map.generals:
						pygame.draw.rect(self._screen, GOLD, [pos_left, pos_top, CELL_WIDTH, CELL_HEIGHT])
					pygame.draw.circle(self._screen, color, [pos_left_circle, pos_top_circle], int(CELL_WIDTH/2))
				else:
					# Draw Rect
					pygame.draw.rect(self._screen, color, [pos_left, pos_top, CELL_WIDTH, CELL_HEIGHT])

				# Draw Text Value
				if tile.army != 0: # Don't draw on empty tiles
					textVal = str(tile.army)
					self._screen.blit(self._font.render(textVal, True, color_font), (pos_left, pos_top+2))

				# Draw Swamps
				if tile.isSwamp:
					self._screen.blit(self._font.render("±", True, color_font), (pos_left+9, pos_top+7))

				# Draw Path
				if self._path != None and (column,row) in self._path:
					self._screen.blit(self._fontLrg.render("*", True, color_font), (pos_left+5, pos_top-3))
				if self._collect_path != None and (column,row) in self._collect_path:
					self._screen.blit(self._fontLrg.render("*", True, PLAYER_COLORS[8]), (pos_left+6, pos_top+6))
