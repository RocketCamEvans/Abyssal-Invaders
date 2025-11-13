"""
Unit tests for the inventory system.
"""

import unittest
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import Player, Item, Enemy
from app.controllers import InventoryController


class TestItemModel(unittest.TestCase):
    """Test the Item model."""
    
    def test_item_creation(self):
        """Test creating an item."""
        item = Item('health_potion')
        
        self.assertIsNotNone(item.item_id)
        self.assertEqual(item.name, 'Health Potion')
        self.assertEqual(item.effect_type, 'heal')
        self.assertEqual(item.effect_value, 30)
        self.assertTrue(item.usable_in_combat)
        self.assertEqual(item.rarity, 'common')
    
    def test_item_types(self):
        """Test all available item types."""
        for item_type in Item.ITEM_TYPES.keys():
            item = Item(item_type)
            self.assertIsNotNone(item)
            self.assertEqual(item.item_type, item_type)
    
    def test_invalid_item_type(self):
        """Test creating an item with invalid type."""
        with self.assertRaises(ValueError):
            Item('invalid_item_type')
    
    def test_item_to_dict(self):
        """Test item serialization."""
        item = Item('health_potion')
        item_dict = item.to_dict()
        
        self.assertIn('item_id', item_dict)
        self.assertIn('item_type', item_dict)
        self.assertIn('name', item_dict)
        self.assertEqual(item_dict['item_type'], 'health_potion')
    
    def test_item_from_dict(self):
        """Test item deserialization."""
        item = Item('attack_boost')
        item_dict = item.to_dict()
        
        restored_item = Item.from_dict(item_dict)
        self.assertEqual(restored_item.item_id, item.item_id)
        self.assertEqual(restored_item.item_type, item.item_type)
        self.assertEqual(restored_item.name, item.name)
    
    def test_health_potion_use(self):
        """Test using a health potion."""
        player = Player(name="Test Hero")
        player.health = 50  # Damage player
        
        item = Item('health_potion')
        result = item.use(player)
        
        self.assertTrue(result['success'])
        self.assertEqual(player.health, 80)  # 50 + 30
        self.assertIn('healed', result)
    
    def test_health_potion_max_health(self):
        """Test health potion doesn't exceed max health."""
        player = Player(name="Test Hero")
        player.health = 90
        
        item = Item('health_potion')
        result = item.use(player)
        
        self.assertTrue(result['success'])
        self.assertEqual(player.health, 100)  # Capped at max
    
    def test_attack_boost_use(self):
        """Test using attack boost."""
        player = Player(name="Test Hero")
        initial_attack = player.attack_power
        
        item = Item('attack_boost')
        result = item.use(player)
        
        self.assertTrue(result['success'])
        self.assertEqual(player.attack_power, initial_attack + 15)
        self.assertIn('attack_boost', result)
    
    def test_defense_boost_use(self):
        """Test using defense boost."""
        player = Player(name="Test Hero")
        initial_defense = player.defense
        
        item = Item('defense_boost')
        result = item.use(player)
        
        self.assertTrue(result['success'])
        self.assertEqual(player.defense, initial_defense + 10)
        self.assertIn('defense_boost', result)
    
    def test_damage_bomb_use(self):
        """Test using damage bomb on enemy."""
        player = Player(name="Test Hero")
        enemy = Enemy(name="Test Enemy", description="A test enemy", floor=1)
        enemy.health = 100
        enemy.max_health = 100
        enemy.defense = 0  # Set defense to 0 for predictable test
        
        item = Item('damage_bomb')
        result = item.use(player, enemy)
        
        self.assertTrue(result['success'])
        self.assertEqual(enemy.health, 60)  # 100 - 40
        self.assertIn('damage_dealt', result)
    
    def test_damage_bomb_without_enemy(self):
        """Test using damage bomb without enemy fails."""
        player = Player(name="Test Hero")
        
        item = Item('damage_bomb')
        result = item.use(player, None)
        
        self.assertFalse(result['success'])
    
    def test_gold_coin_bag_use(self):
        """Test using gold coin bag."""
        player = Player(name="Test Hero")
        initial_gold = player.gold
        
        item = Item('gold_coin_bag')
        result = item.use(player)
        
        self.assertTrue(result['success'])
        self.assertEqual(player.gold, initial_gold + 50)
        self.assertIn('gold_gained', result)
    
    def test_escape_scroll_use(self):
        """Test using escape scroll."""
        player = Player(name="Test Hero")
        
        item = Item('escape_scroll')
        result = item.use(player)
        
        self.assertTrue(result['success'])
        self.assertIn('guaranteed_flee', result)
        self.assertTrue(result['guaranteed_flee'])
    
    def test_get_random_item_type(self):
        """Test random item generation."""
        # Test that it returns valid item types
        for floor in [1, 5, 10]:
            item_type = Item.get_random_item_type(floor)
            self.assertIn(item_type, Item.ITEM_TYPES)


