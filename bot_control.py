'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Bot_control: Create a human controlled bot
'''

import logging
from base import bot_moves

# Set logging level
logging.basicConfig(level=logging.INFO)

######################### Move Making #########################

nextMove = []
last_manual = 0

_bot = None
_map = None
def make_move(currentBot, currentMap):
	global _bot, _map, last_manual
	_bot = currentBot
	_map = currentMap

	if not move_priority():
		if not move_manual():
			last_manual += 1
			if not move_outward():
				if last_manual > 5:
					move_toward()
		else:
			last_manual = 0
	return

def place_move(source, dest):
	_bot.place_move(source, dest, move_half=bot_moves.should_move_half(_map, source, dest))

######################### Manual Control #########################

def add_next_move(source_xy, dest_xy):
	if _map == None:
		return False

	source = _map.grid[source_xy[1]][source_xy[0]]
	dest = _map.grid[dest_xy[1]][dest_xy[0]]

	move = (source, dest)
	nextMove.append(move)

def move_manual():
	global nextMove, last_manual
	if len(nextMove) == 0:
		return False

	(source, dest) = nextMove.pop(0)
	if source and dest:
		place_move(source, dest)
		return True
	return False

######################### Move Priority #########################

def move_priority():
	(source, dest) = bot_moves.move_priority(_map)
	if source and dest:
		place_move(source, dest)
		return True
	return False

######################### Move Outward #########################

def move_outward():
	(source, dest) = bot_moves.move_outward(_map)
	if source and dest:
		place_move(source, dest)
		return True
	return False

######################### Move Toward #########################

def move_toward():
	path = bot_moves.path_proximity_target(_map)
	(move_from, move_to) = bot_moves.move_path(path)
	if move_from and move_to:
		place_move(move_from, move_to)
		return True
	return False

######################### Main #########################

# Start Game
import startup
if __name__ == '__main__':
	startup.startup(make_move, moveEvent=add_next_move, botName="PurdueBot-H")
