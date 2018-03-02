# Generals.io - Automated Client

![Generals.IO Gameplay Image](http://files.harrischristiansen.com/0r0y0C1t2r26/generals.png "Generals.IO Gameplay Image")

## Synopsis

[Generals.io](http://generals.io) is a multiplayer web game where the goal is to protect your general and capture the enemy generals.  

This is a collection of various automated clients (bots) for playing [Generals.io](http://generals.io). The project includes a toolkit for creating bots, as well as a UI viewer for watching live games.  

Project available on [GitHub](https://github.com/harrischristiansen/generals-bot).  

## Setup

- [ ] Python3 (https://www.python.org/downloads/)
- [ ] Install Dependencies: `pip3 install -r requirements.txt`
- [ ] NPM Forever: `npm install -g forever` (optional)

## Usage

- [ ] Blob Bot: `python3 bot_blob.py [-name] [-g gameType] [-r roomID]`
- [ ] Path Bot: `python3 bot_path_collect.py [-name] [-g gameType] [-r roomID]`

- [ ] Run Forever: `forever start -c python3 bot_blob.py -name BotName -g ffa`

## Features

### Bots
- [X] bot_blob.py
	- [X] move_toward: Run largest army to nearest priority target
	- [X] move_outward: Move Border Armies Outward
- [ ] bot_path_collect.py
	- [X] Primary Path Routine: Run path from largest city to primary target
		- [ ] Continue running after reaching primary target
	- [X] Collect Troops Routine (Run largest army toward nearest path tile)
	- [X] Move Border Armies Outward
	- [ ] Proximity Targeting

### Sample Code
- [ ] samples/nearest.py: Run largest army to nearest priority target

## Contributors

@harrischristiansen [HarrisChristiansen.com](http://www.harrischristiansen.com) (code@harrischristiansen.com)  
