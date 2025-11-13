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
        
        # Ensure floor is generated before accessing rooms
        self.ensure_floor_generated(player.floor)
        
        # Get the next room (should exist now due to floor generation)
        next_room = self.get_room(next_room_id, player.floor)
        if not next_room:
            # This should not happen with complete floor generation
            # Try to regenerate the complete floor to restore missing rooms with their staircases
            print(f"WARNING: Room {next_room_id} missing from floor {player.floor}, regenerating complete floor")
            self._regenerate_complete_floor(player.floor)
            next_room = self.get_room(next_room_id, player.floor)
            
            if not next_room:
                # Last resort: create a temporary room (this indicates a serious bug)
                print(f"ERROR: Could not restore room {next_room_id}, creating temporary room")
                next_room = self._generate_room(next_room_id, player.floor)
                self._save_room(next_room)
        
        # Ensure bidirectional connection exists for backtracking
        self._ensure_bidirectional_connection(current_room, next_room, normalized_direction, old_room_id, next_room_id)
        
        # Move player to the new room
        player.move_to_room(next_room_id)
        
        # DON'T mark room as visited yet - let the route handler check for encounters first
        # The room will be marked as visited in the route after encounter processing
        
        # Save both rooms (in case connections were updated)
        self._save_room(current_room)
        self._save_room(next_room)
        
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
        
        # Ensure the new floor is completely generated with guaranteed staircase
        self.ensure_floor_generated(player.floor)
        
        # Get the starting room for new floor (should exist now)
        start_room = self.get_room("start", player.floor)
        
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
        
        # Try to load from database first to ensure we have latest data
        room_data = self.room_db.get_room(room_id, floor)
        if room_data:
            room = Room.from_dict(room_data)
            # Update cache with fresh data
            self.room_cache[cache_key] = room
            return room
        
        # Check cache as fallback if not in database
        if cache_key in self.room_cache:
            return self.room_cache[cache_key]
        
        return None
    
    def get_room_for_session(self, room_id: str, floor: int, player_session: str = None) -> Optional[Room]:
        """
        Get a room for a specific player session, creating session-specific layouts.
        
        Args:
            room_id (str): Room ID
            floor (int): Floor number  
            player_session (str): Player session ID
            
        Returns:
            Optional[Room]: Room object or None if not found
        """
        if not player_session:
            return self.get_room(room_id, floor)
        
        # Create session-specific floor key
        session_floor_key = f"{floor}_session_{player_session[:8]}"  # Use first 8 chars of session
        cache_key = f"{session_floor_key}_{room_id}"
        
        # Try to load from database with session-specific key
        room_data = self.room_db.get_room(f"{room_id}_session_{player_session[:8]}", floor)
        if room_data:
            room = Room.from_dict(room_data)
            # Update room_id to remove session suffix for consistency
            room.room_id = room_id
            self.room_cache[cache_key] = room
            return room
        
        # Check cache as fallback
        if cache_key in self.room_cache:
            return self.room_cache[cache_key]
        
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
        
        # Save to database first
        success = self.room_db.save_room(room.room_id, room.floor, room.to_dict())
        
        if success:
            # Update cache only if database save succeeded
            self.room_cache[cache_key] = room
            
        return success
    
    def _save_room_for_session(self, room: Room, player_session: str = None) -> bool:
        """
        Save room with session-specific identifier.
        
        Args:
            room (Room): Room to save
            player_session (str): Player session ID
            
        Returns:
            bool: True if successful
        """
        if not player_session:
            return self._save_room(room)
        
        # Create session-specific room ID for storage
        session_room_id = f"{room.room_id}_session_{player_session[:8]}"
        session_floor_key = f"{room.floor}_session_{player_session[:8]}"
        
        # Save to database with session-specific ID
        success = self.room_db.save_room(session_room_id, room.floor, room.to_dict())
        
        if success:
            # Update cache with session-specific key
            cache_key = f"{session_floor_key}_{room.room_id}"
            self.room_cache[cache_key] = room
            
        return success
    
    def clear_room_cache(self, floor: int = None):
        """
        Clear room cache for a specific floor or all floors.
        
        Args:
            floor (int, optional): Floor to clear cache for, or None for all floors
        """
        if floor is None:
            self.room_cache.clear()
        else:
            keys_to_remove = [k for k in self.room_cache.keys() if k.startswith(f"{floor}_")]
            for key in keys_to_remove:
                del self.room_cache[key]
    
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
        
        # Set encounter chance based on floor - ensure it's always set with fallback
        try:
            from ..utils.helpers import calculate_encounter_chance
            encounter_chance = calculate_encounter_chance(floor)
        except Exception as e:
            print(f"WARNING: Could not calculate encounter chance: {e}, using default")
            # Fallback encounter chance: 0.3 base + 0.05 per floor, capped at 0.7
            encounter_chance = min(0.3 + (floor * 0.05), 0.7)
        
        room.set_encounter_chance(encounter_chance)
        print(f"[Room Generation] Created room {room_id} on floor {floor} with encounter_chance={room.encounter_chance}")
        
        # Note: Staircases are now placed strategically in _generate_complete_floor
        # No random staircase placement in individual room generation
        
        # Randomly add ally (8% chance, but not in starting room)
        if room_id != "start" and random.random() < 0.08:
            try:
                ally_data = self._generate_room_ally(floor)
                room.set_ally(ally_data)
            except Exception as e:
                print(f"WARNING: Could not generate ally: {e}")
        
        # Generate connections to other rooms
        self._generate_room_connections(room)
        
        return room
    
    def _generate_complete_floor(self, floor: int) -> Dict[str, Room]:
        """
        Generate a complete finite floor with guaranteed staircase.
        
        Args:
            floor (int): Floor number to generate
            
        Returns:
            Dict[str, Room]: Dictionary of room_id -> Room objects
        """
        # Add more randomization with time-based seeding
        import time
        time_seed = int(time.time() * 1000) % 1000000  # Use millisecond timestamp
        random.seed(time_seed)
        
        # Determine floor size (20-100 rooms) with more variation
        floor_size = random.randint(15, 120)  # Wider range for more variety
        rooms = {}
        
        # Create start room
        start_room = self._generate_start_room(floor)
        rooms["start"] = start_room
        
        # Generate all other rooms
        room_ids = ["start"]  # Track all room IDs for connections
        
        # Generate additional rooms
        for _ in range(floor_size - 1):
            room_id = generate_room_id(floor)
            while room_id in rooms:  # Ensure unique IDs
                room_id = generate_room_id(floor)
            
            new_room = self._generate_room(room_id, floor)
            rooms[room_id] = new_room
            room_ids.append(room_id)
        
        # Ensure all rooms are connected in a web
        self._connect_floor_rooms(rooms, room_ids)
        
        # Place exactly one staircase randomly (not in start room)
        non_start_rooms = [rid for rid in room_ids if rid != "start"]
        staircase_room_id = random.choice(non_start_rooms)
        rooms[staircase_room_id].set_staircase(True)
        
        # Reset random seed to avoid affecting other random operations
        random.seed()
        
        return rooms
    
    def _connect_floor_rooms(self, rooms: Dict[str, Room], room_ids: list):
        """
        Connect rooms to ensure the floor is fully traversable.
        
        Args:
            rooms (Dict[str, Room]): Dictionary of rooms
            room_ids (list): List of all room IDs
        """
        # First, create a minimum spanning tree to ensure all rooms are reachable
        connected = {"start"}  # Start with the start room
        unconnected = set(room_ids[1:])  # All other rooms
        
        directions = ['north', 'south', 'east', 'west']
        opposite_dirs = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
        
        # Connect each unconnected room to the growing connected component
        while unconnected:
            # Pick a random connected room and a random unconnected room
            from_room_id = random.choice(list(connected))
            to_room_id = random.choice(list(unconnected))
            
            # Pick a random direction
            direction = random.choice(directions)
            
            # Check if the from_room already has a connection in this direction
            from_room = rooms[from_room_id]
            if from_room.get_connection(direction) is None:
                # Create bidirectional connection
                from_room.add_connection(direction, to_room_id)
                to_room = rooms[to_room_id]
                to_room.add_connection(opposite_dirs[direction], from_room_id)
                
                # Move to_room to connected set
                connected.add(to_room_id)
                unconnected.remove(to_room_id)
        
        # Add some additional random connections for more interesting exploration
        for room_id in room_ids:
            room = rooms[room_id]
            available_dirs = [d for d in directions if room.get_connection(d) is None]
            
            # 30% chance to add an extra connection if directions are available
            if available_dirs and random.random() < 0.3:
                direction = random.choice(available_dirs)
                # Try to connect to another room (avoid creating isolated loops)
                potential_targets = [rid for rid in room_ids if rid != room_id]
                if potential_targets:
                    target_room_id = random.choice(potential_targets)
                    target_room = rooms[target_room_id]
                    opposite_dir = opposite_dirs[direction]
                    
                    # Only create connection if target room can accept it
                    if target_room.get_connection(opposite_dir) is None:
                        room.add_connection(direction, target_room_id)
                        target_room.add_connection(opposite_dir, room_id)
    
    def ensure_floor_generated(self, floor: int):
        """
        Ensure a complete floor is generated and stored.
        
        Args:
            floor (int): Floor number to ensure is generated
        """
        # Check if floor already has rooms generated
        start_room = self.get_room("start", floor)
        if start_room:
            # Floor already exists, check if it has a staircase somewhere
            if not self._floor_has_staircase(floor):
                self._add_staircase_to_floor(floor)
            return
        
        # Generate complete floor
        floor_rooms = self._generate_complete_floor(floor)
        
        # Save all rooms to database
        for room in floor_rooms.values():
            self._save_room(room)
    
    def generate_new_floor_for_session(self, floor: int, player_session: str):
        """
        Force generation of a new unique floor for a player session.
        This clears existing floor data and creates a new layout.
        
        Args:
            floor (int): Floor number to generate
            player_session (str): Player session ID for seeding randomization
        """
        # Clear existing floor data
        self._clear_floor_data(floor)
        
        # Use session ID to seed randomization for unique but consistent layouts
        import hashlib
        session_seed = int(hashlib.md5(f"{floor}_{player_session}".encode()).hexdigest()[:8], 16)
        random.seed(session_seed)
        
        # Generate complete floor
        floor_rooms = self._generate_complete_floor(floor)
        
        # Reset random seed after generation
        random.seed()
        
        # Save all rooms to database
        for room in floor_rooms.values():
            self._save_room(room)
    
    def _clear_floor_data(self, floor: int):
        """
        Clear all room data for a specific floor.
        
        Args:
            floor (int): Floor number to clear
        """
        # Clear cache for this floor
        self.clear_room_cache(floor)
        
        # Clear database data for this floor
        floor_rooms = self.room_db.get_floor_rooms(floor)
        for room_id in floor_rooms.keys():
            # Delete each room from the database
            # Note: This is a simplified approach - in production you'd want batch operations
            pass  # The room_db doesn't have a delete method, so we'll just overwrite
    
    def _floor_has_staircase(self, floor: int) -> bool:
        """
        Check if a floor has any staircase.
        
        Args:
            floor (int): Floor number to check
            
        Returns:
            bool: True if floor has at least one staircase
        """
        # This is a simple check - in a real implementation you'd query the database
        # For now, we'll assume floors generated by _generate_complete_floor have staircases
        return True
    
    def _add_staircase_to_floor(self, floor: int):
        """
        Add a staircase to a floor that doesn't have one.
        
        Args:
            floor (int): Floor number to add staircase to
        """
        # Find a random room on the floor (not start) and add staircase
        # This is a fallback for legacy floors
        rooms_on_floor = self._get_all_rooms_on_floor(floor)
        non_start_rooms = [r for r in rooms_on_floor if r.room_id != "start"]
        
        if non_start_rooms:
            chosen_room = random.choice(non_start_rooms)
            chosen_room.set_staircase(True)
            self._save_room(chosen_room)
    
    def _regenerate_complete_floor(self, floor: int):
        """
        Regenerate a complete floor, preserving any existing room visit states.
        This is used when rooms go missing from a floor.
        
        Args:
            floor (int): Floor number to regenerate
        """
        # Get any existing rooms to preserve their visited state
        existing_rooms = {}
        try:
            # Try to find any existing rooms on this floor
            start_room = self.get_room("start", floor)
            if start_room:
                existing_rooms["start"] = start_room
        except:
            pass
        
        # Clear the floor cache for this floor
        keys_to_remove = [k for k in self.room_cache.keys() if k.startswith(f"{floor}_")]
        for key in keys_to_remove:
            del self.room_cache[key]
        
        # Generate new complete floor
        floor_rooms = self._generate_complete_floor(floor)
        
        # Preserve visit states from existing rooms
        for room_id, new_room in floor_rooms.items():
            if room_id in existing_rooms:
                old_room = existing_rooms[room_id]
                new_room.has_been_visited = old_room.has_been_visited
        
        # Save all rooms to database
        for room in floor_rooms.values():
            self._save_room(room)
    
    def _regenerate_complete_floor_for_session(self, floor: int, player_session: str = None):
        """
        Regenerate a complete floor for a specific session.
        
        Args:
            floor (int): Floor number to regenerate
            player_session (str): Player session ID
        """
        if not player_session:
            return self._regenerate_complete_floor(floor)
        
        # Clear the floor cache for this session
        session_floor_key = f"{floor}_session_{player_session[:8]}"
        keys_to_remove = [k for k in self.room_cache.keys() if k.startswith(f"{session_floor_key}_")]
        for key in keys_to_remove:
            del self.room_cache[key]
        
        # Generate new complete floor with session-specific seed
        import hashlib
        session_seed = int(hashlib.md5(f"{floor}_{player_session}".encode()).hexdigest()[:8], 16)
        random.seed(session_seed)
        
        floor_rooms = self._generate_complete_floor(floor)
        
        # Reset random seed
        random.seed()
        
        # Save all rooms to database with session-specific keys
        for room in floor_rooms.values():
            self._save_room_for_session(room, player_session)
    
    def _get_all_rooms_on_floor(self, floor: int) -> list:
        """
        Get all rooms on a specific floor.
        
        Args:
            floor (int): Floor number
            
        Returns:
            list: List of Room objects on the floor
        """
        # This would need to be implemented based on your database structure
        # For now, return empty list as this is a helper for legacy support
        return []
    
    def _generate_room_ally(self, floor: int) -> Dict[str, Any]:
        """
        Generate ally data for a room.
        
        Args:
            floor (int): Floor number for scaling
            
        Returns:
            Dict[str, Any]: Ally data
        """
        # Import here to avoid circular imports
        from .generation import GenerationController
        
        generation_controller = GenerationController()
        ally_content = generation_controller.generate_ally_content(floor)
        
        # Create ally data with stats scaled to floor
        ally_data = {
            'name': ally_content['name'],
            'description': ally_content['description'],
            'attack_power': 10 + (floor * 2),  # Scales with floor
            'floor': floor
        }
        
        return ally_data
    
    def _generate_start_room(self, floor: int) -> Room:
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
        
        # Note: Connections will be set up in _connect_floor_rooms during complete floor generation
        # Don't generate connections here as they need to be coordinated with the full floor layout
        
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
        
        Note: We do NOT force-regenerate floors for new players because that would
        destroy the floor layout for existing players and break backtracking.
        Floors are generated once per server session and shared by all players.
        
        Args:
            player (Player): New player object
            
        Returns:
            Room: Starting room
        """
        # Ensure complete floor is generated (only generates if not already present)
        self.ensure_floor_generated(player.floor)
        
        # Get the start room from the generated floor
        start_room = self.get_room("start", player.floor)
        if not start_room:
            # This should not happen with the new finite floor system, but fallback just in case
            start_room = self._generate_start_room(player.floor)
            self._save_room(start_room)
        
        return start_room
    
    def _force_regenerate_floor(self, floor: int):
        """
        Force regeneration of a specific floor by clearing existing data.
        
        Args:
            floor (int): Floor number to regenerate
        """
        # Clear room cache for this floor
        self.clear_room_cache(floor)
        
        # Generate new floor layout 
        floor_rooms = self._generate_complete_floor(floor)
        
        # Save all new rooms to database (this overwrites existing data)
        for room in floor_rooms.values():
            self._save_room(room)
    
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