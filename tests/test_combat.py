"""
Tests for combat controller functionality.
"""

import unittest
from app.models import Player, Enemy, Room, Ally
from app.controllers import CombatController


class TestCombat(unittest.TestCase):
    """Test cases for combat controller."""
    
    def setUp(self):
        """Set up test environment."""
        self.controller = CombatController()
        self.player = Player(name="Test Fighter")
        self.enemy = Enemy("Test Monster", "A dangerous test creature", 1)
        self.room = Room("test_room", "Test Arena", "A place for testing combat", 1)
    
    def test_combat_initialization(self):
        """Test combat initialization."""
        self.assertTrue(self.player.is_alive())
        self.assertTrue(self.enemy.is_alive())
        
        player, enemy, result = self.controller.initiate_combat(
            self.player, self.enemy, self.room
        )
        
        self.assertFalse(result['error'])
        self.assertIn('combat_log', result['data'])
        self.assertIn('winner', result['data'])
    
    def test_player_damage_calculation(self):
        """Test player damage calculation."""
        damage = self.controller._calculate_player_damage(self.player)
        
        self.assertIsInstance(damage, int)
        self.assertGreater(damage, 0)
    
    def test_enemy_damage_calculation(self):
        """Test enemy damage calculation."""
        damage = self.controller._calculate_enemy_damage(self.enemy)
        
        self.assertIsInstance(damage, int)
        self.assertGreater(damage, 0)
    
    def test_ally_usage(self):
        """Test using ally in combat."""
        ally = Ally("Test Ally", "A helpful ally", 1)
        self.player.add_ally(ally)
        
        success, result = self.controller.use_ally_in_combat(
            self.player, 0, self.enemy
        )
        
        self.assertTrue(success)
        self.assertFalse(result['error'])
        self.assertIn('damage_dealt', result['data'])
        self.assertEqual(len(self.player.allies), 0)  # Ally should be consumed
    
    def test_flee_attempt(self):
        """Test fleeing from combat."""
        success, result = self.controller.flee_from_combat(self.player, self.enemy)
        
        # Result should be either success (fled) or failure (took damage)
        self.assertIsInstance(success, bool)
        self.assertIn('message' if success else 'message', result)
    
    def test_encounter_chance(self):
        """Test encounter chance checking."""
        # Room that hasn't been visited should have encounter chance
        encounter = self.controller.check_encounter_chance(self.room)
        self.assertIsInstance(encounter, bool)
        
        # Mark room as visited
        self.room.visit()
        
        # Should have much lower chance now
        encounter2 = self.controller.check_encounter_chance(self.room)
        self.assertIsInstance(encounter2, bool)
    
    def test_combat_with_weak_enemy(self):
        """Test combat against a very weak enemy."""
        weak_enemy = Enemy("Weak Rat", "A tiny rat", 1)
        weak_enemy.health = 1
        weak_enemy.attack_power = 1
        
        player, enemy, result = self.controller.initiate_combat(
            self.player, weak_enemy, self.room
        )
        
        # Player should win easily
        self.assertFalse(result['error'])
        self.assertEqual(result['data']['winner'], 'player')
        self.assertFalse(enemy.is_alive())


if __name__ == '__main__':
    unittest.main()