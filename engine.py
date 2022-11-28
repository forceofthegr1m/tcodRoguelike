from __future__ import annotations

import lzma
import pickle
from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

import exceptions
from message_log import MessageLog
import render_functions

if TYPE_CHECKING:
    from entity import Entity
    from game_map import GameMap, GameWorld


class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player  # The player entity. Separate reference outside of entities for ease
        # of access. Need to access player a lot more than any other entity.

    def handle_enemy_turns(self) -> None:
        # Loop through all current Acting entities, except the player.
        for entity in set(self.game_map.actors) - {self.player}:
            # If the Actor in question has an ai class, then execute that class's peform() function.
            if entity.ai:
                try:
                    entity.ai.perform()
                except:
                    pass  # Ignore impossible action exceptions from AI.

    def update_fov(self) -> None:
        """ Recompute the visible area based on the player's point of view. """
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],  # 2D numpy array where every non-zero value is considered transparent.
            (self.player.x, self.player.y),  # origin of the fov
            radius=8  # radius of fov
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

    # Handles drawing the screen. Iterates through self.entities and print them to their proper
    # locations, then present the context, and clear the console, just like in main.py
    def render(self, console: Console) -> None:
        self.game_map.render(console)  # Call GameMap's render method to draw it to the screen.

        self.message_log.render(console=console, x=21, y=45, width=40, height=5)

        render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20
        )

        render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 47)
        )

        render_functions.render_names_at_mouse_location(
            console=console, x=21, y=44, engine=self
        )

    """ pickle.dumps serializes an object hierarchy in Python. lzma.compress compresses the data,
        fo that it take up less space (obviously). We then use with open(filename, "wb") as f: to
        write the file (wb means "write in binary mode"), calling f.write(save_data) to write the
        data. Because everything we are trying to save is already in the Engine class, all we have
        to do is pickle it and write the file to the disk, and voila, the game is saved. """
    def save_as(self, filename: str) -> None:
        """ Save the Engine instance as a compressed file. """
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)
