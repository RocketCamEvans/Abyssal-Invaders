"""
Unit tests for the InventoryController class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import random
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from app.controllers.inventory import InventoryController
from app.models.player import Player
from app.models.item import Item
from app.models.enemy import Enemy


class TestInventoryController:
    """Test cases for InventoryController class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.controller = InventoryController()
        
        # Create test player
        self.player = Player(session_id="test_session", name="Test Hero")
        self.player.health = 100
        self.player.max_health = 100
        self.player.attack_power = 15
        self.player.defense = 5
        self.player.gold = 50
        
        # Create test enemy
        self.enemy = Enemy(name="Test Goblin", description="A small green creature", floor=1)
        self.enemy.health = 30
        self.enemy.max_health = 30
        self.enemy.attack_power = 8
        self.enemy.defense = 2
    
    def test_init(self):
        """Test InventoryController initialization."""
        controller = InventoryController()
        assert controller.BASE_ITEM_FIND_CHANCE == 0.65
    
    @patch('random.random')
    def test_roll_for_item_find_success(self, mock_random):
        """Test successful item finding."""
        mock_random.return_value = 0.5  # Below 0.65 threshold
        
        with patch.object(Item, 'get_random_item_type', return_value='health_potion'):
            found, item = self.controller.roll_for_item_find(self.player, room_visited=False)
            
            assert found is True
            assert item is not None
            assert isinstance(item, Item)
            assert item.item_type == 'health_potion'
    
    @patch('random.random')
    def test_roll_for_item_find_failure(self, mock_random):
        """Test failed item finding."""
        mock_random.return_value = 0.8  # Above 0.65 threshold
        
        found, item = self.controller.roll_for_item_find(self.player, room_visited=False)
        
        assert found is False
        assert item is None
    
    def test_roll_for_item_find_visited_room(self):
        """Test that no items are found in visited rooms."""
        found, item = self.controller.roll_for_item_find(self.player, room_visited=True)
        
        assert found is False
        assert item is None
    
    def test_add_item_to_inventory(self):
        """Test adding item to inventory through controller."""
        item = Item('health_potion')
        
        result = self.controller.add_item_to_inventory(self.player, item)
        
        assert result['error'] is False
        assert len(self.player.inventory) == 1
        assert 'item_added' in result['data']
        assert result['data']['inventory_size'] == 1
        assert result['message'] == f"Found {item.name}!"
    
    def test_use_item_success(self):
        """Test successfully using an item."""
        self.player.health = 50
        item = Item('health_potion')
        self.player.add_item(item)
        
        success, result = self.controller.use_item(self.player, item.item_id)
        
        assert success is True
        assert result['error'] is False
        assert self.player.health == 80  # 50 + 30
        assert len(self.player.inventory) == 0  # Item consumed
        assert 'item_used' in result['data']
        assert 'player_stats' in result['data']
    
    def test_use_item_not_found(self):
        """Test using non-existent item."""
        success, result = self.controller.use_item(self.player, "nonexistent-id")
        
        assert success is False
        assert result['error'] is True
        assert "not found in inventory" in result['message']
    
    def test_use_item_not_usable_in_combat(self):
        """Test using non-combat item during battle."""
        self.player.in_battle = True
        item = Item('gold_coin_bag')  # Not usable in combat
        self.player.add_item(item)
        
        success, result = self.controller.use_item(self.player, item.item_id)
        
        assert success is False
        assert result['error'] is True
        assert "cannot be used during combat" in result['message']
    
    def test_use_item_with_enemy(self):
        """Test using combat item with enemy present."""
        item = Item('damage_bomb')
        self.player.add_item(item)
        
        success, result = self.controller.use_item(self.player, item.item_id, self.enemy)
        
        assert success is True
        assert result['error'] is False
        assert 'enemy_stats' in result['data']
        assert self.enemy.health < 30  # Enemy took damage
    
    def test_use_item_failed_use(self):
        """Test item use failure."""
        item = Item('damage_bomb')
        self.player.add_item(item)
        
        # Mock item.use to return failure
        with patch.object(item, 'use', return_value={'success': False, 'message': 'Use failed'}):
            success, result = self.controller.use_item(self.player, item.item_id)
            
            assert success is False
            assert result['error'] is True
            assert result['message'] == 'Use failed'
    
    def test_get_inventory(self):
        """Test getting inventory information."""
        item1 = Item('health_potion')
        item2 = Item('attack_boost')
        self.player.add_item(item1)
        self.player.add_item(item2)
        
        result = self.controller.get_inventory(self.player)
        
        assert result['error'] is False
        assert result['data']['inventory_size'] == 2
        assert result['data']['total_items'] == 2
        assert 'inventory' in result['data']
        assert 'grouped_inventory' in result['data']
        assert len(result['data']['inventory']) == 2
    
    def test_get_inventory_empty(self):
        """Test getting empty inventory."""
        result = self.controller.get_inventory(self.player)
        
        assert result['error'] is False
        assert result['data']['inventory_size'] == 0
        assert result['data']['total_items'] == 0
        assert len(result['data']['inventory']) == 0
    
    def test_discard_item_success(self):
        """Test successfully discarding an item."""
        item = Item('gold_coin_bag')
        self.player.add_item(item)
        
        success, result = self.controller.discard_item(self.player, item.item_id)
        
        assert success is True
        assert result['error'] is False
        assert len(self.player.inventory) == 0
        assert 'item_discarded' in result['data']
        assert result['message'] == f"Discarded {item.name}"
    
    def test_discard_item_not_found(self):
        """Test discarding non-existent item."""
        success, result = self.controller.discard_item(self.player, "nonexistent-id")
        
        assert success is False
        assert result['error'] is True
        assert "not found in inventory" in result['message']
    
    def test_get_usable_combat_items(self):
        """Test getting combat-usable items."""
        item1 = Item('health_potion')  # Usable in combat
        item2 = Item('gold_coin_bag')  # Not usable in combat
        item3 = Item('damage_bomb')    # Usable in combat
        
        self.player.add_item(item1)
        self.player.add_item(item2)
        self.player.add_item(item3)
        
        usable_items = self.controller.get_usable_combat_items(self.player)
        
        assert len(usable_items) == 2
        for item_info in usable_items:
            assert item_info['usable_in_combat'] is True
    
    def test_get_usable_combat_items_empty(self):
        """Test getting combat items when none are usable."""
        item = Item('gold_coin_bag')  # Not usable in combat
        self.player.add_item(item)
        
        usable_items = self.controller.get_usable_combat_items(self.player)
        
        assert len(usable_items) == 0


