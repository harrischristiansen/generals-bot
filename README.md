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

## Bot Arena (Local Testing)

`tools/arena` plays two git refs' versions of a bot's move logic against each other, many games in a row, headlessly (no network, no viewer) - useful for gauging whether a change actually made the bot stronger.

- [ ] Compare current code against an earlier commit: `python3 -m tools.arena.runner HEAD HEAD~3 --games 50`
- [ ] Compare two branches with a different move script: `python3 -m tools.arena.runner HEAD my-branch --bot bot_blob --games 20`

Flags (all optional except the two git refs): `--bot` move-method script to run, `bot_test` or `bot_blob` only - `bot_control.py` needs manual input and won't work here (default `bot_test`); `--games` number of games to play (default `20`); `--rows` / `--cols` map size (default `25` / `25`); `--seed` base random seed for map generation (default random); `--verbose` print score progress every 50 turns.

Each ref is checked out into its own git worktree and run in its own subprocess, so two different commits' code never collide even if their `Map`/`Tile` classes differ. Moves are decided against a local rules engine that approximates generals.io's growth/combat rules (not bit-exact with the real server, and each turn resolves the two players' moves sequentially rather than truly simultaneously), with a per-player fog-of-war view fed through the real `Map` class exactly as the live server would. Worktrees are cached under `.arena-worktrees/` (gitignored) and reused across runs - safe to delete if you want a clean checkout.

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

### Tools
- [X] tools/arena: Local headless arena for pitting two git refs' bot versions against each other (see "Bot Arena (Local Testing)" above)

## Contributors

@harrischristiansen [HarrisChristiansen.com](http://www.harrischristiansen.com) (code@harrischristiansen.com)  
