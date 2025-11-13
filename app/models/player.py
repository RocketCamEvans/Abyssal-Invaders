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
            "allies": [ally.to_dict() for ally in self.allies]
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
        return player