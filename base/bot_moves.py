'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals Bot: Common Move Logic
'''
import logging
import random

from base import bot_base
from .client.constants import *

######################### Move Outward #########################

def move_outward(gamemap, path=[]):
	for source in gamemap.tiles[gamemap.player_index]: # Check Each Owned Tile
		if source.army >= 2 and source not in path: # Find One With Armies
			for neighbor in bot_base._shuffle(source.neighbors()):
				if ((not neighbor.isAlly() and source.army > neighbor.army + 1) or neighbor in path) and not neighbor.isSwamp: # Capture Somewhere New
					return (source, neighbor)
	return (False, False)

######################### Move Path Forward #########################

def move_path(path):
	if len(path) < 2:
		return (False, False)

	source = path[0]
	target = path[-1]

	if target.tile == source.tile:
		return _move_path_largest(path)

	move_capture = _move_path_capture(path)

	if not target.isGeneral and move_capture[1] != target:
		return _move_path_largest(path)

	return move_capture

def _move_path_largest(path):
	largest = path[0]
	largest_index = 0
	for i, tile in enumerate(path):
		if tile == path[-1]:
			break
		if tile.tile == path[0].tile and tile > largest:
			largest = tile
			largest_index = i

	dest = path[largest_index+1]
	return (largest, dest)
	

def _move_path_capture(path):
	source = path[0]
	capture_army = 0
	for i, tile in reversed(list(enumerate(path))):
		if tile.tile == source.tile:
			capture_army += (tile.army - 1)
		else:
			capture_army -= tile.army

		if capture_army > 0 and i+1 < len(path):
			return (path[i], path[i+1])

	return (False, False)

######################### Move Path Forward #########################

def should_move_half(gamemap, source):
	if gamemap.turn > 250:
		if source in gamemap.generals:
			return True
		elif source in gamemap.cities:
			moveHalf = random.choice([False, False, False, True])
			if gamemap.turn - source.turn_captured < 16:
				return True
	return False

######################### Proximity Targeting - Pathfinding #########################

def path_proximity_target(gamemap):
	# Find path from largest tile to closest target
	source = gamemap.find_largest_tile(includeGeneral=True)
	target = source.nearest_target_tile()
	path = source.path_to(target)
	#logging.debug("Proximity %s -> %s via %s" % (source, target, path))

	if not gamemap.canStepPath(path):
		path = path_gather(gamemap)
		#logging.debug("Proximity FAILED, using path %s" % path)
	return path

def path_gather(gamemap, elsoDo=[]):
	source = gamemap.find_city(includeGeneral=True)
	target = gamemap.find_largest_tile(notInPath=[source])
	if source and target and source != target:
		return source.path_to(target)
	return elsoDo