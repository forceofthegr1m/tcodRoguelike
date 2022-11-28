from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent
from equipment_types import EquipmentType

if TYPE_CHECKING:
    from entity import Actor, Item


class Equipment(BaseComponent):
    parent: Actor

    """ The weapon and armor attributes are what will hold the actual equippable entity. Both can
        be set to None, which represents nothing being equipped in those slots. Can add more
        attributes to suit needs (instead of armor, could be head, body, legs, etc., or allow for
        off-hand weapons and/or shields). """
    def __init__(self, weapon: Optional[Item] = None, armor: Optional[Item] = None):
        self.weapon = weapon
        self.armor = armor

    """ These properties (pwr and def bonus) do the same thing, just for different things. Both 
        calculate the 'bonus' gifted by equipment to either defense or power, based on what's
        equipped. Notice that we take the 'power' bonus from both weapons and armor, and the same
        applies to the 'defense' bonus. This allows you to create weapons that increase both atk and
        def (like a spiked shield, for example), and armor that increases atk 
        (i.e. magical armor). """
    @property
    def defense_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.defense_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.defense_bonus

        return bonus

    @property
    def power_bonus(self) -> int:
        bonus = 0

        if self.weapon is not None and self.weapon.equippable is not None:
            bonus += self.weapon.equippable.power_bonus

        if self.armor is not None and self.armor.equippable is not None:
            bonus += self.armor.equippable.power_bonus

        return bonus

    """ Allows us to quickly check if an Item is equipped by the player or not. """
    def item_is_equipped(self, item: Item) -> bool:
        return self.weapon == item or self.armor == item

    """ Both these methods (equip and unequip msg) add a message to the log, depending on whether
        the player is equipping or removing a piece of equipment. """
    def unequip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You remove the {item_name}."
        )

    def equip_message(self, item_name: str) -> None:
        self.parent.gamemap.engine.message_log.add_message(
            f"You equip the {item_name}."
        )

    """ equip_to_slot and unequip_from_slot add or remove an Item to the given 'slot' (weapon or
        armor). We use getattr to get the slot, whether it's weapon or armor. We use getattr
        because we won't actually know which one we're getting until the function is called.
        gettattr allows us to 'get an attribute' on a class (self in this case) and do what we 
        want with it. We use setattr to 'set the attribute' the same way. 
        
        unequip_from_slot simply removes the item. equip_to_slot first check is there's something 
        already equipped to that slot, and calls unequip_from_slot if there is. This way, we can't
        stack armor in the same slot (you can't have two helmets on at once).
        
        What's with the add_message part? Normally, we'll want to add a message to the message log
        when we equip/remove things, but in this section, we'll see an exception: When we set up the
        player's initial equipment. We'll use the same 'equip' methods to set up the initial 
        equipment, but there's no need to begin every game with message that say the player has put
        on their starting equipment (presumably, the player character did this before walking into
        the dungeon). add_message gives us a simple way to not add the messages if they aren't 
        necessary. Could also use this functionality to secretly equip or remove items from the
        player. """
    def equip_to_slot(self, slot: str, item: Item, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        setattr(self, slot, item)

        if add_message:
            self.equip_message(item.name)

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if add_message:
            self.unequip_message(current_item.name)

        setattr(self, slot, None)

    """ Gets called when the player selects an equippable item. It checks the equipment's type (to
        know which slot to put it in), and then checks to see if the same item is already equipped
        to that slot. If it is, the player presumably wants to remove it. If not, the player wants
        to equip it. """
    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        if (
            equippable_item.equippable
            and equippable_item.equippable.equipment_type == EquipmentType.WEAPON
        ):
            slot = "weapon"
        else:
            slot = "armor"

        if getattr(self, slot) == equippable_item:
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)