class TestItemModel:
    """Test cases for Item model functionality."""
    
    def test_item_creation_all_types(self):
        """Test creating all types of items."""
        for item_type in Item.ITEM_TYPES.keys():
            item = Item(item_type)
            
            assert item.item_id is not None
            assert item.item_type == item_type
            assert item.name == Item.ITEM_TYPES[item_type]['name']
            assert item.effect_type == Item.ITEM_TYPES[item_type]['effect_type']
            assert item.effect_value == Item.ITEM_TYPES[item_type]['effect_value']
            assert item.usable_in_combat == Item.ITEM_TYPES[item_type]['usable_in_combat']
            assert item.rarity == Item.ITEM_TYPES[item_type]['rarity']
    
    def test_invalid_item_type(self):
        """Test creating item with invalid type."""
        with pytest.raises(ValueError, match="Invalid item type"):
            Item('invalid_item_type')
    
    def test_item_serialization(self):
        """Test item to_dict and from_dict."""
        item = Item('health_potion')
        item_dict = item.to_dict()
        
        assert 'item_id' in item_dict
        assert 'item_type' in item_dict
        assert 'name' in item_dict
        assert item_dict['item_type'] == 'health_potion'
        
        # Test deserialization
        restored_item = Item.from_dict(item_dict)
        assert restored_item.item_id == item.item_id
        assert restored_item.item_type == item.item_type
        assert restored_item.name == item.name
    
    def test_health_potion_use(self):
        """Test using health potions."""
        player = Player(session_id="test", name="Test Hero")
        player.health = 50
        
        # Test regular health potion
        item = Item('health_potion')
        result = item.use(player)
        
        assert result['success'] is True
        assert player.health == 80  # 50 + 30
        assert 'healed' in result
        
        # Test greater health potion
        player.health = 30
        item = Item('greater_health_potion')
        result = item.use(player)
        
        assert result['success'] is True
        assert player.health == 90  # 30 + 60
    
    def test_health_potion_max_health_cap(self):
        """Test health potion respects max health."""
        player = Player(session_id="test", name="Test Hero")
        player.health = 90
        
        item = Item('health_potion')
        result = item.use(player)
        
        assert result['success'] is True
        assert player.health == 100  # Capped at max_health
    
    def test_stat_boost_items(self):
        """Test attack and defense boost items."""
        player = Player(session_id="test", name="Test Hero")
        initial_attack = player.attack_power
        initial_defense = player.defense
        
        # Test attack boost
        item = Item('attack_boost')
        result = item.use(player)
        
        assert result['success'] is True
        assert player.attack_power == initial_attack + 15
        assert 'attack_boost' in result
        
        # Test defense boost
        item = Item('defense_boost')
        result = item.use(player)
        
        assert result['success'] is True
        assert player.defense == initial_defense + 10
        assert 'defense_boost' in result
    
    def test_damage_items(self):
        """Test damage-dealing items."""
        player = Player(session_id="test", name="Test Hero")
        enemy = Enemy(name="Test Enemy", description="A test", floor=1)
        enemy.defense = 0  # Remove defense for predictable testing
        
        # Test damage bomb
        item = Item('damage_bomb')
        result = item.use(player, enemy)
        
        assert result['success'] is True
        assert 'damage_dealt' in result
        assert result['damage_dealt'] == 40
        
        # Test poison vial
        enemy.health = enemy.max_health  # Reset health
        item = Item('poison_vial')
        result = item.use(player, enemy)
        
        assert result['success'] is True
        assert 'damage_dealt' in result
        assert result['damage_dealt'] == 25
    
    def test_damage_item_without_enemy(self):
        """Test damage items fail without enemy."""
        player = Player(session_id="test", name="Test Hero")
        
        item = Item('damage_bomb')
        result = item.use(player, None)
        
        assert result['success'] is False
        assert "only be used during combat" in result['message']
    
    def test_utility_items(self):
        """Test utility items (gold, escape scroll)."""
        player = Player(session_id="test", name="Test Hero")
        initial_gold = player.gold
        
        # Test gold coin bag
        item = Item('gold_coin_bag')
        result = item.use(player)
        
        assert result['success'] is True
        assert player.gold == initial_gold + 50
        assert 'gold_gained' in result
        
        # Test escape scroll
        item = Item('escape_scroll')
        result = item.use(player)
        
        assert result['success'] is True
        assert 'guaranteed_flee' in result
        assert result['guaranteed_flee'] is True
    
    def test_get_item_info(self):
        """Test get_item_info method."""
        item = Item('health_potion')
        info = item.get_item_info()
        
        assert 'item_id' in info
        assert 'name' in info
        assert 'description' in info
        assert 'effect_type' in info
        assert 'effect_value' in info
        assert 'usable_in_combat' in info
        assert 'rarity' in info
    
    @patch('random.choice')
    def test_get_random_item_type(self, mock_choice):
        """Test random item type generation."""
        mock_choice.return_value = 'health_potion'
        
        item_type = Item.get_random_item_type(floor=1)
        assert item_type == 'health_potion'
        
        # Test that choice was called with weighted items
        mock_choice.assert_called_once()
        weighted_items = mock_choice.call_args[0][0]
        assert 'health_potion' in weighted_items
        
        # Test higher floor (should affect rarity distribution)
        Item.get_random_item_type(floor=10)
        assert mock_choice.call_count == 2


