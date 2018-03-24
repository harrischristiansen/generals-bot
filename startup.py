"""
    @ Harris Christiansen (code@HarrisChristiansen.com)
    Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
    Startup: Initiate Bots with command line arguments
"""
import argparse
import os

from base import bot_base


def startup(move_method, move_event=None, bot_name="PurdueBot"):
    parser = argparse.ArgumentParser()
    parser.add_argument('-name', metavar='str', type=str, default=os.environ.get('GENERALS_BOT_NAME', bot_name),
                        help='Name of Bot')
    parser.add_argument('-g', '--gameType', metavar='str', type=str, choices=["private", "1v1", "ffa"],
                        default=os.environ.get('GENERALS_BOT_MODE', 'private'), help='Game Type: private, 1v1, or ffa')
    parser.add_argument('-r', '--roomID', metavar='str', type=str,
                        default=os.environ.get("GENERALS_BOT_ROOM_ID", "PurdueBot"), help='Private Room ID (optional)')
    parser.add_argument('-c', '--command', metavar='str', type=str, default="", help='Initial Setup Command (optional)')
    parser.add_argument('--no-ui', action='store_false', help="Hide UI (no game viewer)")
    parser.add_argument('--public', action='store_true', help="Run on public (not bot) server")
    args = vars(parser.parse_args())

    if move_method is None:
        raise ValueError("A move method must be supplied upon startup")

    bot_base.GeneralsBot(move_method, move_event=move_event, name=args['name'], game_type=args['gameType'],
                         private_room_id=args['roomID'], show_game_viewer=args['no_ui'], public_server=args['public'],
                         start_msg_cmd=args['command'])
