'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	March 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Startup: Initiate Bots with command line arguments
'''
import os
import argparse
from base import bot_base

def startup(moveMethod, botName="PurdueBot"):
    parser = argparse.ArgumentParser()
    parser.add_argument('-name', metavar='str', type=str, default=os.environ.get('BOT_NAME', botName), help='Name of Bot')
    parser.add_argument('-g', '--gameType', metavar='str', type=str, choices=["private","1v1","ffa"], default=os.environ.get('BOT_MODE', 'private'), help='Game Type: private, 1v1, or ffa')
    parser.add_argument('-r', '--roomID', metavar='str', type=str, default=os.environ.get("BOT_ROOM_ID", "PurdueBot"), help='Private Room ID (optional)')
    parser.add_argument('--no-ui', action='store_false', help="Hide UI (no game viewer)")
    args = vars(parser.parse_args())

    if (moveMethod == None):
    	raise ValueError("A move method must be supplied upon startup")
    
    bot_base.GeneralsBot(moveMethod, name=args['name'], gameType=args['gameType'], privateRoomID=args['roomID'], gameViewer=args['no_ui'])
