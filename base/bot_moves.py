'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals Bot: Common Move Logic
'''
import logging
import random

from base import bot_base
from .client.constants import *

def _config(gamemap, config=None): # Methods take an explicit config, else use the map's
	return config if config != None else gamemap.config

######################### Move Priority Capture #########################

def move_priority(gamemap, config=None):
	cfg = _config(gamemap, config)
	priority_move = (False, False)
	generals_and_cities = [t for t in gamemap.generals if t is not None]
	generals_and_cities.extend(gamemap.cities)

	for tile in generals_and_cities:
		if cfg.stealth_neutral_cities and tile.isCity and tile.isEmpty() and tile.visibleToEnemy(): # Don't reveal ourselves capturing a neutral city an enemy can see
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

def path_targets_capture(gamemap, config=None): # Is our active movement path a run at a general or city worth committing to?
	if not _config(gamemap, config).commit_to_capture:
		return False
	if len(gamemap.path) < 2:
		return False

	target = gamemap.path[-1]
	if target.isSelf(): # Gathering to something we already hold - keep expanding
		return False

	return target.isGeneral or target.isCity

def move_outward(gamemap, path=[], config=None):
	cfg = _config(gamemap, config)
	if path_targets_capture(gamemap, cfg): # Committed to a run at a general or city - don't peel army off to expand
		return (False, False)

	move_swamp = (False, False)
	hold_general = garrison_needed(gamemap, cfg) > 0 # Don't march the garrison back off our general
	active_path = gamemap.path if cfg.hold_active_path else [] # Legacy freely displaced tiles the path needed

	for source in gamemap.tiles[gamemap.player_index]: # Check Each Owned Tile
		if hold_general and source.isGeneral:
			continue
		if source.army >= 2 and source not in path and source not in active_path: # Find One With Armies, but don't displace a tile the active movement path needs
			target = source.neighbor_to_attack(path)
			if target:
				if not target.isSwamp:
					return (source, target)
				move_swamp = (source, target)

	return move_swamp

######################### Gather Path Selection #########################

def _gather_candidates(gamemap, excludeCities=False, includeGeneral=False, exclude=[], config=None):
	cfg = _config(gamemap, config)
	candidates = []
	for tile in gamemap.tiles[gamemap.player_index]:
		if tile.army < 2 or tile in exclude:
			continue
		if tile.isGeneral and not includeGeneral:
			continue
		if excludeCities and tile.isCity:
			continue
		candidates.append(tile)

	candidates.sort(key=lambda tile: tile.army, reverse=True)
	return candidates[:cfg.gather_candidates]

def _gather_score(path, dest, urgency=1.0, delay_factor=GATHER_DELAY_FACTOR): # Army this path delivers, discounted by how long it takes to arrive
	gathered = 0
	for tile in path:
		if tile is dest: # Already home - it isn't collected by the trip
			continue
		if tile.isSelf():
			gathered += tile.army - 1

	# Discounting (rather than subtracting a flat per-move cost) makes the delay cost scale with the
	# army being delayed: detouring to add 7 is worth it on a stack of 50, but not on a stack of 500.
	moves = len(path) - 1
	return gathered / (1.0 + moves * delay_factor * urgency)

def move_gather_step(path, gamemap=None, config=None): # Step the far end of the chain inward, so each tile absorbs the one behind it
	if len(path) < 2:
		return (False, False)

	source = path[0]
	if source.army < 2:
		return (False, False)
	if gamemap != None and _holds_garrison(source, garrison_needed(gamemap, config) > 0):
		return (False, False)

	return (source, path[1])

def gather_urgency(gamemap, config=None): # Army in transit is worth much less when something is coming for our general
	cfg = _config(gamemap, config)
	if garrison_needed(gamemap, cfg) > 0:
		return cfg.gather_urgent_multiplier
	return 1.0

def best_gather_path(gamemap, candidates, dest_for, config=None): # Pick the source whose route sweeps up the most army on the way in
	cfg = _config(gamemap, config)
	best_path = None
	best_score = None
	urgency = gather_urgency(gamemap, cfg)

	for source in candidates:
		dest = dest_for(source)
		if dest == None or dest is source:
			continue

		path = source.path_to(dest)
		if len(path) < 2:
			continue

		score = _gather_score(path, dest, urgency, cfg.gather_delay_factor)
		if best_score == None or score > best_score:
			best_score = score
			best_path = path

	return best_path

######################### Move Collect To General #########################

def move_collect_to_general(gamemap, config=None):
	cfg = _config(gamemap, config)
	general = gamemap.generals[gamemap.player_index]
	if general == None:
		return (False, False)

	if not cfg.smart_gather: # Legacy: always source the single largest tile
		source = gamemap.find_largest_tile()
		if source == None or source.army < 2:
			return (False, False)
		return move_path(source.path_to(general), config=cfg)

	path = best_gather_path(gamemap, _gather_candidates(gamemap, config=cfg), lambda source: general, cfg)
	if path == None:
		return (False, False)

	return move_gather_step(path, config=cfg)

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

def move_gather_to_holding(gamemap, config=None):
	cfg = _config(gamemap, config)
	candidates = _gather_candidates(gamemap, excludeCities=True, config=cfg) # Field army only - leave cities and our general holding what they have
	if not cfg.smart_gather: # Legacy-style: largest field tile to its nearest holding
		source = gamemap.find_largest_tile(excludeCities=True)
		if source == None or source.army < 2:
			return (False, False)
		dest = nearest_holding(gamemap, source)
		if dest == None or dest is source:
			return (False, False)
		return move_path(source.path_to(dest), gamemap, cfg)

	path = best_gather_path(gamemap, candidates, lambda source: nearest_holding(gamemap, source), cfg)
	if path == None:
		return (False, False)

	return move_gather_step(path, gamemap, cfg)

######################### Move Defend General #########################

def _tiles_near_general(gamemap, general, radius=DEFEND_GENERAL_RADIUS): # Tiles within threat range of our general
	for dx in range(-radius, radius + 1):
		for dy in range(-radius, radius + 1):
			if abs(dx) + abs(dy) > radius:
				continue
			x = general.x + dx
			y = general.y + dy
			if gamemap.isValidPosition(x, y):
				yield gamemap.grid[y][x]

def general_threat_info(gamemap, config=None): # (largest enemy stack near our general, how many moves away it is)
	cfg = _config(gamemap, config)
	general = gamemap.generals[gamemap.player_index]
	if not cfg.defend_general: # Legacy did not defend the general at all
		return (0, None)
	if general == None or not gamemap.generalKnownToEnemy: # They can only come for it if they know where it is
		return (0, None)

	threat = 0
	distance = None
	for tile in _tiles_near_general(gamemap, general, cfg.defend_general_radius):
		if tile.isGeneral or tile.isCity: # Their garrison sits at home growing every turn - it isn't the force walking at us
			continue
		if tile.tile >= 0 and not tile.isSelf() and not tile.tile in gamemap.do_not_attack_players:
			if tile.army > threat:
				threat = tile.army
				distance = tile.distance_to(general)

	return (threat, distance)

def general_threat(gamemap, config=None): # Largest single enemy stack near our general - an attack arrives as one travelling stack, not as every nearby tile at once
	return general_threat_info(gamemap, config)[0]

def garrison_needed(gamemap, config=None): # Army our general must hold back to survive the visible threat
	cfg = _config(gamemap, config)
	threat = general_threat(gamemap, cfg)
	if threat == 0:
		return 0

	needed = threat + cfg.defend_general_margin
	cap = _total_army(gamemap) * cfg.defend_general_max_share # Never sink our whole economy into defense - keep army free to fight with
	if cap > 0 and needed > cap:
		return cap

	return needed

def _total_army(gamemap):
	if len(gamemap.scores) > gamemap.player_index:
		return gamemap.scores[gamemap.player_index]['total']
	return 0

def _defense_path(gamemap, general, shortfall, config=None): # Reinforcement that can arrive before the attack lands AND actually cover it
	cfg = _config(gamemap, config)
	threat, threat_distance = general_threat_info(gamemap, cfg)
	deadline = None
	if threat_distance != None:
		deadline = threat_distance + cfg.defend_general_arrival_slack

	best_path, best_moves = None, None		# Covers the shortfall and gets here in time - soonest wins
	fallback_path, fallback_score = None, None	# Nothing sufficient is close enough - take the best army/distance tradeoff
	urgency = gather_urgency(gamemap, cfg)

	for source in _gather_candidates(gamemap, config=cfg):
		path = source.path_to(general)
		if len(path) < 2:
			continue

		moves = len(path) - 1
		delivered = _gather_score(path, general, 0, cfg.gather_delay_factor) # Raw army delivered, no delay discount

		if deadline != None and moves <= deadline and delivered >= shortfall:
			if best_moves == None or moves < best_moves: # Secure the general as early as we can
				best_moves, best_path = moves, path
		else:
			score = _gather_score(path, general, urgency, cfg.gather_delay_factor)
			if fallback_score == None or score > fallback_score:
				fallback_score, fallback_path = score, path

	return best_path if best_path != None else fallback_path

def _retake_near_general(gamemap, general, config=None): # Push the intruders back out, sourcing from anywhere but the garrison
	cfg = _config(gamemap, config)
	source = gamemap.find_largest_tile() # Never returns the general, so the garrison stays put
	if source == None or source.army < 2:
		return (False, False)

	target = None
	for tile in _tiles_near_general(gamemap, general, cfg.defend_general_radius):
		if tile.tile >= 0 and not tile.isSelf() and tile.shouldAttack() and tile.army < source.army:
			if target == None or tile.distance_to(general) < target.distance_to(general): # Clear the closest intruder first
				target = tile

	if target == None:
		return (False, False)

	return move_path(source.path_to(target), gamemap, cfg)

def move_defend_general(gamemap, config=None):
	cfg = _config(gamemap, config)
	if not cfg.defend_general:
		return (False, False)

	general = gamemap.generals[gamemap.player_index]
	if general == None:
		return (False, False)

	needed = garrison_needed(gamemap, cfg)
	if needed == 0: # Nothing visible is coming for us
		gamemap.defendingGeneral = False
		return (False, False)

	gamemap.defendingGeneral = True

	if general.army <= needed: # Garrison is short - pull in whatever can actually get here in time
		path = _defense_path(gamemap, general, needed - general.army, cfg)
		if path == None:
			return (False, False)
		return move_gather_step(path, config=cfg)

	return _retake_near_general(gamemap, general, cfg) # Garrison holds - go take our tiles back

######################### Move Path Forward #########################

def move_path(path, gamemap=None, config=None): # Pass gamemap to keep the move from spending our general's garrison
	if len(path) < 2:
		return (False, False)

	hold_general = gamemap != None and garrison_needed(gamemap, config) > 0

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

def path_proximity_target(gamemap, config=None):
	cfg = _config(gamemap, config)
	# Find path from largest tile to closest target
	includeGeneral = 0.5 if garrison_needed(gamemap, cfg) == 0 else False # Leave the garrison on our general alone
	source = gamemap.find_largest_tile(includeGeneral=includeGeneral)
	if source == None:
		return []
	target = source.nearest_target_tile()
	path = source.path_to(target)
	#logging.info("Proximity %s -> %s via %s" % (source, target, path))

	if not gamemap.canStepPath(path):
		path = path_gather(gamemap, config=cfg)
		#logging.info("Proximity FAILED, using path %s" % path)
	return path

def path_gather(gamemap, elsoDo=[], config=None):
	cfg = _config(gamemap, config)
	includeGeneral = garrison_needed(gamemap, cfg) == 0 # Leave the garrison on our general alone
	target = gamemap.find_largest_tile()
	if target == None:
		return elsoDo

	if not cfg.smart_gather: # Legacy: second-largest tile heads to the largest
		source = gamemap.find_largest_tile(notInPath=[target], includeGeneral=0.5 if includeGeneral else False)
		if source and target and source != target:
			return source.path_to(target)
		return elsoDo

	candidates = _gather_candidates(gamemap, includeGeneral=includeGeneral, exclude=[target], config=cfg)
	path = best_gather_path(gamemap, candidates, lambda source: target, cfg)
	if path == None:
		return elsoDo

	return path

######################### Helpers #########################

def _shuffle(seq):
	shuffled = list(seq)
	random.shuffle(shuffled)
	return iter(shuffled)
