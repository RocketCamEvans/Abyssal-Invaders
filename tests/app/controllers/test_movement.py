"""
Unit tests for the MovementController class.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any

# Import the classes we need to test
from app.controllers.movement import MovementController
from app.models.player import Player
from app.models.room import Room
from app.utils.file_db import RoomDB


class TestMovementController:
    """Test cases for MovementController class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create mock RoomDB
        self.mock_room_db = Mock(spec=RoomDB)
        self.controller = MovementController(room_db=self.mock_room_db)
        
        # Create test player
        self.test_player = Player(session_id="test-session-123", name="Test Player")
        self.test_player.floor = 1
        self.test_player.room_id = "start"
        
        # Create test rooms
        self.start_room = Room(room_id="start", name="Starting Room", description="A basic starting room", floor=1)
        self.start_room.add_connection("north", "room_1")
        self.start_room.add_connection("east", "room_2")
        
        self.room_1 = Room(room_id="room_1", name="Northern Room", description="A room to the north", floor=1)
        self.room_1.add_connection("south", "start")
        
        self.room_2 = Room(room_id="room_2", name="Eastern Room", description="A room to the east", floor=1)
        self.room_2.add_connection("west", "start")
        self.room_2.set_staircase(True)
    
    def test_init_default_room_db(self):
        """Test initialization with default RoomDB."""
        controller = MovementController()
        assert controller.room_db is not None
        assert controller.room_cache == {}
        assert controller.current_session_id is None
    
    def test_init_with_custom_room_db(self):
        """Test initialization with custom RoomDB."""
        custom_db = Mock(spec=RoomDB)
        controller = MovementController(room_db=custom_db)
        assert controller.room_db is custom_db
    
    def test_set_session(self):
        """Test setting session ID."""
        session_id = "test-session-456"
        self.controller.set_session(session_id)
        assert self.controller.current_session_id == session_id
    
    def test_move_player_valid_direction(self):
        """Test moving player in a valid direction."""
        # Mock room database responses
        self.mock_room_db.get_room.side_effect = [
            self.start_room.to_dict(),  # Current room
            self.room_1.to_dict()       # Next room
        ]
        self.mock_room_db.save_room.return_value = True
        
        # Mock ensure_floor_generated
        with patch.object(self.controller, 'ensure_floor_generated'):
            success, response = self.controller.move_player(self.test_player, "north")
        
        assert success is True
        assert response["error"] is False
        assert response["message"] == "Moved north to Northern Room"
        assert response["data"]["moved_from"] == "start"
        assert response["data"]["moved_to"] == "room_1"
        assert response["data"]["direction"] == "north"
        assert self.test_player.room_id == "room_1"
    
    def test_move_player_invalid_direction(self):
        """Test moving player in an invalid direction."""
        success, response = self.controller.move_player(self.test_player, "invalid")
        
        assert success is False
        assert response["error"] is True
        assert "Invalid direction" in response["message"]
    
    def test_move_player_no_connection(self):
        """Test moving player in a direction with no connection."""
        # Mock room database to return start room without west connection
        self.mock_room_db.get_room.return_value = self.start_room.to_dict()
        
        with patch.object(self.controller, 'ensure_floor_generated'):
            success, response = self.controller.move_player(self.test_player, "west")
        
        assert success is False
        assert response["error"] is True
        assert "You cannot go west from here" in response["message"]
    
    def test_move_player_current_room_not_found(self):
        """Test moving player when current room is not found."""
        self.mock_room_db.get_room.return_value = None
        
        success, response = self.controller.move_player(self.test_player, "north")
        
        assert success is False
        assert response["error"] is True
        assert "Current room not found" in response["message"]
    
    def test_move_player_staircase_direction(self):
        """Test moving player using staircase (up direction)."""
        with patch.object(self.controller, '_handle_staircase') as mock_handle:
            mock_handle.return_value = (True, {"success": True})
            
            success, response = self.controller.move_player(self.test_player, "up")
            
            mock_handle.assert_called_once_with(self.test_player)
            assert success is True
    
    def test_handle_staircase_success(self):
        """Test successful staircase usage."""
        # Set up room with staircase
        staircase_room = Room(room_id="room_with_stairs", name="Staircase Room", floor=1)
        staircase_room.set_staircase(True)
        self.test_player.room_id = "room_with_stairs"
        
        # Mock getting current room and new floor start room
        self.mock_room_db.get_room.side_effect = [
            staircase_room.to_dict(),  # Current room with staircase
            self.start_room.to_dict()  # Start room on new floor
        ]
        
        with patch.object(self.controller, 'ensure_floor_generated'):
            success, response = self.controller._handle_staircase(self.test_player)
        
        assert success is True
        assert response["error"] is False
        assert self.test_player.floor == 2
        assert self.test_player.room_id == "start"
        assert "You ascend to floor 2!" in response["message"]
    
    def test_handle_staircase_no_staircase(self):
        """Test staircase usage when room has no staircase."""
        # Mock room without staircase
        self.mock_room_db.get_room.return_value = self.start_room.to_dict()
        
        success, response = self.controller._handle_staircase(self.test_player)
        
        assert success is False
        assert response["error"] is True
        assert "There is no staircase here" in response["message"]
    
    def test_handle_staircase_room_not_found(self):
        """Test staircase usage when current room is not found."""
        self.mock_room_db.get_room.return_value = None
        
        success, response = self.controller._handle_staircase(self.test_player)
        
        assert success is False
        assert response["error"] is True
        assert "There is no staircase here" in response["message"]
    
    def test_get_room_from_database(self):
        """Test getting room from database."""
        room_data = self.start_room.to_dict()
        self.mock_room_db.get_room.return_value = room_data
        
        result = self.controller.get_room("start", 1)
        
        assert result is not None
        assert result.room_id == "start"
        assert result.name == "Starting Room"
        self.mock_room_db.get_room.assert_called_once_with("start", 1, None)
    
    def test_get_room_from_cache(self):
        """Test getting room from cache when not in database."""
        # Set up cache
        cache_key = "1_start"
        self.controller.room_cache[cache_key] = self.start_room
        
        # Mock database to return None
        self.mock_room_db.get_room.return_value = None
        
        result = self.controller.get_room("start", 1)
        
        assert result is not None
        assert result.room_id == "start"
        assert result.name == "Starting Room"
    
    def test_get_room_with_session(self):
        """Test getting room with session ID."""
        self.controller.set_session("test-session")
        room_data = self.start_room.to_dict()
        self.mock_room_db.get_room.return_value = room_data
        
        result = self.controller.get_room("start", 1)
        
        assert result is not None
        self.mock_room_db.get_room.assert_called_once_with("start", 1, "test-session")
    
    def test_get_room_not_found(self):
        """Test getting room that doesn't exist."""
        self.mock_room_db.get_room.return_value = None
        
        result = self.controller.get_room("nonexistent", 1)
        
        assert result is None
    
    def test_save_room_success(self):
        """Test successful room saving."""
        self.mock_room_db.save_room.return_value = True
        
        result = self.controller._save_room(self.start_room)
        
        assert result is True
        self.mock_room_db.save_room.assert_called_once_with("start", 1, self.start_room.to_dict(), None)
        
        # Check cache is updated
        cache_key = "1_start"
        assert cache_key in self.controller.room_cache
        assert self.controller.room_cache[cache_key] == self.start_room
    
    def test_save_room_with_session(self):
        """Test saving room with session ID."""
        self.controller.set_session("test-session")
        self.mock_room_db.save_room.return_value = True
        
        result = self.controller._save_room(self.start_room)
        
        assert result is True
        self.mock_room_db.save_room.assert_called_once_with("start", 1, self.start_room.to_dict(), "test-session")
    
    def test_save_room_failure(self):
        """Test room saving failure."""
        self.mock_room_db.save_room.return_value = False
        
        result = self.controller._save_room(self.start_room)
        
        assert result is False
        # Cache should not be updated on failure
        assert len(self.controller.room_cache) == 0
    
    def test_clear_room_cache_all_floors(self):
        """Test clearing cache for all floors."""
        # Populate cache
        self.controller.room_cache["1_start"] = self.start_room
        self.controller.room_cache["2_start"] = self.room_1
        
        self.controller.clear_room_cache()
        
        assert len(self.controller.room_cache) == 0
    
    def test_clear_room_cache_specific_floor(self):
        """Test clearing cache for specific floor."""
        # Populate cache
        self.controller.room_cache["1_start"] = self.start_room
        self.controller.room_cache["1_room1"] = self.room_1
        self.controller.room_cache["2_start"] = self.room_2
        
        self.controller.clear_room_cache(floor=1)
        
        # Only floor 1 rooms should be removed
        assert "1_start" not in self.controller.room_cache
        assert "1_room1" not in self.controller.room_cache
        assert "2_start" in self.controller.room_cache
    
    def test_clear_room_cache_with_session(self):
        """Test clearing cache with session ID."""
        self.controller.set_session("test-session")
        
        # Populate cache
        self.controller.room_cache["test-session_1_start"] = self.start_room
        self.controller.room_cache["test-session_1_room1"] = self.room_1
        self.controller.room_cache["other-session_1_start"] = self.room_2
        
        self.controller.clear_room_cache(floor=1)
        
        # Only current session floor 1 rooms should be removed
        assert "test-session_1_start" not in self.controller.room_cache
        assert "test-session_1_room1" not in self.controller.room_cache
        assert "other-session_1_start" in self.controller.room_cache
    
    @patch('app.controllers.movement.random.randint')
    @patch('app.controllers.movement.random.choice')
    @patch('app.controllers.movement.get_random_room_names')
    @patch('app.controllers.movement.get_random_room_descriptions')
    def test_generate_room(self, mock_descriptions, mock_names, mock_choice, mock_randint):
        """Test room generation."""
        # Mock the random functions
        mock_names.return_value = ["Test Room"]
        mock_descriptions.return_value = ["A test room description"]
        mock_choice.side_effect = ["Test Room", "A test room description"]
        mock_randint.return_value = 0.3  # For encounter chance calculation
        
        with patch('app.utils.helpers.calculate_encounter_chance') as mock_calc:
            mock_calc.return_value = 0.4
            
            room = self.controller._generate_room("test_room", 1)
        
        assert room.room_id == "test_room"
        assert room.name == "Test Room"
        assert room.description == "A test room description"
        assert room.floor == 1
        assert room.encounter_chance == 0.4
    
    @patch('app.controllers.movement.random.seed')
    @patch('app.controllers.movement.random.randint')
    def test_generate_complete_floor(self, mock_randint, mock_seed):
        """Test complete floor generation."""
        # Mock random functions
        mock_randint.side_effect = [5, 0, 0, 0, 0]  # Floor size, then room connections
        
        with patch.object(self.controller, '_generate_start_room') as mock_start:
            with patch.object(self.controller, '_generate_room') as mock_gen_room:
                with patch.object(self.controller, '_connect_floor_rooms') as mock_connect:
                    # Set up mocks
                    mock_start.return_value = self.start_room
                    mock_gen_room.return_value = self.room_1
                    
                    # Mock generate_room_id to return predictable IDs
                    with patch('app.controllers.movement.generate_room_id') as mock_gen_id:
                        mock_gen_id.side_effect = ["room_1", "room_2", "room_3", "room_4"]
                        
                        with patch('app.controllers.movement.random.choice') as mock_choice:
                            mock_choice.return_value = "room_1"  # For staircase placement
                            
                            rooms = self.controller._generate_complete_floor(1)
        
        assert len(rooms) == 5  # 1 start + 4 generated
        assert "start" in rooms
        assert rooms["start"].room_id == "start"
        mock_connect.assert_called_once()
    
    def test_connect_floor_rooms(self):
        """Test floor room connection logic."""
        # Create test rooms
        rooms = {
            "start": self.start_room,
            "room_1": self.room_1,
            "room_2": self.room_2
        }
        room_ids = ["start", "room_1", "room_2"]
        
        # Clear existing connections for clean test
        for room in rooms.values():
            room.connections = {}
        
        # Test the function directly without mocking random - it should work regardless
        self.controller._connect_floor_rooms(rooms, room_ids)
        
        # Verify that connections were made
        # At minimum, all rooms should be reachable from start room
        assert len(rooms) == 3
        
        # Check that at least some connections exist
        total_connections = sum(len(room.connections) for room in rooms.values())
        assert total_connections >= 4  # At least 2 bidirectional connections for 3 rooms
    
    def test_ensure_floor_generated_existing_floor(self):
        """Test ensuring floor generation when floor already exists."""
        # Mock that start room exists
        self.mock_room_db.get_room.return_value = self.start_room.to_dict()
        
        with patch.object(self.controller, '_floor_has_staircase') as mock_has_staircase:
            mock_has_staircase.return_value = True
            
            self.controller.ensure_floor_generated(1)
            
            # Should not regenerate if floor exists
            mock_has_staircase.assert_called_once_with(1)
    
    def test_ensure_floor_generated_new_floor(self):
        """Test ensuring floor generation for new floor."""
        # Mock that start room doesn't exist
        self.mock_room_db.get_room.return_value = None
        
        with patch.object(self.controller, '_generate_complete_floor') as mock_gen_floor:
            with patch.object(self.controller, '_save_room') as mock_save:
                mock_gen_floor.return_value = {"start": self.start_room}
                mock_save.return_value = True
                
                self.controller.ensure_floor_generated(1)
                
                mock_gen_floor.assert_called_once_with(1)
                mock_save.assert_called_once_with(self.start_room)
    
    def test_get_available_moves(self):
        """Test getting available movement options."""
        self.mock_room_db.get_room.return_value = self.start_room.to_dict()
        
        result = self.controller.get_available_moves(self.test_player)
        
        assert result["error"] is False
        assert "available_directions" in result["data"]
        assert "has_staircase" in result["data"]
        assert result["data"]["available_directions"] == ["north", "east"]
        assert result["data"]["has_staircase"] is False
    
    def test_get_available_moves_room_not_found(self):
        """Test getting available moves when room not found."""
        self.mock_room_db.get_room.return_value = None
        
        result = self.controller.get_available_moves(self.test_player)
        
        assert result["error"] is True
        assert "Current room not found" in result["message"]
    
    def test_initialize_player_room(self):
        """Test initializing starting room for new player."""
        self.mock_room_db.get_room.return_value = self.start_room.to_dict()
        
        with patch.object(self.controller, 'ensure_floor_generated') as mock_ensure:
            result = self.controller.initialize_player_room(self.test_player)
            
            mock_ensure.assert_called_once_with(1)
            assert result.room_id == "start"
    
    def test_initialize_player_room_fallback(self):
        """Test initializing player room with fallback generation."""
        # Mock that room doesn't exist in database
        self.mock_room_db.get_room.return_value = None
        
        with patch.object(self.controller, 'ensure_floor_generated'):
            with patch.object(self.controller, '_generate_start_room') as mock_gen_start:
                with patch.object(self.controller, '_save_room') as mock_save:
                    mock_gen_start.return_value = self.start_room
                    mock_save.return_value = True
                    
                    result = self.controller.initialize_player_room(self.test_player)
                    
                    assert result == self.start_room
                    mock_gen_start.assert_called_once_with(1)
                    mock_save.assert_called_once_with(self.start_room)
    
    def test_get_opposite_direction(self):
        """Test getting opposite directions."""
        assert self.controller._get_opposite_direction("north") == "south"
        assert self.controller._get_opposite_direction("south") == "north"
        assert self.controller._get_opposite_direction("east") == "west"
        assert self.controller._get_opposite_direction("west") == "east"
        assert self.controller._get_opposite_direction("invalid") == "invalid"
    
    def test_ensure_bidirectional_connection_no_existing(self):
        """Test ensuring bidirectional connection when none exists."""
        # Clear connections
        self.room_1.connections = {}
        
        self.controller._ensure_bidirectional_connection(
            self.start_room, self.room_1, "north", "start", "room_1"
        )
        
        # Should add reverse connection
        assert self.room_1.get_connection("south") == "start"
    
    def test_ensure_bidirectional_connection_existing(self):
        """Test ensuring bidirectional connection when one already exists."""
        # Set up existing connection
        self.room_1.add_connection("south", "start")
        
        self.controller._ensure_bidirectional_connection(
            self.start_room, self.room_1, "north", "start", "room_1"
        )
        
        # Should not change existing connection
        assert self.room_1.get_connection("south") == "start"
    
    @patch('hashlib.md5')
    @patch('app.controllers.movement.random.seed')
    def test_generate_new_floor_for_session(self, mock_seed, mock_md5):
        """Test generating new floor for specific session."""
        # Mock hash generation
        mock_hash = Mock()
        mock_hash.hexdigest.return_value = "12345678abcdef"
        mock_md5.return_value = mock_hash
        
        session_id = "test-session-123"
        
        with patch.object(self.controller, '_clear_floor_data') as mock_clear:
            with patch.object(self.controller, '_generate_complete_floor') as mock_gen_floor:
                with patch.object(self.controller, '_save_room') as mock_save:
                    mock_gen_floor.return_value = {"start": self.start_room}
                    
                    self.controller.generate_new_floor_for_session(1, session_id)
                    
                    mock_clear.assert_called_once_with(1)
                    mock_gen_floor.assert_called_once_with(1)
                    mock_save.assert_called_once_with(self.start_room)
                    # Verify seeding was called with session-based seed
                    mock_seed.assert_called()
    
    def test_move_player_missing_next_room_regeneration(self):
        """Test movement when next room is missing and needs regeneration."""
        # Mock current room exists but next room is missing
        self.mock_room_db.get_room.side_effect = [
            self.start_room.to_dict(),  # Current room
            None,  # Next room missing first time
            self.room_1.to_dict()  # Next room after regeneration
        ]
        self.mock_room_db.save_room.return_value = True
        
        with patch.object(self.controller, 'ensure_floor_generated'):
            with patch.object(self.controller, '_regenerate_complete_floor') as mock_regen:
                success, response = self.controller.move_player(self.test_player, "north")
                
                # Should attempt regeneration
                mock_regen.assert_called_once_with(1)
                assert success is True
    
    def test_move_player_missing_next_room_create_temporary(self):
        """Test movement when next room is missing and can't be regenerated."""
        # Mock current room exists but next room is missing even after regeneration
        self.mock_room_db.get_room.side_effect = [
            self.start_room.to_dict(),  # Current room
            None,  # Next room missing first time
            None   # Next room still missing after regeneration
        ]
        self.mock_room_db.save_room.return_value = True
        
        with patch.object(self.controller, 'ensure_floor_generated'):
            with patch.object(self.controller, '_regenerate_complete_floor'):
                with patch.object(self.controller, '_generate_room') as mock_gen_room:
                    with patch.object(self.controller, '_save_room') as mock_save:
                        mock_gen_room.return_value = self.room_1
                        mock_save.return_value = True
                        
                        success, response = self.controller.move_player(self.test_player, "north")
                        
                        # Should create temporary room as last resort
                        mock_gen_room.assert_called_once_with("room_1", 1)
                        mock_save.assert_called()
                        assert success is True


