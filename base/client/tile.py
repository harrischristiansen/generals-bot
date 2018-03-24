"""
    @ Harris Christiansen (code@HarrisChristiansen.com)
    Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
    Tile: Objects for representing Generals IO Tiles
"""

from queue import Queue

from .constants import *


class Tile(object):
    def __init__(self, gamemap, x, y):
        # Public Properties
        self.x = x  # Integer X Coordinate
        self.y = y  # Integer Y Coordinate
        self.tile = TILE_FOG  # Integer Tile Type (TILE_OBSTACLE, TILE_FOG, TILE_MOUNTAIN, TILE_EMPTY, or player_ID)
        self.turn_captured = 0  # Integer Turn Tile Last Captured
        self.turn_held = 0  # Integer Last Turn Held
        self.army = 0  # Integer Army Count
        self.isCity = False  # Boolean isCity
        self.isSwamp = False  # Boolean isSwamp
        self.isGeneral = False  # Boolean isGeneral

        # Private Properties
        self._map = gamemap  # Pointer to Map Object
        self._general_index = -1  # Player Index if tile is a general

    def __repr__(self):
        return "(%d,%d) %d (%d)" % (self.x, self.y, self.tile, self.army)

    # def __eq__(self, other):
    #     return (other != None and self.x == other.x and self.y == other.y)

    def __lt__(self, other):
        return self.army < other.army

    def set_neighbors(self, gamemap):
        self._map = gamemap
        self._set_neighbors()

    def set_is_swamp(self, is_swamp):
        self.isSwamp = is_swamp

    def update(self, gamemap, tile, army, is_city=False, is_general=False):
        self._map = gamemap

        if self.tile < 0 or tile >= TILE_MOUNTAIN or (tile < TILE_MOUNTAIN and self.is_self()):
            # Tile should be updated
            if (tile >= 0 or self.tile >= 0) and self.tile != tile:  # Remember Discovered Tiles
                self.turn_captured = gamemap.turn
                if self.tile >= 0:
                    gamemap.tiles[self.tile].remove(self)
                if tile >= 0:
                    gamemap.tiles[tile].append(self)
            if tile == gamemap.player_index:
                self.turn_held = gamemap.turn
            self.tile = tile
        if self.army == 0 or army > 0 or tile >= TILE_MOUNTAIN or self.isSwamp:  # Remember Discovered Armies
            self.army = army

        if is_city:
            self.isCity = True
            self.isGeneral = False
            if self not in gamemap.cities:
                gamemap.cities.append(self)
            if self._general_index != -1 and self._general_index < 8:
                gamemap.generals[self._general_index] = None
                self._general_index = -1
        elif is_general:
            self.isGeneral = True
            gamemap.generals[tile] = self
            self._general_index = self.tile

    ################################ Tile Properties ################################

    def distance_to(self, dest):
        if dest is not None:
            return abs(self.x - dest.x) + abs(self.y - dest.y)
        return 0

    def neighbors(self, include_swamps=False, include_cities=True):
        neighbors = []
        for tile in self._neighbors:
            if (tile.tile != TILE_OBSTACLE or tile.isCity or tile.isGeneral) and tile.tile != TILE_MOUNTAIN and (
                    include_swamps or not tile.isSwamp) and (include_cities or not tile.isCity):
                neighbors.append(tile)
        return neighbors

    def is_valid_target(self):  # Check tile to verify reachablity
        if self.tile < TILE_EMPTY:
            return False
        for tile in self.neighbors(include_swamps=True):
            if tile.turn_held > 0:
                return True
        return False

    def is_self(self):
        return self.tile == self._map.player_index

    def is_on_team(self):
        if self.is_self():
            return True
        return False

    def should_not_attack(self):
        if self.is_on_team():
            return True
        if self.tile in self._map.do_not_attack_players:
            return True
        return False

    ################################ Select Other Tiles ################################

    def nearest_tile_in_path(self, path):
        dest = None
        # noinspection PyUnusedLocal
        # TODO: unused local variable
        dest_distance = 9999
        for tile in path:
            distance = self.distance_to(tile)
            # noinspection PyUnresolvedReferences
            # TODO: unresolved reference to tile_distance
            if distance < tile_distance:
                dest = tile
                # noinspection PyUnusedLocal
                # TODO: unused local variable
                dest_distance = distance

        return dest

    def nearest_target_tile(self):
        max_target_army = self.army * 2 + 14

        dest = None
        dest_distance = 9999
        for x in range(self._map.cols):  # Check Each Square
            for y in range(self._map.rows):
                tile = self._map.grid[y][x]
                if not tile.is_valid_target() or tile.should_not_attack() or tile.army > max_target_army:
                    # Non Target Tiles
                    continue

                distance = self.distance_to(tile)
                if tile.isGeneral:  # Generals appear closer
                    distance *= 0.09
                elif tile.isCity:  # Cities vary distance based on size, but appear closer
                    distance = distance * sorted((0.17, (tile.army / (3.2 * self.army)), 20))[1]

                if tile.tile == TILE_EMPTY:  # Empties appear further away
                    distance *= 4.3
                if tile.army > self.army:  # Larger targets appear further away
                    distance = distance * (1.5 * tile.army / self.army)
                if tile.isSwamp:  # Swamps appear further away
                    distance *= 10
                    if tile.turn_held > 0:  # Swamps which have been held appear even further away
                        distance *= 20

                if distance < dest_distance:
                    dest = tile
                    dest_distance = distance

        return dest

    ################################ Pathfinding ################################

    def path_to(self, dest, include_cities=False):
        if dest is None:
            return []

        frontier = Queue()
        frontier.put(self)
        came_from = {self: None}
        army_count = {self: self.army}

        while not frontier.empty():
            current = frontier.get()

            if current == dest:  # Found Destination
                break

            for next_neighbor in current.neighbors(include_swamps=True, include_cities=include_cities):

                if next_neighbor not in came_from and (
                        next_neighbor.is_on_team() or
                        next_neighbor == dest or
                        next_neighbor.army < army_count[current]):
                    # priority = self.distance(next_neighbor, dest)
                    frontier.put(next_neighbor)
                    came_from[next_neighbor] = current
                    if next_neighbor.is_on_team():
                        army_count[next_neighbor] = army_count[current] + (next_neighbor.army - 1)
                    else:
                        army_count[next_neighbor] = army_count[current] - (next_neighbor.army + 1)

        if dest not in came_from:  # Did not find dest
            if include_cities:
                return []
            else:
                return self.path_to(dest, include_cities=True)

        # Create Path List
        path = _path_reconstruct(came_from, dest)

        return path

    ################################ PRIVATE FUNCTIONS ################################

    def _set_neighbors(self):
        x = self.x
        y = self.y

        neighbors = []
        for dy, dx in DIRECTIONS:
            if self._map.is_valid_position(x + dx, y + dy):
                tile = self._map.grid[y + dy][x + dx]
                neighbors.append(tile)

        self._neighbors = neighbors
        return neighbors


def _path_reconstruct(came_from, dest):
    current = dest
    path = [current]
    try:
        while came_from[current] is not None:
            current = came_from[current]
            path.append(current)
    except KeyError:
        pass
    path.reverse()

    return path
