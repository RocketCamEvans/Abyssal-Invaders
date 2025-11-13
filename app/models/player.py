"""
Player class for the dungeon crawler game.
"""

import uuid
from typing import Optional


class Player:
    """
    Represents a player in the dungeon crawler game.
    """
    
    def __init__(self, session_id: Optional[str] = None, name: str = "Unknown Adventurer"):
        self.session_id = session_id or str(uuid.uuid4())
        self.name = name
        self.health = 100
        self.max_health = 100
        self.gold = 0
        self.attack_power = 10
        self.defense = 5
        self.floor = 1
        self.room_id = "start"
        self.visited_rooms = set()
        self.allies = []  # List of ally objects that can help in combat
        self.inventory = []  # List of item objects
        
        # Battle state tracking
        self.in_battle = False
        self.current_enemy = None  # Current enemy data (dict)
        self.current_ally = None  # Current ally for this battle (if any)
        self.ally_used = False  # Whether ally has been used in current battle
        self.battle_room = None  # Room data where battle is taking place
        
    def take_damage(self, damage: int) -> bool:
        """
        Apply damage to the player.
        
        Args:
            damage (int): Amount of damage to apply
            
        Returns:
            bool: True if player is still alive, False if dead
        """
        actual_damage = max(0, damage - self.defense)
        self.health = max(0, self.health - actual_damage)
        return self.health > 0
    
    def heal(self, amount: int):
        """
        Heal the player.
        
        Args:
            amount (int): Amount of health to restore
        """
        self.health = min(self.max_health, self.health + amount)
    
    def add_gold(self, amount: int):
        """
        Add gold to the player's inventory.
        
        Args:
            amount (int): Amount of gold to add
        """
        self.gold += amount
    
    def add_ally(self, ally):
        """
        Add an ally to the player's party.
        
        Args:
            ally: Ally object to add
        """
        self.allies.append(ally)
    
    def add_item(self, item):
        """
        Add an item to the player's inventory.
        
        Args:
            item: Item object to add
        """
        self.inventory.append(item)
    
    def remove_item(self, item_id: str) -> Optional['Item']:
        """
        Remove an item from inventory by ID.
        
        Args:
            item_id (str): ID of the item to remove
            
        Returns:
            Optional[Item]: The removed item, or None if not found
        """
        for i, item in enumerate(self.inventory):
            if item.item_id == item_id:
                return self.inventory.pop(i)
        return None
    
    def get_item(self, item_id: str) -> Optional['Item']:
        """
        Get an item from inventory by ID.
        
        Args:
            item_id (str): ID of the item to get
            
        Returns:
            Optional[Item]: The item, or None if not found
        """
        for item in self.inventory:
            if item.item_id == item_id:
                return item
        return None
    
    def use_ally_attack(self, ally_index: int) -> Optional[int]:
        """
        Use an ally's attack (one-time use).
        
        Args:
            ally_index (int): Index of the ally to use
            
        Returns:
            Optional[int]: Damage dealt by the ally, or None if invalid
        """
        if 0 <= ally_index < len(self.allies):
            ally = self.allies.pop(ally_index)  # Remove after use
            return ally.attack_power
        return None
    
    def move_to_room(self, room_id: str):
        """
        Move the player to a new room.
        
        Args:
            room_id (str): ID of the room to move to
        """
        self.visited_rooms.add(self.room_id)
        self.room_id = room_id
    
    def go_to_next_floor(self):
        """
        Move the player to the next floor.
        """
        self.floor += 1
        self.room_id = "start"  # Reset to start room of new floor
        self.visited_rooms.clear()  # Clear visited rooms for new floor
    
    def is_alive(self) -> bool:
        """
        Check if the player is still alive.
        
        Returns:
            bool: True if alive, False if dead
        """
        return self.health > 0
    
    def start_battle(self, enemy_data: dict, room_data: dict, ally_data: Optional[dict] = None):
        """
        Start a new battle with an enemy.
        
        Args:
            enemy_data (dict): Enemy data dictionary
            room_data (dict): Room data dictionary
            ally_data (Optional[dict]): Ally data if present
        """
        self.in_battle = True
        self.current_enemy = enemy_data
        self.battle_room = room_data
        self.current_ally = ally_data
        self.ally_used = False
    
    def end_battle(self):
        """
        End the current battle and reset battle state.
        """
        self.in_battle = False
        self.current_enemy = None
        self.battle_room = None
        self.current_ally = None
        self.ally_used = False
    
    def flee_battle(self) -> int:
        """
        Flee from battle, losing half of current gold.
        
        Returns:
            int: Amount of gold lost
        """
        gold_lost = self.gold // 2
        self.gold -= gold_lost
        self.end_battle()
        return gold_lost
    
    def to_dict(self) -> dict:
        """
        Convert player to dictionary for JSON serialization.
        
        Returns:
            dict: Player data as dictionary
        """
        return {
            "session_id": self.session_id,
            "name": self.name,
            "health": self.health,
            "max_health": self.max_health,
            "gold": self.gold,
            "attack_power": self.attack_power,
            "defense": self.defense,
            "floor": self.floor,
            "room_id": self.room_id,
            "visited_rooms": list(self.visited_rooms),
            "allies": [ally.to_dict() for ally in self.allies],
            "inventory": [item.to_dict() for item in self.inventory],
            "in_battle": self.in_battle,
            "current_enemy": self.current_enemy,
            "current_ally": self.current_ally,
            "ally_used": self.ally_used,
            "battle_room": self.battle_room
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Player':
        """
        Create player from dictionary data.
        
        Args:
            data (dict): Player data dictionary
            
        Returns:
            Player: Player object created from data
        """
        from .ally import Ally  # Import here to avoid circular imports
        from .item import Item  # Import here to avoid circular imports
        
        player = cls(session_id=data["session_id"], name=data["name"])
        player.health = data["health"]
        player.max_health = data["max_health"]
        player.gold = data["gold"]
        player.attack_power = data["attack_power"]
        player.defense = data["defense"]
        player.floor = data["floor"]
        player.room_id = data["room_id"]
        player.visited_rooms = set(data["visited_rooms"])
        player.allies = [Ally.from_dict(ally_data) for ally_data in data["allies"]]
        player.inventory = [Item.from_dict(item_data) for item_data in data.get("inventory", [])]
        
        # Battle state (with defaults for backward compatibility)
        player.in_battle = data.get("in_battle", False)
        player.current_enemy = data.get("current_enemy", None)
        player.current_ally = data.get("current_ally", None)
        player.ally_used = data.get("ally_used", False)
        player.battle_room = data.get("battle_room", None)
        
        return player