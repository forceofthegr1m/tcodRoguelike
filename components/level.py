from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class Level(BaseComponent):
    parent: Actor

    def __init__(
            self,
            current_level: int = 1,  # The current level of the Entity, which defaults to 1.
            current_xp: int = 0,  # The Entity's current experience points.
            level_up_base: int = 0,  # The base number we decide for leveling up. We'll set this to
            # 200 when creating the Player.
            level_up_factor: int = 150,  # The number to multiply against the Entity's current level.
            xp_given: int = 0  # When the Entity dies, this is how much XP the Player will be given.
    ):
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.level_up_factor = level_up_factor
        self.xp_given = xp_given

    """ This represents how much experience the player needs to hit the next level. """
    @property
    def experience_to_next_level(self) -> int:
        return self.level_up_base + self.current_level * self.level_up_factor

    """ This property determines if the player needs to level up or not. If the current xp is 
        higher than the xp needed to level up, then the player levels up. If not, then nothing
        happens. """
    @property
    def requires_level_up(self) -> bool:
        return self.current_xp > self.experience_to_next_level

    """ This method adds xp to the Entity's xp pool, as the name implies. If the value is 0, we just
        return, as there's nothing to do. Notice that we also return is the level_up_base is 0. Why?
        Because enemies don't level up, so we'll set their level_up_base to 0 so there's no way they
        could ever gain xp in the first place. """
    def add_xp(self, xp: int) -> None:
        if xp == 0 or self.level_up_base == 0:
            return

        self.current_xp += xp

        self.engine.message_log.add_message(f"You gain {xp} experience points!")

        if self.requires_level_up:
            self.engine.message_log.add_message(
                f"You advance to level {self.current_level + 1}!"
            )

    """ This method adds 1 to the current_level, while decreasing the current_xp by the 
        experience_to_next_level. We do this because if we didn't it would always just take the 
        level_up_factor amount to level up, which isn't what we want. If you want to keep track of
        the player's cumulative xp throughout the playthrough (like instead of xp the monsters just
        gave points and then you could have a tracker for the player's score), you could skip
        decrementing the current_xp and instead adjust the experience_to_next_level formula
        accordingly. """
    def increase_level(self) -> None:
        self.current_xp -= self.experience_to_next_level

        self.current_level += 1

    def increase_max_hp(self, amount: int = 20) -> None:
        self.parent.fighter.max_hp += amount
        self.parent.fighter.hp += amount

        self.engine.message_log.add_message("Your health improves!")

        self.increase_level()

    def increase_power(self, amount: int = 1) -> None:
        self.parent.fighter.base_power += amount

        self.engine.message_log.add_message("You feel stronger!")

        self.increase_level()

    def increase_defense(self, amount: int = 1) -> None:
        self.parent.fighter.base_defense += amount

        self.engine.message_log.add_message("Your movements are getting swifter!")

        self.increase_level()