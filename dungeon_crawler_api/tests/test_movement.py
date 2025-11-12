"""
Tests for movement controller functionality.
"""

import unittest
from app.models import Player, Room
from app.controllers import MovementController
from app.utils import RoomDB


class TestMovement(unittest.TestCase):
    """Test cases for movement controller."""
    
    def setUp(self):
        """Set up test environment."""
        self.controller = MovementController()
        self.player = Player(name="Test Player")
    
    def test_initialize_player_room(self):
        """Test player room initialization."""
        room = self.controller.initialize_player_room(self.player)
        
        self.assertIsNotNone(room)
        self.assertEqual(room.room_id, "start")
        self.assertEqual(room.floor, 1)
        self.assertGreater(len(room.get_available_directions()), 0)
    
    def test_invalid_direction(self):
        """Test movement with invalid direction."""
        success, result = self.controller.move_player(self.player, "invalid")
        
        self.assertFalse(success)
        self.assertTrue(result['error'])
        self.assertIn('Invalid direction', result['message'])
    
    def test_valid_movement(self):
        """Test valid movement between rooms."""
        # Initialize starting room
        start_room = self.controller.initialize_player_room(self.player)
        available_directions = start_room.get_available_directions()
        
        if available_directions:
            direction = available_directions[0]
            success, result = self.controller.move_player(self.player, direction)
            
            self.assertTrue(success)
            self.assertFalse(result['error'])
            self.assertNotEqual(self.player.room_id, "start")
    
    def test_get_available_moves(self):
        """Test getting available movement options."""
        self.controller.initialize_player_room(self.player)
        moves = self.controller.get_available_moves(self.player)
        
        self.assertFalse(moves['error'])
        self.assertIn('available_directions', moves['data'])
        self.assertIsInstance(moves['data']['available_directions'], list)
    
    def test_room_generation(self):
        """Test room generation functionality."""
        room = self.controller._generate_room("test_room", 1)
        
        self.assertEqual(room.room_id, "test_room")
        self.assertEqual(room.floor, 1)
        self.assertIsNotNone(room.name)
        self.assertIsNotNone(room.description)
        self.assertGreater(len(room.get_available_directions()), 0)
    
    def test_bidirectional_movement(self):
        """Test that players can backtrack to previous rooms."""
        # Initialize starting room
        start_room = self.controller.initialize_player_room(self.player)
        available_directions = start_room.get_available_directions()
        
        if available_directions:
            # Move in one direction
            direction = available_directions[0]
            success, result = self.controller.move_player(self.player, direction)
            
            if success:
                current_room_id = self.player.room_id
                
                # Get the current room and check if it has a connection back
                current_room = self.controller.get_room(current_room_id, self.player.floor)
                opposite_direction = self.controller._get_opposite_direction(direction)
                
                # Should be able to go back
                back_connection = current_room.get_connection(opposite_direction)
                self.assertIsNotNone(back_connection, f"No {opposite_direction} connection from {current_room_id}")
                
                # Try to move back
                success_back, result_back = self.controller.move_player(self.player, opposite_direction)
                self.assertTrue(success_back, f"Could not move back {opposite_direction}")
                
                # Should be back at the starting room
                self.assertEqual(self.player.room_id, "start")


if __name__ == '__main__':
    unittest.main()