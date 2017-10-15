'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Bot_blob: Creates a blob of troops.
'''

import logging
import random
from base import bot_base, bot_moves

# Show all logging
logging.basicConfig(level=logging.DEBUG)

######################### Move Making #########################

_bot = None
_map = None
def make_move(currentBot, currentMap):
	global _bot, _map
	_bot = currentBot
	_map = currentMap

	if _map.turn % 3 == 0:
		if not move_outward():
			make_primary_move()
	else:
		make_primary_move()
	return

def place_move(source, dest):
	moveHalf = False
	if _map.turn > 150:
		if source in _map.generals:
			moveHalf = True
		elif source in _map.cities:
			moveHalf = random.choice([False, False, False, True])
			if _map.turn - source.turn_captured < 16:
				moveHalf = True
	
	_bot.place_move(source, dest, move_half=moveHalf)

def make_primary_move():
	if not move_toward():
		move_outward()

######################### Move Outward #########################

def move_outward():
	(source, dest) = bot_moves.move_outward(_map, _path)
	if source:
		place_move(source, dest)
		return True
	return False

######################### Move Toward #########################

_path = []
def move_toward():
	# Find path from largest tile to closest target
	source = _bot.find_largest_tile(includeGeneral=True)
	target = _bot.find_closest_target(source)
	path = source.find_path(target)

	army_total = 0
	for tile in path: # Verify can obtain every tile in path
		if tile.tile == _map.player_index:
			army_total += tile.army - 1
		elif tile.army + 1 > army_total: # Cannot obtain tile, draw path from largest city to largest tile
			source = _bot.find_city(includeGeneral=True)
			target = _bot.find_largest_tile(notInPath=[source])
			if source and target and source != target:
				path = source.find_path(target)
			break

	# Place Move
	_path = path
	_bot._path = path
	(move_from, move_to) = _bot.path_forward_moves(path)
	if move_from and move_to:
		place_move(move_from, move_to)
		return True

	return False

######################### Main #########################

# Start Game
import startup
if __name__ == '__main__':
	startup.startup(make_move, "PurdueBot-B2")
