'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Bot_blob: Creates a blob of troops.
'''

import logging
from base import bot_moves

# Show all logging
logging.basicConfig(level=logging.DEBUG)

######################### Move Making #########################

_bot = None
_map = None
def make_move(currentBot, currentMap):
	global _bot, _map
	_bot = currentBot
	_map = currentMap

	if move_priority():
		return

	if _map.turn % 3 == 0:
		if move_outward():
			return True
	if not move_toward():
		move_outward()
	return

def place_move(source, dest):
	_bot.place_move(source, dest, move_half=bot_moves.should_move_half(_map, source, dest))

######################### Move Priority #########################

def move_priority():
	(source, dest) = bot_moves.move_priority(_map)
	if source and dest:
		place_move(source, dest)
		return True
	return False

######################### Move Outward #########################

def move_outward():
	(source, dest) = bot_moves.move_outward(_map, _map.path)
	if source and dest:
		place_move(source, dest)
		return True
	return False

######################### Move Toward #########################

def move_toward():
	_map.path = bot_moves.path_proximity_target(_map)
	(move_from, move_to) = bot_moves.move_path(_map.path)
	if move_from and move_to:
		place_move(move_from, move_to)
		return True
	return False

######################### Main #########################

# Start Game
import startup
if __name__ == '__main__':
	startup.startup(make_move, "PurdueBot-B2")
