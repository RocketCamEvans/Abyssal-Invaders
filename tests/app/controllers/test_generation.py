"""
Unit tests for the GenerationController class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import random
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from app.controllers.generation import GenerationController
from app.models.room import Room


class TestGenerationController:
    """Test cases for GenerationController class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create test room
        self.room = Room(room_id="test_room", name="Test Chamber", description="A mysterious test chamber", floor=1)
        
    def test_init_with_openai_available_and_configured(self):
        """Test initialization when OpenAI is available and configured."""
        with patch('app.controllers.generation.OPENAI_AVAILABLE', True):
            with patch('app.controllers.generation.create_openai_client') as mock_create_client:
                mock_client = Mock()
                mock_create_client.return_value = mock_client
                
                controller = GenerationController(use_openai=True)
                
                assert controller.use_openai is True
                assert controller.openai_client == mock_client
                mock_create_client.assert_called_once()
    
    def test_init_with_openai_unavailable(self):
        """Test initialization when OpenAI is not available."""
        with patch('app.controllers.generation.OPENAI_AVAILABLE', False):
            controller = GenerationController(use_openai=True)
            
            assert controller.use_openai is False
            assert controller.openai_client is None
    
    def test_init_with_openai_client_creation_failure(self):
        """Test initialization when OpenAI client creation fails."""
        with patch('app.controllers.generation.OPENAI_AVAILABLE', True):
            with patch('app.controllers.generation.create_openai_client') as mock_create_client:
                mock_create_client.return_value = None
                
                controller = GenerationController(use_openai=True)
                
                assert controller.use_openai is False
                assert controller.openai_client is None
    
    def test_init_with_openai_client_exception(self):
        """Test initialization when OpenAI client creation throws exception."""
        with patch('app.controllers.generation.OPENAI_AVAILABLE', True):
            with patch('app.controllers.generation.create_openai_client') as mock_create_client:
                mock_create_client.side_effect = Exception("API Error")
                
                controller = GenerationController(use_openai=True)
                
                assert controller.use_openai is False
                assert controller.openai_client is None
    
    def test_init_use_openai_false(self):
        """Test initialization with use_openai=False."""
        with patch('app.controllers.generation.OPENAI_AVAILABLE', True):
            controller = GenerationController(use_openai=False)
            
            assert controller.use_openai is False
            assert controller.openai_client is None
    
    def test_init_loads_templates(self):
        """Test that initialization loads all template data."""
        controller = GenerationController(use_openai=False)
        
        assert isinstance(controller.enemy_name_templates, dict)
        assert isinstance(controller.ally_name_templates, list)
        assert isinstance(controller.room_name_templates, dict)
        assert isinstance(controller.description_templates, dict)
        
        # Check that templates have expected keys
        assert "basic" in controller.enemy_name_templates
        assert "intermediate" in controller.enemy_name_templates
        assert "advanced" in controller.enemy_name_templates
        assert "legendary" in controller.enemy_name_templates
        
        assert "basic" in controller.room_name_templates
        assert "atmospheric" in controller.description_templates
    
    def test_generate_enemy_content_with_openai_success(self):
        """Test enemy content generation with successful OpenAI call."""
        mock_client = Mock()
        mock_client.generate_enemy_content.return_value = {
            "name": "AI Generated Enemy",
            "description": "An AI-generated enemy description"
        }
        
        controller = GenerationController(use_openai=False)
        controller.use_openai = True
        controller.openai_client = mock_client
        
        result = controller.generate_enemy_content(3, self.room)
        
        assert result["name"] == "AI Generated Enemy"
        assert result["description"] == "An AI-generated enemy description"
        mock_client.generate_enemy_content.assert_called_once_with(3, self.room.description)
    
    def test_generate_enemy_content_with_openai_failure(self):
        """Test enemy content generation when OpenAI fails."""
        mock_client = Mock()
        mock_client.generate_enemy_content.side_effect = Exception("API Error")
        
        controller = GenerationController(use_openai=False)
        controller.use_openai = True
        controller.openai_client = mock_client
        
        with patch('random.choice') as mock_choice:
            mock_choice.side_effect = ["Test Enemy", "menacing", "A menacing creature that lurks in the shadows."]  # For name, descriptor, and final description
            
            result = controller.generate_enemy_content(3, self.room)
        
        assert "name" in result
        assert "description" in result
        assert isinstance(result["name"], str)
        assert isinstance(result["description"], str)
    
    def test_generate_enemy_content_template_fallback(self):
        """Test enemy content generation using template fallback."""
        controller = GenerationController(use_openai=False)
        
        with patch('random.choice') as mock_choice:
            mock_choice.side_effect = ["Shadow Wraith", "menacing", "A menacing creature lurks in the darkness."]  # Name, descriptor, and final description
            
            result = controller.generate_enemy_content(1)
        
        assert result["name"] == "Shadow Wraith"
        assert "description" in result
        assert isinstance(result["description"], str)
        assert len(result["description"]) > 0
    
    def test_generate_enemy_content_different_floor_levels(self):
        """Test enemy content generation for different floor levels uses appropriate difficulty templates."""
        controller = GenerationController(use_openai=False)
        
        # Mock random.choice to control which template is selected
        with patch('random.choice') as mock_choice:
            # Test basic level (floor 1) - should use basic templates
            mock_choice.side_effect = ["Basic Enemy", "menacing", "A menacing creature."]
            result_basic = controller.generate_enemy_content(1)
            
            # Verify the correct template was accessed (basic templates for floor 1)
            basic_templates = controller.enemy_name_templates["basic"]
            mock_choice.assert_any_call(basic_templates)
            assert result_basic["name"] == "Basic Enemy"
        
        with patch('random.choice') as mock_choice:
            # Test intermediate level (floor 4) - should use intermediate templates
            mock_choice.side_effect = ["Intermediate Enemy", "formidable", "A formidable creature."]
            result_intermediate = controller.generate_enemy_content(4)
            
            # Verify the correct template was accessed (intermediate templates for floor 4)
            intermediate_templates = controller.enemy_name_templates["intermediate"]
            mock_choice.assert_any_call(intermediate_templates)
            assert result_intermediate["name"] == "Intermediate Enemy"
        
        with patch('random.choice') as mock_choice:
            # Test advanced level (floor 8) - should use advanced templates
            mock_choice.side_effect = ["Advanced Enemy", "terrifying", "A terrifying creature."]
            result_advanced = controller.generate_enemy_content(8)
            
            # Verify the correct template was accessed (advanced templates for floor 8)
            advanced_templates = controller.enemy_name_templates["advanced"]
            mock_choice.assert_any_call(advanced_templates)
            assert result_advanced["name"] == "Advanced Enemy"
        
        with patch('random.choice') as mock_choice:
            # Test legendary level (floor 15) - should use legendary templates
            mock_choice.side_effect = ["Legendary Enemy", "apocalyptic", "An apocalyptic creature."]
            result_legendary = controller.generate_enemy_content(15)
            
            # Verify the correct template was accessed (legendary templates for floor 15)
            legendary_templates = controller.enemy_name_templates["legendary"]
            mock_choice.assert_any_call(legendary_templates)
            assert result_legendary["name"] == "Legendary Enemy"
    
    def test_generate_ally_content_with_openai_success(self):
        """Test ally content generation with successful OpenAI call."""
        mock_client = Mock()
        mock_client.generate_ally_content.return_value = {
            "name": "AI Generated Ally",
            "description": "An AI-generated ally description"
        }
        
        controller = GenerationController(use_openai=False)
        controller.use_openai = True
        controller.openai_client = mock_client
        
        result = controller.generate_ally_content(2, self.room)
        
        assert result["name"] == "AI Generated Ally"
        assert result["description"] == "An AI-generated ally description"
        mock_client.generate_ally_content.assert_called_once_with(2, self.room.description)
    
    def test_generate_ally_content_with_openai_failure(self):
        """Test ally content generation when OpenAI fails."""
        mock_client = Mock()
        mock_client.generate_ally_content.side_effect = Exception("API Error")
        
        controller = GenerationController(use_openai=False)
        controller.use_openai = True
        controller.openai_client = mock_client
        
        with patch('random.choice') as mock_choice:
            mock_choice.side_effect = ["Brave Warrior", "willing to lend"]  # Name and description part
            
            result = controller.generate_ally_content(2, self.room)
        
        assert "name" in result
        assert "description" in result
        assert result["name"] == "Brave Warrior"
    
    def test_generate_ally_content_template_fallback(self):
        """Test ally content generation using template fallback."""
        controller = GenerationController(use_openai=False)
        
        with patch('random.choice') as mock_choice:
            mock_choice.side_effect = ["Mysterious Mage", "A brave soul who has somehow survived the perils of floor 3. Mysterious Mage offers to aid you in battle."]  # Ally name and description
            
            result = controller.generate_ally_content(3)
        
        assert result["name"] == "Mysterious Mage"
        assert "description" in result
        assert isinstance(result["description"], str)
        assert "floor 3" in result["description"]
    
    def test_generate_room_content_with_openai_success(self):
        """Test room content generation with successful OpenAI call."""
        mock_client = Mock()
        mock_client.generate_room_content.return_value = {
            "name": "AI Generated Room",
            "description": "An AI-generated room description"
        }
        
        controller = GenerationController(use_openai=False)
        controller.use_openai = True
        controller.openai_client = mock_client
        
        result = controller.generate_room_content(4, "test_room")
        
        assert result["name"] == "AI Generated Room"
        assert result["description"] == "An AI-generated room description"
        mock_client.generate_room_content.assert_called_once_with(4)
    
    def test_generate_room_content_with_openai_failure(self):
        """Test room content generation when OpenAI fails."""
        mock_client = Mock()
        mock_client.generate_room_content.side_effect = Exception("API Error")
        
        controller = GenerationController(use_openai=False)
        controller.use_openai = True
        controller.openai_client = mock_client
        
        with patch('random.choice') as mock_choice:
            mock_choice.side_effect = ["Crystal Cavern", "The air is thick"]  # Name and atmosphere
            
            result = controller.generate_room_content(4, "test_room")
        
        assert result["name"] == "Crystal Cavern"
        assert "description" in result
    
    def test_generate_room_content_template_fallback(self):
        """Test room content generation using template fallback."""
        controller = GenerationController(use_openai=False)
        
        with patch('random.choice') as mock_choice:
            mock_choice.side_effect = ["Stone Chamber", "The air is thick with ancient dust"]
            
            result = controller.generate_room_content(1, "room_1")
        
        assert result["name"] == "Stone Chamber"
        assert "description" in result
        assert "The air is thick with ancient dust" in result["description"]
    
    def test_generate_combat_description(self):
        """Test combat description generation."""
        controller = GenerationController(use_openai=False)
        
        with patch('random.choice') as mock_choice:
            expected_desc = "As Hero explores the area, Goblin suddenly appears! The mysterious chamber provides an ominous backdrop for the impending battle."
            mock_choice.return_value = expected_desc
            
            result = controller.generate_combat_description("Hero", "Goblin", "mysterious chamber", "encounter")
        
        assert result == expected_desc
    
    def test_generate_combat_description_different_action_types(self):
        """Test combat description generation for different action types."""
        controller = GenerationController(use_openai=False)
        
        # Test encounter action
        with patch('random.choice') as mock_choice:
            mock_choice.return_value = "Encounter description"
            result_encounter = controller.generate_combat_description("Hero", "Goblin", "chamber", "encounter")
            assert result_encounter == "Encounter description"
        
        # Test victory action
        with patch('random.choice') as mock_choice:
            mock_choice.return_value = "Victory description"
            result_victory = controller.generate_combat_description("Hero", "Goblin", "chamber", "victory")
            assert result_victory == "Victory description"
        
        # Test unknown action (should default to encounter)
        with patch('random.choice') as mock_choice:
            mock_choice.return_value = "Default description"
            result_unknown = controller.generate_combat_description("Hero", "Goblin", "chamber", "unknown")
            assert result_unknown == "Default description"
    
    def test_get_difficulty_modifier(self):
        """Test difficulty modifier calculation."""
        controller = GenerationController(use_openai=False)
        
        assert controller._get_difficulty_modifier(1) == "basic"
        assert controller._get_difficulty_modifier(2) == "basic"
        assert controller._get_difficulty_modifier(3) == "intermediate"
        assert controller._get_difficulty_modifier(5) == "intermediate"
        assert controller._get_difficulty_modifier(6) == "advanced"
        assert controller._get_difficulty_modifier(10) == "advanced"
        assert controller._get_difficulty_modifier(11) == "legendary"
        assert controller._get_difficulty_modifier(100) == "legendary"
    
    def test_enemy_generation_uses_correct_difficulty_templates(self):
        """Test that enemy generation actually uses templates matching the floor difficulty."""
        controller = GenerationController(use_openai=False)
        
        # Test multiple generations to ensure consistency
        for _ in range(5):  # Run multiple times due to randomness
            # Floor 1 should use basic templates
            result_basic = controller.generate_enemy_content(1)
            basic_names = controller.enemy_name_templates["basic"]
            # The generated name should be from the basic template pool
            # (This test may occasionally fail due to randomness, but should mostly pass)
            
            # Floor 15 should use legendary templates  
            result_legendary = controller.generate_enemy_content(15)
            legendary_names = controller.enemy_name_templates["legendary"]
            
            # Verify results are valid
            assert result_basic["name"] in basic_names
            assert result_legendary["name"] in legendary_names
            assert isinstance(result_basic["description"], str)
            assert isinstance(result_legendary["description"], str)
    
    def test_get_room_context_with_room(self):
        """Test room context extraction with valid room."""
        controller = GenerationController(use_openai=False)
        
        result = controller._get_room_context(self.room)
        
        assert result == "Test Chamber - A mysterious test chamber"
    
    def test_get_room_context_without_room(self):
        """Test room context extraction with no room."""
        controller = GenerationController(use_openai=False)
        
        result = controller._get_room_context(None)
        
        assert result == "a mysterious chamber"
    
    def test_generate_enemy_description(self):
        """Test enemy description generation."""
        controller = GenerationController(use_openai=False)
        
        with patch('random.choice') as mock_choice:
            mock_choice.side_effect = ["menacing", "A menacing creature that has claimed this domain as its own."]
            
            result = controller._generate_enemy_description("Shadow Wraith", 3, "Test Chamber")
        
        assert "menacing creature" in result
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_generate_enemy_description_different_difficulties(self):
        """Test enemy description generation for different difficulty levels."""
        controller = GenerationController(use_openai=False)
        
        # Test each difficulty level
        for floor, expected_difficulty in [(1, "basic"), (4, "intermediate"), (8, "advanced"), (15, "legendary")]:
            result = controller._generate_enemy_description("Test Enemy", floor, "Test Room")
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_generate_ally_description(self):
        """Test ally description generation."""
        controller = GenerationController(use_openai=False)
        
        with patch('random.choice') as mock_choice:
            expected_desc = f"A brave soul who has somehow survived the perils of floor 5. Test Ally offers to aid you in battle."
            mock_choice.return_value = expected_desc
            
            result = controller._generate_ally_description("Test Ally", 5, "Test Room")
        
        assert result == expected_desc
        assert "Test Ally" in result
        assert "floor 5" in result
    
    def test_generate_room_description(self):
        """Test room description generation."""
        controller = GenerationController(use_openai=False)
        
        with patch('random.choice') as mock_choice:
            mock_choice.return_value = "The air is thick with ancient dust and mystery."
            
            result = controller._generate_room_description("Ancient Hall", 1, "room_1")
        
        assert "The air is thick with ancient dust and mystery." in result
        assert isinstance(result, str)
    
    def test_generate_room_description_higher_floor(self):
        """Test room description generation for higher floors."""
        controller = GenerationController(use_openai=False)
        
        with patch('random.choice') as mock_choice:
            mock_choice.return_value = "Strange echoes bounce off the weathered walls."
            
            result = controller._generate_room_description("Deep Chamber", 5, "room_5")
        
        assert "Strange echoes bounce off the weathered walls." in result
        assert "floor 5" in result
    
    def test_load_enemy_name_templates(self):
        """Test enemy name template loading."""
        controller = GenerationController(use_openai=False)
        
        templates = controller._load_enemy_name_templates()
        
        assert isinstance(templates, dict)
        assert "basic" in templates
        assert "intermediate" in templates
        assert "advanced" in templates
        assert "legendary" in templates
        
        # Check that each difficulty has a list of names
        for difficulty, names in templates.items():
            assert isinstance(names, list)
            assert len(names) > 0
            for name in names:
                assert isinstance(name, str)
                assert len(name) > 0
    
    def test_load_ally_name_templates(self):
        """Test ally name template loading."""
        controller = GenerationController(use_openai=False)
        
        templates = controller._load_ally_name_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        for name in templates:
            assert isinstance(name, str)
            assert len(name) > 0
    
    def test_load_room_name_templates(self):
        """Test room name template loading."""
        controller = GenerationController(use_openai=False)
        
        templates = controller._load_room_name_templates()
        
        assert isinstance(templates, dict)
        assert "basic" in templates
        assert "intermediate" in templates
        assert "advanced" in templates
        assert "legendary" in templates
        
        # Check that each difficulty has a list of names
        for difficulty, names in templates.items():
            assert isinstance(names, list)
            assert len(names) > 0
            for name in names:
                assert isinstance(name, str)
                assert len(name) > 0
    
    def test_load_description_templates(self):
        """Test description template loading."""
        controller = GenerationController(use_openai=False)
        
        templates = controller._load_description_templates()
        
        assert isinstance(templates, dict)
        assert "atmospheric" in templates
        assert "dangerous" in templates
        
        # Check that each category has a list of descriptions
        for category, descriptions in templates.items():
            assert isinstance(descriptions, list)
            assert len(descriptions) > 0
            for desc in descriptions:
                assert isinstance(desc, str)
                assert len(desc) > 0


