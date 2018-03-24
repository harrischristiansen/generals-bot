"""
    @ Harris Christiansen (code@HarrisChristiansen.com)
    Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
    bot_test: Used for testing various move methods
"""

import logging

import startup
from base import bot_moves

# Show all logging
logging.basicConfig(level=logging.DEBUG)

######################### Move Making #########################

_bot = None
_map = None


def make_move(current_bot, current_map):
    global _bot, _map
    _bot = current_bot
    _map = current_map

    move_outward()


def place_move(source, dest):
    _bot.place_move(source, dest)


######################### Move Outward #########################

def move_outward():
    (source, dest) = bot_moves.move_outward(_map)
    if source and dest:
        place_move(source, dest)
        return True
    return False


######################### Main #########################

# Start Game

if __name__ == '__main__':
    startup.startup(make_move, "PurdueBot-T")
