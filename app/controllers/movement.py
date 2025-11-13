"""
Movement controller for handling player movement between rooms.
"""

from typing import Optional, Tuple, Dict, Any
from ..models import Player, Room
from ..utils import RoomDB, validate_direction, create_error_response, create_success_response
from ..utils.helpers import generate_room_id, get_random_room_names, get_random_room_descriptions
import random


class MovementController:
    """
    Handles player movement between rooms and room generation.
    """
    
    def __init__(self, room_db: Optional[RoomDB] = None):
        """
        Initialize the movement controller.
        
        Args:
            room_db (Optional[RoomDB]): Room database instance
        """
        self.room_db = room_db or RoomDB()
        self.room_cache = {}  # Cache rooms in memory for current session
    
    def move_player(self, player: Player, direction: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Move player in the specified direction.
        
        Args:
            player (Player): Player object
            direction (str): Direction to move ('north', 'south', 'east', 'west', 'up')
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (Success, Response data)
        """
        # Validate direction
        normalized_direction = validate_direction(direction)
        if not normalized_direction:
            return False, create_error_response("Invalid direction. Use north, south, east, west, or up (for stairs).")
        
        # Handle staircase (up direction)
        if normalized_direction == 'up':
            return self._handle_staircase(player)
        
        # Get current room
        current_room = self.get_room(player.room_id, player.floor)
        if not current_room:
            return False, create_error_response("Current room not found. Something went wrong!")
        
        # Check if movement direction is valid
        next_room_id = current_room.get_connection(normalized_direction)
        if not next_room_id:
            return False, create_error_response(f"You cannot go {direction} from here.")
        
        # Store current room ID before moving
        old_room_id = player.room_id
        
        # Get or create the next room
        next_room = self.get_room(next_room_id, player.floor)
        if not next_room:
            next_room = self._generate_room(next_room_id, player.floor)
            self._save_room(next_room)
        
        # Ensure bidirectional connection exists for backtracking
        self._ensure_bidirectional_connection(current_room, next_room, normalized_direction, old_room_id, next_room_id)
        
        # Move player to the new room
        player.move_to_room(next_room_id)
        
        # DON'T mark room as visited yet - let the route handler check for encounters first
        # The room will be marked as visited in the route after encounter processing
        
        # Save the current room (in case connections were updated)
        self._save_room(current_room)
        
        # Prepare response
        response_data = {
            "moved_from": old_room_id,
            "moved_to": next_room_id,
            "direction": normalized_direction,
            "room_info": next_room.get_room_info(),
            "player_stats": {
                "floor": player.floor,
                "room_id": player.room_id,
                "health": f"{player.health}/{player.max_health}",
                "gold": player.gold
            },
            # Add debug info
            "debug": {
                "room_was_new": not next_room.has_been_visited,
                "encounter_chance": next_room.encounter_chance,
                "has_staircase": next_room.has_staircase
            }
        }
        
        return True, create_success_response(response_data, f"Moved {direction} to {next_room.name}")
    
    def _handle_staircase(self, player: Player) -> Tuple[bool, Dict[str, Any]]:
        """
        Handle player using staircase to go to next floor.
        
        Args:
            player (Player): Player object
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (Success, Response data)
        """
        current_room = self.get_room(player.room_id, player.floor)
        if not current_room or not current_room.has_staircase:
            return False, create_error_response("There is no staircase here.")
        
        # Move player to next floor
        old_floor = player.floor
        player.go_to_next_floor()
        
        # Get or create starting room for new floor
        start_room = self.get_room("start", player.floor)
        if not start_room:
            start_room = self._generate_starting_room(player.floor)
            self._save_room(start_room)
        
        response_data = {
            "moved_from_floor": old_floor,
            "moved_to_floor": player.floor,
            "room_info": start_room.get_room_info(),
            "player_stats": {
                "floor": player.floor,
                "room_id": player.room_id,
                "health": f"{player.health}/{player.max_health}",
                "gold": player.gold
            }
        }
        
        return True, create_success_response(response_data, f"You ascend to floor {player.floor}!")
    
    def get_room(self, room_id: str, floor: int) -> Optional[Room]:
        """
        Get a room by ID and floor, checking cache first.
        
        Args:
            room_id (str): Room ID
            floor (int): Floor number
            
        Returns:
            Optional[Room]: Room object or None if not found
        """
        cache_key = f"{floor}_{room_id}"
        
        # Check cache first
        if cache_key in self.room_cache:
            return self.room_cache[cache_key]
        
        # Try to load from database
        room_data = self.room_db.get_room(room_id, floor)
        if room_data:
            room = Room.from_dict(room_data)
            self.room_cache[cache_key] = room
            return room
        
        return None
    
    def _save_room(self, room: Room) -> bool:
        """
        Save room to database and update cache.
        
        Args:
            room (Room): Room to save
            
        Returns:
            bool: True if successful
        """
        cache_key = f"{room.floor}_{room.room_id}"
        self.room_cache[cache_key] = room
        return self.room_db.save_room(room.room_id, room.floor, room.to_dict())
    
    def _generate_room(self, room_id: str, floor: int) -> Room:
        """
        Generate a new room with random properties.
        
        Args:
            room_id (str): Room ID
            floor (int): Floor number
            
        Returns:
            Room: Generated room
        """
        # Generate random name and description
        # In a real implementation, this would call the LLM generation service
        room_names = get_random_room_names()
        room_descriptions = get_random_room_descriptions()
        
        name = random.choice(room_names)
        description = random.choice(room_descriptions)
        
        # Create room
        room = Room(room_id=room_id, name=name, description=description, floor=floor)
        
        # Set encounter chance based on floor
        from ..utils.helpers import calculate_encounter_chance
        room.set_encounter_chance(calculate_encounter_chance(floor))
        
        # Randomly add staircase (15% chance, but not in starting room)
        if room_id != "start" and random.random() < 0.15:
            room.set_staircase(True)
        
        # Generate connections to other rooms
        self._generate_room_connections(room)
        
        return room
    
    def _generate_starting_room(self, floor: int) -> Room:
        """
        Generate the starting room for a floor.
        
        Args:
            floor (int): Floor number
            
        Returns:
            Room: Starting room
        """
        name = f"Floor {floor} Entrance"
        description = f"You find yourself at the entrance to floor {floor}. The air feels different here, charged with mysterious energy."
        
        room = Room(room_id="start", name=name, description=description, floor=floor)
        room.set_encounter_chance(0.1)  # Lower encounter chance in starting room
        
        # Generate connections
        self._generate_room_connections(room)
        
        return room
    
    def _generate_room_connections(self, room: Room):
        """
        Generate random connections for a room.
        
        Args:
            room (Room): Room to generate connections for
        """
        directions = ['north', 'south', 'east', 'west']
        
        # Generate 1-3 connections randomly
        num_connections = random.randint(1, 3)
        selected_directions = random.sample(directions, num_connections)
        
        for direction in selected_directions:
            # Generate room ID for this direction using just a simple random ID
            # This prevents the exponential growth of room IDs
            connected_room_id = generate_room_id(room.floor)
            room.add_connection(direction, connected_room_id)
    
    def get_available_moves(self, player: Player) -> Dict[str, Any]:
        """
        Get available movement options for the player.
        
        Args:
            player (Player): Player object
            
        Returns:
            Dict[str, Any]: Available movement information
        """
        current_room = self.get_room(player.room_id, player.floor)
        if not current_room:
            return create_error_response("Current room not found.")
        
        available_directions = current_room.get_available_directions()
        
        response_data = {
            "room_info": current_room.get_room_info(),
            "available_directions": available_directions,
            "has_staircase": current_room.has_staircase,
            "can_go_up": current_room.has_staircase
        }
        
        return create_success_response(response_data, "Available movement options")
    
    def initialize_player_room(self, player: Player) -> Room:
        """
        Initialize the starting room for a new player.
        
        Args:
            player (Player): New player object
            
        Returns:
            Room: Starting room
        """
        start_room = self.get_room("start", player.floor)
        if not start_room:
            start_room = self._generate_starting_room(player.floor)
            self._save_room(start_room)
        
        return start_room
    
    def _get_opposite_direction(self, direction: str) -> str:
        """
        Get the opposite direction for bidirectional connections.
        
        Args:
            direction (str): Original direction
            
        Returns:
            str: Opposite direction
        """
        opposite_map = {
            'north': 'south',
            'south': 'north',
            'east': 'west',
            'west': 'east'
        }
        return opposite_map.get(direction, direction)
    
    def _ensure_bidirectional_connection(self, current_room: Room, next_room: Room, 
                                       direction: str, current_room_id: str, next_room_id: str):
        """
        Ensure that both rooms have connections to each other for backtracking.
        
        Args:
            current_room (Room): The room the player is leaving
            next_room (Room): The room the player is entering
            direction (str): Direction of movement
            current_room_id (str): ID of the current room
            next_room_id (str): ID of the next room
        """
        opposite_direction = self._get_opposite_direction(direction)
        
        # Check if the next room already has a connection back to the current room
        existing_connection = next_room.get_connection(opposite_direction)
        
        if not existing_connection:
            # Add the reverse connection
            next_room.add_connection(opposite_direction, current_room_id)