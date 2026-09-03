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

def path_targets_capture(gamemap): # Is our active movement path a run at a general or city worth committing to?
	if len(gamemap.path) < 2:
		return False

	target = gamemap.path[-1]
	if target.isSelf(): # Gathering to something we already hold - keep expanding
		return False

	return target.isGeneral or target.isCity

def move_outward(gamemap, path=[]):
	if path_targets_capture(gamemap): # Committed to a run at a general or city - don't peel army off to expand
		return (False, False)

	move_swamp = (False, False)
	hold_general = garrison_needed(gamemap) > 0 # Don't march the garrison back off our general

	for source in gamemap.tiles[gamemap.player_index]: # Check Each Owned Tile
		if hold_general and source.isGeneral:
			continue
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

######################### Move Gather To Nearest Holding #########################

def nearest_holding(gamemap, source): # Closest city or general we own
	nearest = None
	nearest_distance = 0

	holdings = [t for t in gamemap.cities if t.isSelf()]
	general = gamemap.generals[gamemap.player_index]
	if general != None:
		holdings.append(general)

	for tile in holdings:
		distance = source.distance_to(tile)
		if nearest == None or distance < nearest_distance:
			nearest = tile
			nearest_distance = distance

	return nearest

def move_gather_to_holding(gamemap):
	source = gamemap.find_largest_tile(excludeCities=True) # Field army only - leave cities and our general holding what they have
	if source == None or source.army < 2:
		return (False, False)

	dest = nearest_holding(gamemap, source)
	if dest == None or dest == source:
		return (False, False)

	return move_path(source.path_to(dest), gamemap)

######################### Move Defend General #########################

def _tiles_near_general(gamemap, general): # Tiles within threat range of our general
	for dx in range(-DEFEND_GENERAL_RADIUS, DEFEND_GENERAL_RADIUS + 1):
		for dy in range(-DEFEND_GENERAL_RADIUS, DEFEND_GENERAL_RADIUS + 1):
			if abs(dx) + abs(dy) > DEFEND_GENERAL_RADIUS:
				continue
			x = general.x + dx
			y = general.y + dy
			if gamemap.isValidPosition(x, y):
				yield gamemap.grid[y][x]

def general_threat(gamemap): # Largest single enemy stack near our general - an attack arrives as one travelling stack, not as every nearby tile at once
	general = gamemap.generals[gamemap.player_index]
	if general == None or not gamemap.generalKnownToEnemy: # They can only come for it if they know where it is
		return 0

	threat = 0
	for tile in _tiles_near_general(gamemap, general):
		if tile.isGeneral or tile.isCity: # Their garrison sits at home growing every turn - it isn't the force walking at us
			continue
		if tile.tile >= 0 and not tile.isSelf() and not tile.tile in gamemap.do_not_attack_players:
			if tile.army > threat:
				threat = tile.army

	return threat

def garrison_needed(gamemap): # Army our general must hold back to survive the visible threat
	threat = general_threat(gamemap)
	if threat == 0:
		return 0

	needed = threat + DEFEND_GENERAL_MARGIN
	cap = _total_army(gamemap) * DEFEND_GENERAL_MAX_SHARE # Never sink our whole economy into defense - keep army free to fight with
	if cap > 0 and needed > cap:
		return cap

	return needed

def _total_army(gamemap):
	if len(gamemap.scores) > gamemap.player_index:
		return gamemap.scores[gamemap.player_index]['total']
	return 0

def _retake_near_general(gamemap, general): # Push the intruders back out, sourcing from anywhere but the garrison
	source = gamemap.find_largest_tile() # Never returns the general, so the garrison stays put
	if source == None or source.army < 2:
		return (False, False)

	target = None
	for tile in _tiles_near_general(gamemap, general):
		if tile.tile >= 0 and not tile.isSelf() and tile.shouldAttack() and tile.army < source.army:
			if target == None or tile.distance_to(general) < target.distance_to(general): # Clear the closest intruder first
				target = tile

	if target == None:
		return (False, False)

	return move_path(source.path_to(target), gamemap)

def move_defend_general(gamemap):
	general = gamemap.generals[gamemap.player_index]
	if general == None:
		return (False, False)

	needed = garrison_needed(gamemap)
	if needed == 0: # Nothing visible is coming for us
		gamemap.defendingGeneral = False
		return (False, False)

	gamemap.defendingGeneral = True

	if general.army <= needed: # Garrison is short - top it up from elsewhere
		source = gamemap.find_largest_tile() # Excludes the general itself, so the rest of the army keeps doing normal work
		if source != None and source.army >= 2:
			return move_path(source.path_to(general), gamemap)
		return (False, False)

	return _retake_near_general(gamemap, general) # Garrison holds - go take our tiles back

######################### Move Path Forward #########################

def move_path(path, gamemap=None): # Pass gamemap to keep the move from spending our general's garrison
	if len(path) < 2:
		return (False, False)

	hold_general = gamemap != None and garrison_needed(gamemap) > 0

	source = path[0]
	target = path[-1]

	if target.tile == source.tile:
		return _move_path_largest(path, hold_general)

	move_capture = _move_path_capture(path, hold_general)

	if not target.isGeneral and move_capture[1] != target:
		return _move_path_largest(path, hold_general)

	return move_capture

def _holds_garrison(tile, hold_general):
	return hold_general and tile.isGeneral and tile.isSelf() # Our general, needed where it is

def _move_path_largest(path, hold_general=False):
	largest = None
	largest_index = 0
	for i, tile in enumerate(path):
		if tile == path[-1]:
			break
		if _holds_garrison(tile, hold_general):
			continue
		if tile.tile == path[0].tile and (largest == None or tile > largest):
			largest = tile
			largest_index = i

	if largest == None:
		return (False, False)

	dest = path[largest_index+1]
	return (largest, dest)


def _move_path_capture(path, hold_general=False):
	source = path[0]
	capture_army = 0
	for i, tile in reversed(list(enumerate(path))):
		if tile.tile == source.tile:
			capture_army += (tile.army - 1)
		else:
			capture_army -= tile.army

		if capture_army > 0 and i+1 < len(path) and path[i].army > 1 and not _holds_garrison(path[i], hold_general):
			return (path[i], path[i+1])

	return _move_path_largest(path, hold_general)

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
	includeGeneral = 0.5 if garrison_needed(gamemap) == 0 else False # Leave the garrison on our general alone
	source = gamemap.find_largest_tile(includeGeneral=includeGeneral)
	if source == None:
		return []
	target = source.nearest_target_tile()
	path = source.path_to(target)
	#logging.info("Proximity %s -> %s via %s" % (source, target, path))

	if not gamemap.canStepPath(path):
		path = path_gather(gamemap)
		#logging.info("Proximity FAILED, using path %s" % path)
	return path

def path_gather(gamemap, elsoDo=[]):
	includeGeneral = 0.5 if garrison_needed(gamemap) == 0 else False # Leave the garrison on our general alone
	target = gamemap.find_largest_tile()
	source = gamemap.find_largest_tile(notInPath=[target], includeGeneral=includeGeneral)
	if source and target and source != target:
		return source.path_to(target)
	return elsoDo

######################### Helpers #########################

def _shuffle(seq):
	shuffled = list(seq)
	random.shuffle(shuffled)
	return iter(shuffled)
