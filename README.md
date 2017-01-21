# Generals.io - Automated Client

![Generals.IO Gameplay Image](http://files.harrischristiansen.com/0r0y0C1t2r26/generals.png "Generals.IO Gameplay Image")

## Synopsis

[Generals.io](http://generals.io) is a multiplayer web game where the goal is to protect your general and capture the enemy generals.  

This is a collection of various automated clients (bots) for playing [Generals.io](http://generals.io).  

Project available on [GitHub](https://github.com/harrischristiansen/generals-bot).  

## Setup

- [ ] `pip install -r requirements.txt`
- [ ] Edit `bot_*.py`: At bottom set bot name and match type

## Usage

- [ ] Blob Bot: `python bot_blob.py`
- [ ] Path Bot: `python bot_path_collect.py`

## Features

- [X] Bot Base
	- [X] Primary Target Finding
	- [X] Path Finding
		- [X] Improve Pathfinding w/ army count + cities
			- [ ] Optimize for max army size and path length
			- [ ] Fix Dumb Paths
		- [ ] Fix pathfinding to always find target
			- [ ] Do not target islands
- [X] Blob Bot
	- [X] Expand Blob
	- [X] Dumb Army Distribution
	- [X] Run Large Armies Outward. Prioritize Opponents and Cities
- [ ] Path Collect Bot
	- [X] Run Path Routine
		- [ ] Continue running after reaching primary target
	- [X] Collect Troops Routine (Run largest blob toward closest path point)
	- [X] Expand Outward Routine
	- [ ] Proximity Targeting

## Contributors

@harrischristiansen [HarrisChristiansen.com](http://www.harrischristiansen.com) (harris@harrischristiansen.com)  