class TestPlayerInventory(unittest.TestCase):
    """Test player inventory management."""
    
    def test_add_item_to_inventory(self):
        """Test adding an item to player inventory."""
        player = Player(name="Test Hero")
        item = Item('health_potion')
        
        self.assertEqual(len(player.inventory), 0)
        player.add_item(item)
        self.assertEqual(len(player.inventory), 1)
    
    def test_remove_item_from_inventory(self):
        """Test removing an item from inventory."""
        player = Player(name="Test Hero")
        item = Item('health_potion')
        player.add_item(item)
        
        removed_item = player.remove_item(item.item_id)
        self.assertIsNotNone(removed_item)
        self.assertEqual(removed_item.item_id, item.item_id)
        self.assertEqual(len(player.inventory), 0)
    
    def test_remove_nonexistent_item(self):
        """Test removing item that doesn't exist."""
        player = Player(name="Test Hero")
        removed_item = player.remove_item("nonexistent-id")
        self.assertIsNone(removed_item)
    
    def test_get_item_from_inventory(self):
        """Test getting an item from inventory."""
        player = Player(name="Test Hero")
        item = Item('attack_boost')
        player.add_item(item)
        
        found_item = player.get_item(item.item_id)
        self.assertIsNotNone(found_item)
        self.assertEqual(found_item.item_id, item.item_id)
    
    def test_inventory_serialization(self):
        """Test that inventory is properly serialized."""
        player = Player(name="Test Hero")
        item1 = Item('health_potion')
        item2 = Item('attack_boost')
        player.add_item(item1)
        player.add_item(item2)
        
        player_dict = player.to_dict()
        self.assertIn('inventory', player_dict)
        self.assertEqual(len(player_dict['inventory']), 2)
    
    def test_inventory_deserialization(self):
        """Test that inventory is properly deserialized."""
        player = Player(name="Test Hero")
        item1 = Item('health_potion')
        item2 = Item('defense_boost')
        player.add_item(item1)
        player.add_item(item2)
        
        player_dict = player.to_dict()
        restored_player = Player.from_dict(player_dict)
        
        self.assertEqual(len(restored_player.inventory), 2)
        self.assertEqual(restored_player.inventory[0].item_type, 'health_potion')
        self.assertEqual(restored_player.inventory[1].item_type, 'defense_boost')


