# Generals.io - Automated Client

## Synopsis

[Generals.io](http://generals.io) is a multiplayer web client game where the goal is to protect your general and capture the enemy generals.  

This is a collection of various automated clients (bots) for playing [Generals.io](http://generals.io).  

Project available on [GitHub](https://github.com/harrischristiansen/generals-bot).  

## Setup

- [ ] `pip install -r requirements.txt`

## Features

- [X] Bot Base
	- [X] Primary Target Finding
	- [X] Path Finding
		- [ ] Improve Path Selection (use army count and cities in selection)
		- [ ] Fix pathfinding to always find target
- [X] Blob Bot
	- [X] Expand Blob
	- [X] Dumb Army Distribution
	- [X] Run Large Armies Outward. Prioritize Opponents and Cities
	- [ ] Translate to new bot base
- [ ] Path Collect Bot
	- [X] Run Path Routine
		- [ ] Regenerate primary path each restart
		- [ ] Continue running after reaching primary target
	- [X] Collect Troops Routine (Run largest blob toward closest path point)
		- [ ] Bug Test
	- [X] Expand Outward Routine
	- [ ] Sub-prioritize cities/etc

## Contributors

@harrischristiansen [HarrisChristiansen.com](http://www.harrischristiansen.com) (harris@harrischristiansen.com)   

[Python client](https://github.com/toshima/generalsio) by [@toshima](https://github.com/toshima)