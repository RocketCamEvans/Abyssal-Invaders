"""
Item class for the dungeon crawler game.
"""

from typing import Optional
import uuid


class Item:
    """
    Represents an item that can be found and used by players.
    """
    
    # Item types and their effects
    ITEM_TYPES = {
        "health_potion": {
            "name": "Health Potion",
            "description": "Restores health when used",
            "effect_type": "heal",
            "effect_value": 30,
            "usable_in_combat": True,
            "rarity": "common"
        },
        "greater_health_potion": {
            "name": "Greater Health Potion",
            "description": "Restores a large amount of health",
            "effect_type": "heal",
            "effect_value": 60,
            "usable_in_combat": True,
            "rarity": "uncommon"
        },
        "attack_boost": {
            "name": "Attack Elixir",
            "description": "Temporarily increases attack power for one battle",
            "effect_type": "attack_boost",
            "effect_value": 15,
            "usable_in_combat": True,
            "rarity": "uncommon"
        },
        "defense_boost": {
            "name": "Iron Skin Tonic",
            "description": "Temporarily increases defense for one battle",
            "effect_type": "defense_boost",
            "effect_value": 10,
            "usable_in_combat": True,
            "rarity": "uncommon"
        },
        "damage_bomb": {
            "name": "Explosive Bomb",
            "description": "Deals direct damage to enemy",
            "effect_type": "damage",
            "effect_value": 40,
            "usable_in_combat": True,
            "rarity": "rare"
        },
        "poison_vial": {
            "name": "Poison Vial",
            "description": "Deals damage over time to enemy",
            "effect_type": "damage",
            "effect_value": 25,
            "usable_in_combat": True,
            "rarity": "uncommon"
        },
        "escape_scroll": {
            "name": "Scroll of Escape",
            "description": "Guarantees successful flee from combat",
            "effect_type": "guaranteed_flee",
            "effect_value": 0,
            "usable_in_combat": True,
            "rarity": "rare"
        },
        "gold_coin_bag": {
            "name": "Bag of Gold Coins",
            "description": "Contains extra gold",
            "effect_type": "gold",
            "effect_value": 50,
            "usable_in_combat": False,
            "rarity": "common"
        }
    }
    
    def __init__(self, item_type: str, item_id: Optional[str] = None):
        """
        Initialize an item.
        
        Args:
            item_type (str): Type of item (must be in ITEM_TYPES)
            item_id (Optional[str]): Unique identifier for this item instance
        """
        if item_type not in self.ITEM_TYPES:
            raise ValueError(f"Invalid item type: {item_type}")
        
        self.item_id = item_id or str(uuid.uuid4())
        self.item_type = item_type
        
        # Load item properties from ITEM_TYPES
        item_data = self.ITEM_TYPES[item_type]
        self.name = item_data["name"]
        self.description = item_data["description"]
        self.effect_type = item_data["effect_type"]
        self.effect_value = item_data["effect_value"]
        self.usable_in_combat = item_data["usable_in_combat"]
        self.rarity = item_data["rarity"]
    
    def use(self, player, enemy=None):
        """
        Use the item and apply its effect.
        
        Args:
            player: Player object to apply effects to
            enemy: Enemy object (required for damage/poison effects)
            
        Returns:
            dict: Result of using the item
        """
        result = {
            "item_name": self.name,
            "effect_type": self.effect_type,
            "success": True,
            "message": ""
        }
        
        if self.effect_type == "heal":
            old_health = player.health
            player.heal(self.effect_value)
            healed = player.health - old_health
            result["message"] = f"Used {self.name} and restored {healed} health!"
            result["healed"] = healed
            
        elif self.effect_type == "attack_boost":
            player.attack_power += self.effect_value
            player.temp_attack_boost += self.effect_value
            result["message"] = f"Used {self.name}! Attack power increased by {self.effect_value}!"
            result["attack_boost"] = self.effect_value
            
        elif self.effect_type == "defense_boost":
            player.defense += self.effect_value
            player.temp_defense_boost += self.effect_value
            result["message"] = f"Used {self.name}! Defense increased by {self.effect_value}!"
            result["defense_boost"] = self.effect_value
            
        elif self.effect_type == "damage":
            if enemy:
                enemy.take_damage(self.effect_value)
                result["message"] = f"Used {self.name} and dealt {self.effect_value} damage to {enemy.name}!"
                result["damage_dealt"] = self.effect_value
            else:
                result["success"] = False
                result["message"] = f"{self.name} can only be used during combat!"
                
        elif self.effect_type == "guaranteed_flee":
            result["message"] = f"Used {self.name}! Flee is now guaranteed!"
            result["guaranteed_flee"] = True
            
        elif self.effect_type == "gold":
            player.add_gold(self.effect_value)
            result["message"] = f"Used {self.name} and gained {self.effect_value} gold!"
            result["gold_gained"] = self.effect_value
        
        return result
    
    def get_item_info(self) -> dict:
        """
        Get item information for display.
        
        Returns:
            dict: Item information
        """
        return {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "effect_type": self.effect_type,
            "effect_value": self.effect_value,
            "usable_in_combat": self.usable_in_combat,
            "rarity": self.rarity
        }
    
    def to_dict(self) -> dict:
        """
        Convert item to dictionary for JSON serialization.
        
        Returns:
            dict: Item data as dictionary
        """
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "name": self.name,
            "description": self.description,
            "effect_type": self.effect_type,
            "effect_value": self.effect_value,
            "usable_in_combat": self.usable_in_combat,
            "rarity": self.rarity
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Item':
        """
        Create item from dictionary data.
        
        Args:
            data (dict): Item data dictionary
            
        Returns:
            Item: Item object created from data
        """
        return cls(
            item_type=data["item_type"],
            item_id=data["item_id"]
        )
    
    @classmethod
    def get_random_item_type(cls, floor: int = 1) -> str:
        """
        Get a random item type based on rarity weights adjusted by floor.
        
        Args:
            floor (int): Current floor level (affects rarity)
            
        Returns:
            str: Random item type
        """
        import random
        
        # Rarity weights (higher floor = better items)
        rarity_weights = {
            "common": max(1, 10 - floor),      # Common items become less frequent
            "uncommon": 5 + (floor // 2),      # Uncommon items scale moderately
            "rare": floor                      # Rare items scale with floor
        }
        
        # Build weighted list of item types
        weighted_items = []
        for item_type, item_data in cls.ITEM_TYPES.items():
            rarity = item_data["rarity"]
            weight = rarity_weights.get(rarity, 1)
            weighted_items.extend([item_type] * weight)
        
        return random.choice(weighted_items)