class TestPlayerInventoryIntegration:
    """Test player inventory management integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.player = Player(session_id="test_session", name="Test Hero")
    
    def test_inventory_operations(self):
        """Test complete inventory operations."""
        item1 = Item('health_potion')
        item2 = Item('attack_boost')
        
        # Add items
        assert len(self.player.inventory) == 0
        self.player.add_item(item1)
        self.player.add_item(item2)
        assert len(self.player.inventory) == 2
        
        # Get item
        found_item = self.player.get_item(item1.item_id)
        assert found_item is not None
        assert found_item.item_id == item1.item_id
        
        # Remove item
        removed_item = self.player.remove_item(item1.item_id)
        assert removed_item is not None
        assert removed_item.item_id == item1.item_id
        assert len(self.player.inventory) == 1
        
        # Remove non-existent item
        removed_item = self.player.remove_item("nonexistent-id")
        assert removed_item is None
    
    def test_inventory_persistence(self):
        """Test inventory survives serialization/deserialization."""
        item1 = Item('health_potion')
        item2 = Item('defense_boost')
        self.player.add_item(item1)
        self.player.add_item(item2)
        
        # Serialize
        player_dict = self.player.to_dict()
        assert 'inventory' in player_dict
        assert len(player_dict['inventory']) == 2
        
        # Deserialize
        restored_player = Player.from_dict(player_dict)
        assert len(restored_player.inventory) == 2
        assert restored_player.inventory[0].name == item1.name
        assert restored_player.inventory[1].name == item2.name


class TestInventoryControllerIntegration:
    """Integration tests for inventory controller with real objects."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.controller = InventoryController()
        self.player = Player(session_id="test_session", name="Test Hero")
    
    def test_full_item_lifecycle(self):
        """Test complete item lifecycle: find, store, use."""
        # Simulate finding an item
        item = Item('health_potion')
        result = self.controller.add_item_to_inventory(self.player, item)
        
        assert result['error'] is False
        assert len(self.player.inventory) == 1
        
        # Damage player
        self.player.health = 40
        
        # Use the item
        success, result = self.controller.use_item(self.player, item.item_id)
        
        assert success is True
        assert self.player.health == 70  # 40 + 30
        assert len(self.player.inventory) == 0  # Item consumed
    
    def test_multiple_items_management(self):
        """Test managing multiple different items."""
        items = [
            Item('health_potion'),
            Item('attack_boost'),
            Item('defense_boost'),
            Item('gold_coin_bag')
        ]
        
        # Add all items
        for item in items:
            self.controller.add_item_to_inventory(self.player, item)
        
        assert len(self.player.inventory) == 4
        
        # Get inventory
        inventory_result = self.controller.get_inventory(self.player)
        assert inventory_result['data']['inventory_size'] == 4
        assert len(inventory_result['data']['grouped_inventory']) <= 4  # May be grouped
        
        # Use one item
        self.controller.use_item(self.player, items[0].item_id)
        assert len(self.player.inventory) == 3
        
        # Discard one item
        self.controller.discard_item(self.player, items[1].item_id)
        assert len(self.player.inventory) == 2
        
        # Get usable combat items
        usable_items = self.controller.get_usable_combat_items(self.player)
        # defense_boost is usable in combat, gold_coin_bag is not
        assert len(usable_items) == 1
    
    @patch('random.random')
    def test_item_finding_workflow(self, mock_random):
        """Test the complete item finding workflow."""
        mock_random.return_value = 0.5  # Ensure item is found
        
        with patch.object(Item, 'get_random_item_type', return_value='attack_boost'):
            # Try to find item in new room
            found, item = self.controller.roll_for_item_find(self.player, room_visited=False)
            
            assert found is True
            assert item is not None
            
            # Add found item to inventory
            result = self.controller.add_item_to_inventory(self.player, item)
            
            assert result['error'] is False
            assert len(self.player.inventory) == 1
            
            # Use the found item
            initial_attack = self.player.attack_power
            success, use_result = self.controller.use_item(self.player, item.item_id)
            
            assert success is True
            assert self.player.attack_power == initial_attack + 15