class TestInventoryController(unittest.TestCase):
    """Test the inventory controller."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = InventoryController()
        self.player = Player(name="Test Hero")
    
    def test_roll_for_item_find(self):
        """Test item finding logic."""
        # Test multiple times to check probability
        found_count = 0
        trials = 100
        
        for _ in range(trials):
            found, item = self.controller.roll_for_item_find(self.player, room_visited=False)
            if found:
                found_count += 1
                self.assertIsNotNone(item)
                self.assertIsInstance(item, Item)
        
        # Should find items at approximately BASE_ITEM_FIND_CHANCE rate (65%)
        # Allow for variance (between 50% and 80%)
        self.assertGreater(found_count, trials * 0.5)
        self.assertLess(found_count, trials * 0.8)
    
    def test_no_items_in_visited_rooms(self):
        """Test that no items are found in visited rooms."""
        for _ in range(50):
            found, item = self.controller.roll_for_item_find(self.player, room_visited=True)
            self.assertFalse(found)
            self.assertIsNone(item)
    
    def test_add_item_to_inventory(self):
        """Test adding item through controller."""
        item = Item('health_potion')
        result = self.controller.add_item_to_inventory(self.player, item)
        
        self.assertFalse(result['error'])
        self.assertEqual(len(self.player.inventory), 1)
        self.assertIn('item_added', result['data'])
    
    def test_use_item_success(self):
        """Test using an item successfully."""
        self.player.health = 50
        item = Item('health_potion')
        self.player.add_item(item)
        
        success, result = self.controller.use_item(self.player, item.item_id)
        
        self.assertTrue(success)
        self.assertEqual(self.player.health, 80)
        self.assertEqual(len(self.player.inventory), 0)  # Item consumed
    
    def test_use_nonexistent_item(self):
        """Test using an item that doesn't exist."""
        success, result = self.controller.use_item(self.player, "nonexistent-id")
        
        self.assertFalse(success)
        self.assertTrue(result['error'])
    
    def test_use_combat_item_in_combat(self):
        """Test using combat item during battle."""
        enemy = Enemy(name="Test Enemy", description="A test", floor=1)
        enemy.health = 100
        enemy.max_health = 100
        enemy.defense = 0  # Set defense to 0 for predictable test
        self.player.in_battle = True
        
        item = Item('damage_bomb')
        self.player.add_item(item)
        
        success, result = self.controller.use_item(self.player, item.item_id, enemy)
        
        self.assertTrue(success)
        self.assertEqual(enemy.health, 60)  # 100 - 40 damage
    
    def test_get_inventory(self):
        """Test getting inventory information."""
        item1 = Item('health_potion')
        item2 = Item('attack_boost')
        self.player.add_item(item1)
        self.player.add_item(item2)
        
        result = self.controller.get_inventory(self.player)
        
        self.assertFalse(result['error'])
        self.assertEqual(result['data']['inventory_size'], 2)
        self.assertIn('inventory', result['data'])
        self.assertIn('grouped_inventory', result['data'])
    
    def test_discard_item(self):
        """Test discarding an item."""
        item = Item('gold_coin_bag')
        self.player.add_item(item)
        
        success, result = self.controller.discard_item(self.player, item.item_id)
        
        self.assertTrue(success)
        self.assertEqual(len(self.player.inventory), 0)
        self.assertIn('item_discarded', result['data'])
    
    def test_get_usable_combat_items(self):
        """Test getting combat-usable items."""
        item1 = Item('health_potion')  # Usable in combat
        item2 = Item('gold_coin_bag')  # Not usable in combat
        item3 = Item('damage_bomb')    # Usable in combat
        
        self.player.add_item(item1)
        self.player.add_item(item2)
        self.player.add_item(item3)
        
        usable_items = self.controller.get_usable_combat_items(self.player)
        
        self.assertEqual(len(usable_items), 2)
        # Verify only combat items are returned
        for item_info in usable_items:
            self.assertTrue(item_info['usable_in_combat'])


class TestInventoryIntegration(unittest.TestCase):
    """Integration tests for inventory system."""
    
    def test_full_item_lifecycle(self):
        """Test finding, storing, and using an item."""
        player = Player(name="Test Hero")
        controller = InventoryController()
        
        # Simulate finding an item
        item = Item('health_potion')
        controller.add_item_to_inventory(player, item)
        
        # Verify it's in inventory
        self.assertEqual(len(player.inventory), 1)
        
        # Damage player
        player.health = 40
        
        # Use the item
        success, result = controller.use_item(player, item.item_id)
        
        # Verify results
        self.assertTrue(success)
        self.assertEqual(player.health, 70)
        self.assertEqual(len(player.inventory), 0)
    
    def test_multiple_items_management(self):
        """Test managing multiple items."""
        player = Player(name="Test Hero")
        controller = InventoryController()
        
        # Add multiple items
        items = [
            Item('health_potion'),
            Item('attack_boost'),
            Item('defense_boost'),
            Item('gold_coin_bag')
        ]
        
        for item in items:
            controller.add_item_to_inventory(player, item)
        
        self.assertEqual(len(player.inventory), 4)
        
        # Use one item
        controller.use_item(player, items[0].item_id)
        self.assertEqual(len(player.inventory), 3)
        
        # Discard one item
        controller.discard_item(player, items[1].item_id)
        self.assertEqual(len(player.inventory), 2)
    
    def test_inventory_persistence(self):
        """Test that inventory survives serialization/deserialization."""
        player = Player(name="Test Hero")
        
        # Add items
        item1 = Item('health_potion')
        item2 = Item('attack_boost')
        player.add_item(item1)
        player.add_item(item2)
        
        # Serialize
        player_dict = player.to_dict()
        
        # Deserialize
        restored_player = Player.from_dict(player_dict)
        
        # Verify inventory
        self.assertEqual(len(restored_player.inventory), 2)
        self.assertEqual(restored_player.inventory[0].name, item1.name)
        self.assertEqual(restored_player.inventory[1].name, item2.name)


if __name__ == '__main__':
    unittest.main()