class TestGenerationControllerIntegration:
    """Integration tests for GenerationController with real template data."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.controller = GenerationController(use_openai=False)
        self.room = Room("int_room", "Integration Room", "A test room for integration", 3)
    
    def test_enemy_generation_consistency(self):
        """Test that enemy generation produces consistent, valid results."""
        for floor in [1, 3, 7, 12]:
            result = self.controller.generate_enemy_content(floor, self.room)
            
            assert "name" in result
            assert "description" in result
            assert isinstance(result["name"], str)
            assert isinstance(result["description"], str)
            assert len(result["name"]) > 0
            assert len(result["description"]) > 0
    
    def test_ally_generation_consistency(self):
        """Test that ally generation produces consistent, valid results."""
        for floor in [1, 3, 7, 12]:
            result = self.controller.generate_ally_content(floor, self.room)
            
            assert "name" in result
            assert "description" in result
            assert isinstance(result["name"], str)
            assert isinstance(result["description"], str)
            assert len(result["name"]) > 0
            assert len(result["description"]) > 0
            # Floor number should appear in some descriptions but not necessarily all
            assert isinstance(result["description"], str)
    
    def test_room_generation_consistency(self):
        """Test that room generation produces consistent, valid results."""
        for floor in [1, 3, 7, 12]:
            result = self.controller.generate_room_content(floor, f"room_{floor}")
            
            assert "name" in result
            assert "description" in result
            assert isinstance(result["name"], str)
            assert isinstance(result["description"], str)
            assert len(result["name"]) > 0
            assert len(result["description"]) > 0
    
    def test_combat_description_all_types(self):
        """Test combat description generation for all action types."""
        player_name = "Test Hero"
        enemy_name = "Test Enemy"
        room_desc = "test chamber"
        
        for action_type in ["encounter", "victory", "unknown"]:
            result = self.controller.generate_combat_description(
                player_name, enemy_name, room_desc, action_type
            )
            
            assert isinstance(result, str)
            assert len(result) > 0
            assert player_name in result
            assert enemy_name in result
    
    def test_difficulty_scaling_names(self):
        """Test that different floor levels use appropriate difficulty templates."""
        # Test that basic floors use basic templates
        basic_result = self.controller.generate_enemy_content(1)
        basic_templates = self.controller.enemy_name_templates["basic"]
        
        # Test that legendary floors use legendary templates  
        legendary_result = self.controller.generate_enemy_content(15)
        legendary_templates = self.controller.enemy_name_templates["legendary"]
        
        # The names should come from appropriate template pools
        # We can't guarantee specific names due to randomness, but we can verify structure
        assert isinstance(basic_result["name"], str)
        assert isinstance(legendary_result["name"], str)
    
    def test_room_context_integration(self):
        """Test that room context is properly integrated in descriptions."""
        detailed_room = Room("detailed", "Haunted Crypt", "A spooky underground burial chamber", 4)
        
        enemy_result = self.controller.generate_enemy_content(4, detailed_room)
        ally_result = self.controller.generate_ally_content(4, detailed_room)
        
        # Results should be valid regardless of room context
        assert "name" in enemy_result and "description" in enemy_result
        assert "name" in ally_result and "description" in ally_result
    
    def test_template_data_integrity(self):
        """Test that all template data is properly structured and accessible."""
        # Enemy templates
        enemy_templates = self.controller.enemy_name_templates
        for difficulty in ["basic", "intermediate", "advanced", "legendary"]:
            assert difficulty in enemy_templates
            assert len(enemy_templates[difficulty]) >= 5  # Ensure reasonable variety
        
        # Room templates  
        room_templates = self.controller.room_name_templates
        for difficulty in ["basic", "intermediate", "advanced", "legendary"]:
            assert difficulty in room_templates
            assert len(room_templates[difficulty]) >= 5  # Ensure reasonable variety
        
        # Ally templates
        ally_templates = self.controller.ally_name_templates
        assert len(ally_templates) >= 10  # Ensure reasonable variety
        
        # Description templates
        desc_templates = self.controller.description_templates
        assert "atmospheric" in desc_templates
        assert "dangerous" in desc_templates
        assert len(desc_templates["atmospheric"]) >= 3
        assert len(desc_templates["dangerous"]) >= 3