class TestMovementControllerEdgeCases:
    """Test edge cases and error conditions for MovementController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_room_db = Mock(spec=RoomDB)
        self.controller = MovementController(room_db=self.mock_room_db)
        self.test_player = Player(session_id="test-session", name="Test Player")
    
    def test_move_player_normalized_directions(self):
        """Test that movement directions are properly normalized."""
        room = Room(room_id="start", name="Start", floor=1)
        room.add_connection("north", "next_room")
        
        next_room = Room(room_id="next_room", name="Next", floor=1)
        self.mock_room_db.save_room.return_value = True
        
        with patch.object(self.controller, 'ensure_floor_generated'):
            # Test various direction formats
            for direction in ["north", "North", "NORTH", "n", "N"]:
                self.test_player.room_id = "start"  # Reset position
                
                # Reset mock for each iteration
                self.mock_room_db.get_room.side_effect = [
                    room.to_dict(),
                    next_room.to_dict()
                ]
                
                success, response = self.controller.move_player(self.test_player, direction)
                assert success is True
                assert response["data"]["direction"] == "north"
    
    def test_room_cache_key_generation(self):
        """Test that room cache keys are generated correctly."""
        # Test without session
        room = Room(room_id="test", name="Test", floor=2)
        self.controller._save_room(room)
        
        expected_key = "2_test"
        assert expected_key in self.controller.room_cache
        
        # Test with session
        self.controller.set_session("test-session")
        room2 = Room(room_id="test2", name="Test2", floor=3)
        self.controller._save_room(room2)
        
        expected_key2 = "test-session_3_test2"
        assert expected_key2 in self.controller.room_cache
    
    def test_floor_has_staircase_default(self):
        """Test _floor_has_staircase default implementation."""
        # This method currently always returns True as a simplified implementation
        result = self.controller._floor_has_staircase(1)
        assert result is True
    
    def test_get_all_rooms_on_floor_empty(self):
        """Test _get_all_rooms_on_floor returns empty list by default."""
        # This method currently returns empty list as it's for legacy support
        result = self.controller._get_all_rooms_on_floor(1)
        assert result == []
    
    @patch('app.controllers.movement.random.random')
    def test_generate_room_ally_probability(self, mock_random):
        """Test ally generation probability in rooms."""
        # Mock random to trigger ally generation (8% chance)
        mock_random.return_value = 0.07  # Below 8% threshold
        
        with patch.object(self.controller, '_generate_room_ally') as mock_gen_ally:
            mock_gen_ally.return_value = {"name": "Test Ally", "attack_power": 15}
            
            room = self.controller._generate_room("test_room", 1)
            
            # Should generate ally for non-start rooms
            mock_gen_ally.assert_called_once_with(1)
            assert room.ally_data == {"name": "Test Ally", "attack_power": 15}
    
    @patch('app.controllers.movement.random.random')
    def test_generate_room_no_ally(self, mock_random):
        """Test room generation without ally."""
        # Mock random to not trigger ally generation
        mock_random.return_value = 0.09  # Above 8% threshold
        
        room = self.controller._generate_room("test_room", 1)
        
        assert room.ally_data is None
    
    def test_generate_room_ally_with_generation_controller(self):
        """Test ally generation using GenerationController."""
        mock_ally_content = {
            "name": "Brave Knight",
            "description": "A valiant knight ready to help"
        }
        
        with patch('app.controllers.generation.GenerationController') as mock_gen_class:
            mock_gen_instance = Mock()
            mock_gen_instance.generate_ally_content.return_value = mock_ally_content
            mock_gen_class.return_value = mock_gen_instance
            
            ally_data = self.controller._generate_room_ally(2)
            
            assert ally_data["name"] == "Brave Knight"
            assert ally_data["description"] == "A valiant knight ready to help"
            assert ally_data["attack_power"] == 14  # 10 + (2 * 2)
            assert ally_data["floor"] == 2
    
    def test_generate_start_room(self):
        """Test generation of start room."""
        room = self.controller._generate_start_room(3)
        
        assert room.room_id == "start"
        assert room.name == "Floor 3 Entrance"
        assert "floor 3" in room.description.lower()
        assert room.floor == 3
        assert room.encounter_chance == 0.1  # Lower chance in start room
    
    @patch('app.controllers.movement.random.randint')
    @patch('app.controllers.movement.random.sample')
    def test_generate_room_connections(self, mock_sample, mock_randint):
        """Test generation of room connections."""
        room = Room(room_id="test", name="Test", floor=1)
        
        # Mock 2 connections to north and east
        mock_randint.return_value = 2
        mock_sample.return_value = ["north", "east"]
        
        with patch('app.controllers.movement.generate_room_id') as mock_gen_id:
            mock_gen_id.side_effect = ["room_north", "room_east"]
            
            self.controller._generate_room_connections(room)
            
            assert room.get_connection("north") == "room_north"
            assert room.get_connection("east") == "room_east"
            assert len(room.connections) == 2


class TestMovementControllerSessionHandling:
    """Test session-specific functionality in MovementController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_room_db = Mock(spec=RoomDB)
        self.controller = MovementController(room_db=self.mock_room_db)
        self.session_id = "test-session-123"
    
    def test_get_room_for_session(self):
        """Test getting room for specific session."""
        room_data = {
            "room_id": "test", 
            "name": "Test Room", 
            "description": "A test room",
            "floor": 1,
            "connections": {},
            "has_staircase": False,
            "encounter_chance": 0.3,
            "has_been_visited": False,
            "ally_data": None
        }
        self.mock_room_db.get_room.return_value = room_data
        
        result = self.controller.get_room_for_session("test", 1, self.session_id)
        
        assert result is not None
        assert result.room_id == "test"
        # Should call with session-specific room ID
        expected_session_room_id = f"test_session_{self.session_id[:8]}"
        self.mock_room_db.get_room.assert_called_once_with(expected_session_room_id, 1)
    
    def test_get_room_for_session_fallback_to_regular(self):
        """Test session room handling falls back to regular when no session provided."""
        room_data = {
            "room_id": "test", 
            "name": "Test Room", 
            "description": "A test room",
            "floor": 1,
            "connections": {},
            "has_staircase": False,
            "encounter_chance": 0.3,
            "has_been_visited": False,
            "ally_data": None
        }
        
        with patch.object(self.controller, 'get_room') as mock_get_room:
            mock_get_room.return_value = Room.from_dict(room_data)
            
            # Test with empty string instead of None to avoid type errors
            result = self.controller.get_room_for_session("test", 1, "")
            
            mock_get_room.assert_called_once_with("test", 1)
    
    def test_save_room_for_session(self):
        """Test saving room for specific session."""
        room = Room(room_id="test", name="Test Room", floor=1)
        self.mock_room_db.save_room.return_value = True
        
        result = self.controller._save_room_for_session(room, self.session_id)
        
        assert result is True
        # Should save with session-specific room ID
        expected_session_room_id = f"test_session_{self.session_id[:8]}"
        self.mock_room_db.save_room.assert_called_once_with(
            expected_session_room_id, 1, room.to_dict()
        )
    
    def test_save_room_for_session_fallback(self):
        """Test session room saving falls back to regular when no session provided."""
        room = Room(room_id="test", name="Test Room", floor=1)
        
        with patch.object(self.controller, '_save_room') as mock_save_room:
            mock_save_room.return_value = True
            
            # Test with empty string instead of None to avoid type errors
            result = self.controller._save_room_for_session(room, "")
            
            mock_save_room.assert_called_once_with(room)
            assert result is True
    
    @patch('hashlib.md5')
    @patch('app.controllers.movement.random.seed')
    def test_regenerate_complete_floor_for_session(self, mock_seed, mock_md5):
        """Test regenerating complete floor for specific session."""
        # Mock hash generation
        mock_hash = Mock()
        mock_hash.hexdigest.return_value = "abcdef123456"
        mock_md5.return_value = mock_hash
        
        floor = 2
        
        # Set up cache to clear
        session_cache_key = f"{floor}_session_{self.session_id[:8]}_test"
        self.controller.room_cache[session_cache_key] = Room("test", "Test", floor=floor)
        
        with patch.object(self.controller, '_generate_complete_floor') as mock_gen_floor:
            with patch.object(self.controller, '_save_room_for_session') as mock_save:
                mock_gen_floor.return_value = {"start": Room("start", "Start", floor=floor)}
                
                self.controller._regenerate_complete_floor_for_session(floor, self.session_id)
                
                # Should clear session-specific cache
                assert session_cache_key not in self.controller.room_cache
                
                # Should generate floor with session-based seed
                mock_seed.assert_called()
                mock_gen_floor.assert_called_once_with(floor)
                mock_save.assert_called()
    
    def test_regenerate_complete_floor_for_session_fallback(self):
        """Test session floor regeneration falls back when no session provided."""
        with patch.object(self.controller, '_regenerate_complete_floor') as mock_regen:
            # Test with empty string instead of None to avoid type errors
            self.controller._regenerate_complete_floor_for_session(1, "")
            
            mock_regen.assert_called_once_with(1)