"""
Tests for API routes and endpoints.
"""

import unittest
import json
from app import create_app
from app.utils import UserDB, HighScoreDB, RoomDB


class TestRoutes(unittest.TestCase):
    """Test cases for API routes."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['DATA_DIR'] = 'test_data'
        self.client = self.app.test_client()
        
        # Create test context
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test environment."""
        self.app_context.pop()
    
    def test_health_check(self):
        """Test basic health check endpoint."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertFalse(data['error'])
        self.assertIn('status', data['data'])
        self.assertEqual(data['data']['status'], 'healthy')
    
    def test_create_player(self):
        """Test player creation endpoint."""
        # Test with name
        response = self.client.post('/api/player/new', 
                                   json={'name': 'Test Hero'})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertFalse(data['error'])
        self.assertIn('session_id', data['data'])
        self.assertEqual(data['data']['player']['name'], 'Test Hero')
        
        # Test without name
        response = self.client.post('/api/player/new', json={})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertFalse(data['error'])
        self.assertEqual(data['data']['player']['name'], 'Unknown Adventurer')
    
    def test_player_status(self):
        """Test getting player status."""
        # Create player first
        create_response = self.client.post('/api/player/new', 
                                         json={'name': 'Status Test'})
        create_data = json.loads(create_response.data)
        session_id = create_data['data']['session_id']
        
        # Get status
        response = self.client.post('/api/player/status', 
                                   json={'session_id': session_id})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertFalse(data['error'])
        self.assertIn('player', data['data'])
        self.assertIn('current_room', data['data'])
    
    def test_invalid_session(self):
        """Test endpoints with invalid session ID."""
        response = self.client.post('/api/player/status', 
                                   json={'session_id': 'invalid-session'})
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertTrue(data['error'])
    
    def test_missing_data(self):
        """Test endpoints with missing required data."""
        # Missing session_id
        response = self.client.post('/api/player/status', json={})
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertTrue(data['error'])
    
    def test_high_scores(self):
        """Test high scores endpoint."""
        response = self.client.get('/api/scores/highscores')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertFalse(data['error'])
        self.assertIsInstance(data['data'], list)


if __name__ == '__main__':
    unittest.main()