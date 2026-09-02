'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals Bot: Common Move Logic
'''
import logging
import random

from base import bot_base
from .client.constants import *

######################### Move Priority Capture #########################

def move_priority(gamemap):
	priority_move = (False, False)
	generals_and_cities = [t for t in gamemap.generals if t is not None]
	generals_and_cities.extend(gamemap.cities)

	for tile in generals_and_cities:
		if tile.isCity and tile.isEmpty() and tile.visibleToEnemy(): # Don't reveal ourselves capturing a neutral city an enemy can see
			continue
		if not tile.shouldNotAttack():
			for neighbor in tile.neighbors():
				if neighbor.isSelf() and neighbor.army > max(1, tile.army + 1):
					if priority_move[0] == False or priority_move[0].army < neighbor.army:
						priority_move = (neighbor, tile)
			if priority_move[0] != False:
				#logging.info("Priority Move from %s -> %s" % (priority_move[0], priority_move[1])) # TODO: Note, priority moves are repeatedly sent, indiating move making is sending repeated moves
				break
	return priority_move

######################### Move Outward #########################

def move_outward(gamemap, path=[]):
	move_swamp = (False, False)

	for source in gamemap.tiles[gamemap.player_index]: # Check Each Owned Tile
		if source.army >= 2 and source not in path and source not in gamemap.path: # Find One With Armies, but don't displace a tile the active movement path needs
			target = source.neighbor_to_attack(path)
			if target:
				if not target.isSwamp:
					return (source, target)
				move_swamp = (source, target)

	return move_swamp

######################### Move Collect To General #########################

def move_collect_to_general(gamemap):
	general = gamemap.generals[gamemap.player_index]
	if general == None:
		return (False, False)

	source = gamemap.find_largest_tile()
	if source == None or source.army < 2:
		return (False, False)

	return move_path(source.path_to(general))

######################### Move Defend General #########################

def general_threat(gamemap): # Estimated enemy army that could converge on our general
	general = gamemap.generals[gamemap.player_index]
	if general == None or not gamemap.generalKnownToEnemy: # They can only come for it if they know where it is
		return 0

	threat = 0
	for dx in range(-DEFEND_GENERAL_RADIUS, DEFEND_GENERAL_RADIUS + 1):
		for dy in range(-DEFEND_GENERAL_RADIUS, DEFEND_GENERAL_RADIUS + 1):
			if abs(dx) + abs(dy) > DEFEND_GENERAL_RADIUS:
				continue
			x = general.x + dx
			y = general.y + dy
			if not gamemap.isValidPosition(x, y):
				continue
			tile = gamemap.grid[y][x]
			if tile.tile >= 0 and not tile.isSelf() and not tile.tile in gamemap.do_not_attack_players:
				threat += tile.army

	return threat

def move_defend_general(gamemap):
	general = gamemap.generals[gamemap.player_index]
	if general == None:
		return (False, False)

	threat = general_threat(gamemap)
	if threat == 0 or general.army > threat + DEFEND_GENERAL_MARGIN: # Garrison already covers what they could throw at us
		gamemap.defendingGeneral = False
		return (False, False)

	gamemap.defendingGeneral = True

	source = gamemap.find_largest_tile() # Excludes the general itself, so the rest of the army keeps doing normal work
	if source == None or source.army < 2:
		return (False, False)

	return move_path(source.path_to(general))

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

		if capture_army > 0 and i+1 < len(path) and path[i].army > 1:
			return (path[i], path[i+1])

	return _move_path_largest(path)

######################### Move Path Forward #########################

def should_move_half(gamemap, source, dest=None):
	if dest != None and dest.isCity:
		return False

	if gamemap.turn > 250:
		if source.isGeneral:
			return random.choice([True, True, True, False])
		elif source.isCity:
			if gamemap.turn - source.turn_captured < 16:
				return True
			return random.choice([False, False, False, True])
	return False

######################### Proximity Targeting - Pathfinding #########################

def path_proximity_target(gamemap):
	# Find path from largest tile to closest target
	source = gamemap.find_largest_tile(includeGeneral=0.5)
	target = source.nearest_target_tile()
	path = source.path_to(target)
	#logging.info("Proximity %s -> %s via %s" % (source, target, path))

	if not gamemap.canStepPath(path):
		path = path_gather(gamemap)
		#logging.info("Proximity FAILED, using path %s" % path)
	return path

def path_gather(gamemap, elsoDo=[]):
	target = gamemap.find_largest_tile()
	source = gamemap.find_largest_tile(notInPath=[target], includeGeneral=0.5)
	if source and target and source != target:
		return source.path_to(target)
	return elsoDo

######################### Helpers #########################

def _shuffle(seq):
	shuffled = list(seq)
	random.shuffle(shuffled)
	return iter(shuffled)
