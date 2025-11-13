"""
Inventory controller for managing player items.
"""

from typing import Dict, Any, Tuple, Optional
from ..models import Player, Item, Enemy
from ..utils import create_error_response, create_success_response
import random


class InventoryController:
    """
    Handles inventory management including item finding, usage, and management.
    """
    
    # Chance to find an item when moving (if no encounter)
    BASE_ITEM_FIND_CHANCE = 0.65  # 65% chance to find an item
    
    def __init__(self):
        """
        Initialize the inventory controller.
        """
        pass
    
    def roll_for_item_find(self, player: Player, room_visited: bool) -> Tuple[bool, Optional[Item]]:
        """
        Determine if player finds an item when entering a room.
        
        Args:
            player (Player): Player object
            room_visited (bool): Whether the room has been visited before
            
        Returns:
            Tuple[bool, Optional[Item]]: (Found item?, Item object if found)
        """
        # Don't find items in already visited rooms
        if room_visited:
            return False, None
        
        # Roll for item find
        if random.random() < self.BASE_ITEM_FIND_CHANCE:
            item_type = Item.get_random_item_type(player.floor)
            item = Item(item_type)
            return True, item
        
        return False, None
    
    def add_item_to_inventory(self, player: Player, item: Item) -> Dict[str, Any]:
        """
        Add an item to player's inventory.
        
        Args:
            player (Player): Player object
            item (Item): Item to add
            
        Returns:
            Dict[str, Any]: Response data
        """
        player.add_item(item)
        
        response_data = {
            "item_added": item.get_item_info(),
            "inventory_size": len(player.inventory),
            "message": f"Found {item.name}!"
        }
        
        return create_success_response(response_data, f"Found {item.name}!")
    
    def use_item(self, player: Player, item_id: str, enemy: Optional[Enemy] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Use an item from player's inventory.
        
        Args:
            player (Player): Player object
            item_id (str): ID of the item to use
            enemy (Optional[Enemy]): Enemy object if in combat
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (Success, Response data)
        """
        # Find the item in inventory
        item = player.get_item(item_id)
        if not item:
            return False, create_error_response("Item not found in inventory")
        
        # Check if item can be used in current context
        if player.in_battle and not item.usable_in_combat:
            return False, create_error_response(f"{item.name} cannot be used during combat")
        
        # Use the item
        use_result = item.use(player, enemy)
        
        if use_result["success"]:
            # Remove item from inventory after use
            player.remove_item(item_id)
            
            response_data = {
                "item_used": item.get_item_info(),
                "use_result": use_result,
                "inventory_size": len(player.inventory),
                "player_stats": {
                    "health": f"{player.health}/{player.max_health}",
                    "attack_power": player.attack_power,
                    "defense": player.defense,
                    "gold": player.gold
                }
            }
            
            # Add enemy stats if in combat
            if enemy:
                response_data["enemy_stats"] = {
                    "name": enemy.name,
                    "health": f"{enemy.health}/{enemy.max_health}"
                }
            
            return True, create_success_response(response_data, use_result["message"])
        else:
            return False, create_error_response(use_result["message"])
    
    def get_inventory(self, player: Player) -> Dict[str, Any]:
        """
        Get player's current inventory.
        
        Args:
            player (Player): Player object
            
        Returns:
            Dict[str, Any]: Response data with inventory
        """
        inventory_items = [item.get_item_info() for item in player.inventory]
        
        # Group items by type for easier viewing
        grouped_inventory = {}
        for item_info in inventory_items:
            item_type = item_info["name"]
            if item_type not in grouped_inventory:
                grouped_inventory[item_type] = []
            grouped_inventory[item_type].append(item_info)
        
        response_data = {
            "inventory": inventory_items,
            "grouped_inventory": grouped_inventory,
            "inventory_size": len(player.inventory),
            "total_items": len(player.inventory)
        }
        
        return create_success_response(response_data, "Inventory retrieved")
    
    def discard_item(self, player: Player, item_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Discard an item from inventory.
        
        Args:
            player (Player): Player object
            item_id (str): ID of the item to discard
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (Success, Response data)
        """
        item = player.remove_item(item_id)
        
        if item:
            response_data = {
                "item_discarded": item.get_item_info(),
                "inventory_size": len(player.inventory)
            }
            return True, create_success_response(response_data, f"Discarded {item.name}")
        else:
            return False, create_error_response("Item not found in inventory")
    
    def get_usable_combat_items(self, player: Player) -> list:
        """
        Get list of items that can be used in combat.
        
        Args:
            player (Player): Player object
            
        Returns:
            list: List of usable item info dicts
        """
        return [
            item.get_item_info() 
            for item in player.inventory 
            if item.usable_in_combat
        ]
