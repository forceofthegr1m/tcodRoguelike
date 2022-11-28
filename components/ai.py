from __future__ import annotations

import random
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction

if TYPE_CHECKING:
    from entity import Actor


class BaseAI(Action):
    entity: Actor

    """ Doesn't implement a perform method, since entities which will be using AI to act will have
        to have an AI class that inherits from this one. """
    def perform(self) -> None:
        raise NotImplementedError()

    """ Uses the "walkable" tiles in our map, along with some TCOD pathfinding tools to get the 
        path from the BaseAI's parent entity to whatever their target might be. In the case of
        the tutorial, the target will always be the player, though you could theoretically write
        a monster that cares more about food or treasure than attacking the player. """
    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """ Compute and return a path to the target position.
            If there is no valid path then returns an empty list. """

        # Copy the walkable array
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # Check that an entity blocks movement and the cost ins't zero (blocking).
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in hallways.
                # A higher number means enemies will take longer paths in order to surround the
                # player.
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass that graph to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # Starting position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]


class ConfusedEnemy(BaseAI):
    """ A confused enemy will stumble around aimlessly for a given number of turns, then revert
        back to its previous AI. If an actor occupies a tile it is randomly moving into, it
        will attack. """

    def __init__(
            self,
            entity: Actor,  # The actor who is being confused.
            previous_ai: Optional[BaseAI],  # The AI class that the actor currently has. This is
            # needed because when the confusion effect wears off, the entity must revert back to
            # its previous AI.
            turns_remaining: int  # How many turns the confusion effect will last for.
    ):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    """ Causes the entity to move in a randomly selected direction. It uses BumpAction, which means
        that it will try to move into a tile, and if there's an actor there, it will attack it 
        (regardless if it's the player or another monster). Each turn, the turns_remaining will
        decrement, and when it's less than or equal to zero, the AI reverts back and the entity
        is no longer confused. """
    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"The {self.entity.name} is no longer confused."
            )
            self.entity.ai = self.previous_ai
        else:
            # Pick a random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Northwest
                    (0, -1),  # North
                    (1, -1),  # Northeast
                    (-1, 0),  # West
                    (1, 0),  # East
                    (-1, 1),  # Southwest
                    (0, 1),  # South
                    (1, 1)  # Southeast
                ]
            )

            self.turns_remaining -= 1

            # The actor will either try to move or attack in the chosen random direction.
            # It's possible the actor will just bump into the wall, wasting a turn.
            return BumpAction(self.entity, direction_x, direction_y).perform()


class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        # Check is entity is within player's FOV. If not, then wait.
        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            # Check if distance of target. If it is less than or equal to one (right next to player),
            # then the monster attacks the player.
            if distance <= 1:
                return MeleeAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

        # If entity is in player's FOV, but is not adjacent to player, move towards player.
        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y
            ).perform()

        return WaitAction(self.entity).perform()
