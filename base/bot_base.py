"""
    @ Harris Christiansen (code@HarrisChristiansen.com)
    Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
    Generals Bot: Base Bot Class
"""

import logging
import os
import threading
import time

from .client import generals
from .client.constants import *
from .viewer import GeneralsViewer


class GeneralsBot(object):
    def __init__(self, move_method, move_event=None, name="PurdueBot", game_type="private", private_room_id=None,
                 show_game_viewer=True, public_server=False, start_msg_cmd=""):
        # Save Config
        self._moveMethod = move_method
        self._name = name
        self._gameType = game_type
        self._privateRoomID = private_room_id
        self._public_server = public_server
        self._start_msg_cmd = start_msg_cmd

        # ----- Start Game -----
        self._running = True
        self._move_event = threading.Event()
        _create_thread(self._start_game_thread)
        _create_thread(self._start_chat_thread)
        _create_thread(self._start_moves_thread)

        # Start Game Viewer
        if show_game_viewer:
            window_title = "%s (%s)" % (self._name, self._gameType)
            if self._privateRoomID is not None:
                window_title = "%s (%s - %s)" % (self._name, self._gameType, self._privateRoomID)
            self._viewer = GeneralsViewer(window_title, move_event=move_event)
            self._viewer.main_viewer_loop()  # Consumes Main Thread
            self._exit_game()

        while self._running:
            time.sleep(10)

        self._exit_game()

    ######################### Handle Updates From Server #########################

    def _start_game_thread(self):
        # Create Game
        self._game = generals.Generals(self._name, self._name, self._gameType, game_id=self._privateRoomID,
                                       public_server=self._public_server)
        _create_thread(self._send_start_msg_cmd)

        # Start Receiving Updates
        for gamemap in self._game.get_updates():
            self._set_update(gamemap)

            if not gamemap.complete:
                self._move_event.set()  # Permit another move

        self._exit_game()

    def _set_update(self, gamemap):
        self._map = gamemap
        self_dir = dir(self)

        # Update GeneralsViewer Grid
        if '_viewer' in self_dir:
            if '_moves_realized' in self_dir:
                self._map.bottomText = "Realized: " + str(self._moves_realized)
            # noinspection PyUnusedLocal
            viewer = self._viewer.update_grid(gamemap)

        # Handle Game Complete
        if gamemap.complete and not self._has_completed:
            logging.info("!!!! Game Complete. Result = " + str(gamemap.result) + " !!!!")
            if '_moves_realized' in self_dir:
                logging.info("Moves: %d, Realized: %d" % (self._map.turn, self._moves_realized))
            _create_thread(self._exit_game)
        self._has_completed = gamemap.complete

    def _exit_game(self):
        time.sleep(1.1)
        if not self._map.exit_on_game_over:
            time.sleep(100)
        self._running = False
        # noinspection PyProtectedMember
        os._exit(0)  # End Program

    ######################### Move Generation #########################

    def _start_moves_thread(self):
        self._moves_realized = 0
        while self._running:
            self._move_event.wait()
            self._make_move()
            self._move_event.clear()
            self._moves_realized += 1

    def _make_move(self):
        self._moveMethod(self, self._map)

    ######################### Chat Messages #########################

    def _start_chat_thread(self):
        # Send Chat Messages
        while self._running:
            msg = str(input('Send Msg:'))
            self._game.send_chat(msg)
            time.sleep(0.7)
        return

    def _send_start_msg_cmd(self):
        time.sleep(0.2)
        for cmd in self._start_msg_cmd.split("\\n"):
            self._game.handle_command(cmd)

    ######################### Move Making #########################

    def place_move(self, source, dest, move_half=False):
        if self._map.is_valid_position(dest.x, dest.y):
            self._game.move(source.y, source.x, dest.y, dest.x, move_half)
            if SHOULD_DIRTY_MAP_ON_MOVE:
                self._update_map_dirty(source, dest, move_half)
            return True
        return False

    def _update_map_dirty(self, source, dest, move_half):
        army = source.army if not move_half else source.army / 2
        source.update(self._map, source.tile, 1)

        if dest.is_on_team():  # Moved Internal Tile
            dest_army = army - 1 + dest.army
            dest.update(self._map, source.tile, dest_army)
            return True

        elif army > dest.army + 1:  # Captured Tile
            dest_army = army - 1 - dest.army
            dest.update(self._map, source.tile, dest_army, isCity=dest.isGeneral)
            return True
        return False


######################### Global Helpers #########################

def _create_thread(f):
    t = threading.Thread(target=f)
    t.daemon = True
    t.start()
