from __future__ import annotations

from typing import Iterable, Iterator, Optional, TYPE_CHECKING, Union

import numpy as np  # type: ignore
from tcod.console import Console

from entity import Actor, Item
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class GameMap:
    def __init__(self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)

        # Create a 2D array filled with all the same values (wall tiles)
        # This will be the base map, which generate_dungeon will then use to
        # "dig out" rooms and tunnels.
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        self.visible = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player can currently see.
        self.explored = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player has seen, but are not currently in FOV

        self.downstairs_location = (0, 0)

    @property
    def gamemap(self) -> GameMap:
        return self

    @property
    def actors(self) -> Iterator[Actor]:
        """ Iterate over this map's living actors. """
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )

    @property
    def items(self) -> Iterator[Item]:
        yield from (entity for entity in self.entities if isinstance(entity, Item))

    def get_blocking_entity_at_location(
            self, location_x: int, location_y: int
    ) -> Optional[Entity]:
        for entity in self.entities:
            if (
                    entity.blocks_movement
                    and entity.x == location_x
                    and entity.y == location_y
            ):
                return entity

        return None

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor

        return None

    def in_bounds(self, x: int, y: int) -> bool:
        """ Return True if x and y are inside the bounds of this map. """
        return 0 <= x < self.width and 0 <= y < self.height

    # Using the Console class's tiles_rgb method, we can quickly render the entire map.
    # This method proves much faster than using the console.print method we use for
    # individual entities.
    def render(self, console: Console) -> None:
        # Renders the map. If a tile is in the "visible" array, then draw it with the "light"
        # colors. If it isn't, but it's in the "explored" array, then draw it with the "dark"
        # colors. Otherwise, the default is "SHROUD".
        console.tiles_rgb[0: self.width, 0: self.height] = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD
        )

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            # Only print entities that are in the FOV
            if self.visible[entity.x, entity.y]:
                console.print(
                    x=entity.x,
                    y=entity.y,
                    string=entity.char,
                    fg=entity.color
                )


class GameWorld:
    """ Holds settings for the GameMap, and generates new maps when moving down stairs. """

    def __init__(
            self,
            *,
            engine: Engine,
            map_width: int,
            map_height: int,
            max_rooms: int,
            room_min_size: int,
            room_max_size: int,
            max_monsters_per_room: int,
            max_items_per_room: int,
            max_containers_per_room: int,
            current_floor: int = 0
    ):
        self.engine = engine

        self.map_width = map_width
        self.map_height = map_height

        self.max_rooms = max_rooms

        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

        self.max_monsters_per_room = max_monsters_per_room
        self.max_items_per_room = max_items_per_room
        self.max_containers_per_room = max_containers_per_room

        self.current_floor = current_floor

    """ Creates a new map each time the player goes down a floor, using the variables that GameWorld
        stores. Could perhaps modify GameWorld to hold the previous maps. """
    def generate_floor(self) -> None:
        from procgen import generate_dungeon

        self.current_floor += 1

        self.engine.game_map = generate_dungeon(
            max_rooms=self.max_rooms,
            room_min_size=self.room_min_size,
            room_max_size=self.room_max_size,
            map_width=self.map_width,
            map_height=self.map_height,
            max_monsters_per_room=self.max_monsters_per_room,
            max_items_per_room=self.max_items_per_room,
            max_containers_per_room=self.max_containers_per_room,
            engine=self.engine
        )
