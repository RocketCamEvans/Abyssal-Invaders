"""
Room class for the dungeon crawler game.
"""

import random
from typing import Dict, Optional, List


class Room:
    """
    Represents a room in the dungeon crawler game.
    """
    
    def __init__(self, room_id: str, name: str = "", description: str = "", floor: int = 1):
        self.room_id = room_id
        self.name = name
        self.description = description
        self.floor = floor
        self.connections = {}  # Direction -> room_id mapping
        self.has_staircase = False
        self.encounter_chance = 0.3  # 30% chance of encounter
        self.has_been_visited = False
        self.ally_data = None  # Ally data if room contains an ally
        
    def add_connection(self, direction: str, room_id: str):
        """
        Add a connection to another room.
        
        Args:
            direction (str): Direction of connection ('north', 'south', 'east', 'west')
            room_id (str): ID of the connected room
        """
        valid_directions = ['north', 'south', 'east', 'west', 'n', 's', 'e', 'w']
        if direction.lower() in valid_directions:
            self.connections[direction.lower()] = room_id
    
    def get_connection(self, direction: str) -> Optional[str]:
        """
        Get the room ID connected in a given direction.
        
        Args:
            direction (str): Direction to check
            
        Returns:
            Optional[str]: Room ID if connection exists, None otherwise
        """
        # Normalize direction input
        direction_map = {
            'n': 'north', 'north': 'north',
            's': 'south', 'south': 'south',
            'e': 'east', 'east': 'east',
            'w': 'west', 'west': 'west'
        }
        
        normalized_direction = direction_map.get(direction.lower())
        return self.connections.get(normalized_direction)
    
    def get_available_directions(self) -> List[str]:
        """
        Get list of available directions from this room.
        
        Returns:
            List[str]: List of available direction names
        """
        return list(self.connections.keys())
    
    def set_staircase(self, has_staircase: bool = True):
        """
        Set whether this room has a staircase to the next floor.
        
        Args:
            has_staircase (bool): Whether room has staircase
        """
        self.has_staircase = has_staircase
    
    def set_ally(self, ally_data: Optional[Dict] = None):
        """
        Set ally data for this room.
        
        Args:
            ally_data (Optional[Dict]): Ally data or None to remove ally
        """
        self.ally_data = ally_data
    
    def has_ally(self) -> bool:
        """
        Check if this room has an ally.
        
        Returns:
            bool: True if room has ally, False otherwise
        """
        return self.ally_data is not None
    
    def take_ally(self) -> Optional[Dict]:
        """
        Take the ally from this room (one-time use).
        
        Returns:
            Optional[Dict]: Ally data if present, None otherwise
        """
        ally = self.ally_data
        self.ally_data = None  # Remove ally after taking
        return ally
    
    def roll_for_encounter(self) -> bool:
        """
        Roll to see if an encounter occurs in this room.
        
        Returns:
            bool: True if encounter occurs, False otherwise
        """
        # Don't have encounters on repeat visits to the same room
        if self.has_been_visited:
            return False
            
        return random.random() < self.encounter_chance
    
    def visit(self):
        """
        Mark this room as visited.
        """
        self.has_been_visited = True
    
    def set_encounter_chance(self, chance: float):
        """
        Set the encounter chance for this room.
        
        Args:
            chance (float): Encounter chance between 0.0 and 1.0
        """
        self.encounter_chance = max(0.0, min(1.0, chance))
    
    def to_dict(self) -> dict:
        """
        Convert room to dictionary for JSON serialization.
        
        Returns:
            dict: Room data as dictionary
        """
        return {
            "room_id": self.room_id,
            "name": self.name,
            "description": self.description,
            "floor": self.floor,
            "connections": self.connections,
            "has_staircase": self.has_staircase,
            "encounter_chance": self.encounter_chance,
            "has_been_visited": self.has_been_visited,
            "ally_data": self.ally_data
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Room':
        """
        Create room from dictionary data.
        
        Args:
            data (dict): Room data dictionary
            
        Returns:
            Room: Room object created from data
        """
        room = cls(
            room_id=data["room_id"],
            name=data["name"],
            description=data["description"],
            floor=data["floor"]
        )
        room.connections = data["connections"]
        room.has_staircase = data["has_staircase"]
        room.encounter_chance = data["encounter_chance"]
        room.has_been_visited = data["has_been_visited"]
        room.ally_data = data.get("ally_data", None)  # Backward compatibility
        return room
    
    def get_room_info(self) -> dict:
        """
        Get basic room information for API responses.
        
        Returns:
            dict: Basic room information
        """
        return {
            "room_id": self.room_id,
            "name": self.name,
            "description": self.description,
            "floor": self.floor,
            "available_directions": self.get_available_directions(),
            "has_staircase": self.has_staircase,
            "has_ally": self.has_ally(),
            "ally_name": self.ally_data.get('name') if self.ally_data else None
        }