# Generals.io - Automated Client

![Generals.IO Gameplay Image](http://files.harrischristiansen.com/0r0y0C1t2r26/generals.png "Generals.IO Gameplay Image")

## Synopsis

[Generals.io](http://generals.io) is a multiplayer web game where the goal is to protect your general and capture the enemy generals.  

This is a collection of various automated clients (bots) for playing [Generals.io](http://generals.io).  

Project available on [GitHub](https://github.com/harrischristiansen/generals-bot).  

## Setup

- [ ] Install Dependencies: `pip install -r requirements.txt`
- [ ] Edit `bot_*.py`: At bottom set bot name and game type in bot_base.GeneralsBot(...)
- [ ] NPM Forever: `npm install -g forever` (optional)

## Usage

- [ ] Blob Bot: `python bot_blob.py`
- [ ] Path Bot: `python bot_path_collect.py`

- [ ] Run Forever: `forever start -c python bot_NAME.py `

## Features

### Bots
- [X] bot_blob.py
	- [X] Run largest army to nearest priority target
	- [X] Move Border Armies Outward
- [ ] bot_path_collect.py
	- [X] Primary Path Routine: Run path from largest city to primary target
		- [ ] Continue running after reaching primary target
	- [X] Collect Troops Routine (Run largest army toward nearest path tile)
	- [X] Move Border Armies Outward
	- [ ] Proximity Targeting

### Sample Code
- [ ] samples/nearest.py: Run largest army to nearest priority target

### Bot Base
- [X] Bot Base
	- [X] find_largest_tile(ofType, notInPath, includeGeneral): Returns largest tile ofType, notInPath, optionally includeGeneral
	- [X] find_city(ofType, notOfType, findLargest, includeGeneral): Finds largest/smallest city ofType (or notOfType), optionally includeGenerals
	- [X] find_closest_in_path(source_tile, path): Returns dest_tile in path nearest to source_tile
	- [X] find_closest_target(source): Returns closest tile to target given a source
		- [ ] Do not target unreachable tiles
	- [X] find_primary_target(target): Returns primary tile to target, optionally given an previous unobtained target to consider
		- [ ] Do not target unreachable tiles
	- [X] find_path(source, dest): Finds optimal path from source to dest
		- [ ] Improve Pathfinding
			- [ ] Correctly collect max chains and run shortest paths
	- [X] path_forward_moves(path): Returns (from_tile, to_tile) to move next given the current state of a path.
	- [X] toward_dest_moves(source, dest): Returns DIRECTIONS array with first directions toward dest
	- [X] away_king_moves(source): Returns DIRECTIONS array with first directions away from general
	- [X] moves_random(): Returns DIRECTION array shuffled
	- [X] distance(source, dest): Returns Manhattan distance between source and dest
	- [X] place_move(source, dest, moveHalf=False): Place move from source to dest
		- [ ] Only permit 1 move/turn
	- [X] validPosition(x,y): Returns boolean if x,y is valid tile in grid

### Client/Viewer
- [X] Client
	- [X] Join Game
	- [X] Receive Map Updates
		- [X] Maintain Map of tiles, with memory (remembers previously visited tiles).
	- [X] Make Moves
	- [X] Send/Receive Chat
- [X] Viewer
	- [X] View Grid (Color tiles w/ army count, circles for cities/generals)
		- [ ] Uniquely identify generals
	- [X] View Leaderboard (Sorted, colored boxes w/ player name, army count, and # tiles)
		- [ ] Add player ratings estimated # cities

## Contributors

@harrischristiansen [HarrisChristiansen.com](http://www.harrischristiansen.com) (harris@harrischristiansen.com)  
