"""
Unit tests for the CombatController class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import random
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from app.controllers.combat import CombatController
from app.models.player import Player
from app.models.enemy import Enemy
from app.models.room import Room


class TestCombatController:
    """Test cases for CombatController class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.controller = CombatController()
        
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
        
        # Create test room
        self.room = Room(room_id="test_room", name="Test Chamber", description="A test room", floor=1)
        
    def test_init_with_openai_available(self):
        """Test CombatController initialization when OpenAI is available."""
        with patch('app.controllers.combat.OPENAI_AVAILABLE', True):
            # Import the combat module to access the actual imported function
            from app.controllers import combat
            with patch.object(combat, 'create_openai_client') as mock_create_client:
                mock_client = Mock()
                mock_create_client.return_value = mock_client
                
                controller = CombatController()
                
                assert controller.openai_client == mock_client
                mock_create_client.assert_called_once()
    
    def test_init_with_openai_unavailable(self):
        """Test CombatController initialization when OpenAI is not available."""
        with patch('app.controllers.combat.OPENAI_AVAILABLE', False):
            controller = CombatController()
            assert controller.openai_client is None
    
    def test_initiate_combat_player_already_defeated(self):
        """Test initiating combat when player is already defeated."""
        self.player.health = 0
        
        _, _, result = self.controller.initiate_combat(self.player, self.enemy, self.room)
        
        assert result["error"] is True
        assert "already defeated" in result["message"]
    
    @patch('app.controllers.combat.random.choice')
    def test_initiate_combat_successful_player_victory(self, mock_choice):
        """Test successful combat initiation where player wins."""
        # Mock random choice for combat description
        mock_choice.return_value = f"Test combat description with {self.enemy.name}"
        
        # Mock the combat to ensure player wins (enemy dies first)
        original_enemy_health = self.enemy.health
        
        with patch.object(self.controller, '_execute_combat_round') as mock_round:
            # Simulate enemy dying after one round
            def side_effect(player, enemy, round_num):
                enemy.health = 0  # Kill enemy
                return {
                    "round": round_num,
                    "player_action": {"action": "attack", "damage_dealt": 25, "target_health_remaining": 0},
                    "enemy_action": {"action": "defeated", "damage_dealt": 0, "target_health_remaining": player.health},
                    "summary": f"Test round {round_num} summary"
                }
            
            mock_round.side_effect = side_effect
            
            player, enemy, result = self.controller.initiate_combat(self.player, self.enemy, self.room)
        
        assert result["error"] is False
        assert result["data"]["winner"] == "player"
        assert "victory" in result["data"]["result"]["outcome"]
        assert result["data"]["final_enemy_health"] == 0
    
    def test_start_battle_player_defeated(self):
        """Test starting battle when player is already defeated."""
        self.player.health = 0
        
        result = self.controller.start_battle(self.player, self.enemy, self.room)
        
        assert result["error"] is True
        assert "already defeated" in result["message"]
    
    @patch('app.controllers.combat.CombatController._generate_ai_battle_description')
    def test_start_battle_successful(self, mock_description):
        """Test successful battle start."""
        mock_description.return_value = "Epic battle begins!"
        
        result = self.controller.start_battle(self.player, self.enemy, self.room)
        
        assert result["error"] is False
        assert result["data"]["message"] == "Battle started!"
        assert result["data"]["description"] == "Epic battle begins!"
        assert result["data"]["player_health"] == self.player.health
        assert result["data"]["enemy_health"] == self.enemy.health
        assert self.player.in_battle is True
        assert self.player.current_enemy is not None
    
    def test_start_battle_with_ally(self):
        """Test starting battle with ally present."""
        ally_data = {"name": "Test Ally", "attack_power": 10}
        
        with patch.object(self.controller, '_generate_ai_battle_description') as mock_desc:
            mock_desc.return_value = "Battle with ally!"
            
            result = self.controller.start_battle(self.player, self.enemy, self.room, ally_data)
        
        assert result["error"] is False
        assert result["data"]["ally_available"] is True
        assert result["data"]["ally_name"] == "Test Ally"
        assert self.player.current_ally == ally_data
    
    def test_execute_attack_not_in_battle(self):
        """Test executing attack when player is not in battle."""
        result = self.controller.execute_attack(self.player)
        
        assert result["error"] is True
        assert "not in battle" in result["message"]
    
    @patch('app.controllers.combat.CombatController._check_critical_hit')
    @patch('app.controllers.combat.calculate_damage_with_variance')
    def test_execute_attack_player_victory(self, mock_damage, mock_crit):
        """Test executing attack that results in player victory."""
        # Set up battle state
        self.player.start_battle(self.enemy.to_dict(), self.room.to_dict())
        
        # Mock damage calculation and no critical hit
        mock_damage.return_value = 50  # Enough to kill enemy
        mock_crit.return_value = False
        
        with patch.object(self.controller, '_handle_enemy_defeat') as mock_victory:
            mock_victory.return_value = {
                "outcome": "victory",
                "gold_earned": 25,
                "exp_earned": 30,
                "leveled_up": False,
                "total_gold": 75,
                "message": "Victory!"
            }
            
            result = self.controller.execute_attack(self.player)
        
        assert result["error"] is False
        assert result["data"]["battle_ended"] is True
        assert result["data"]["victory"] is True
        assert "reward" in result["data"]
        assert self.player.in_battle is False
    
    def test_execute_attack_with_ally(self):
        """Test executing attack using ally special move."""
        ally_data = {"name": "Test Ally", "attack_power": 15}
        self.player.start_battle(self.enemy.to_dict(), self.room.to_dict(), ally_data)
        
        with patch.object(self.controller, '_execute_ally_attack') as mock_ally_attack:
            with patch.object(self.controller, '_execute_enemy_attack') as mock_enemy_attack:
                mock_ally_attack.return_value = 20
                mock_enemy_attack.return_value = 8
                
                result = self.controller.execute_attack(self.player, use_ally=True)
        
        assert result["error"] is False
        assert self.player.ally_used is True
        mock_ally_attack.assert_called_once()
    
    def test_execute_attack_ally_already_used(self):
        """Test executing attack when ally has already been used."""
        ally_data = {"name": "Test Ally", "attack_power": 15}
        self.player.start_battle(self.enemy.to_dict(), self.room.to_dict(), ally_data)
        self.player.ally_used = True
        
        with patch.object(self.controller, '_execute_player_attack') as mock_player_attack:
            with patch.object(self.controller, '_execute_enemy_attack') as mock_enemy_attack:
                mock_player_attack.return_value = 15
                mock_enemy_attack.return_value = 8
                
                result = self.controller.execute_attack(self.player, use_ally=True)
        
        # Should use regular attack since ally was already used
        mock_player_attack.assert_called_once()
        assert result["error"] is False
    
    def test_execute_flee_not_in_battle(self):
        """Test fleeing when not in battle."""
        result = self.controller.execute_flee(self.player)
        
        assert result["error"] is True
        assert "not in battle" in result["message"]
    
    def test_execute_flee_successful(self):
        """Test successful fleeing from battle."""
        original_gold = self.player.gold
        self.player.start_battle(self.enemy.to_dict(), self.room.to_dict())
        
        result = self.controller.execute_flee(self.player)
        
        assert result["error"] is False
        assert result["data"]["battle_ended"] is True
        assert result["data"]["gold_lost"] == original_gold // 2
        assert self.player.in_battle is False
    
    def test_generate_ai_battle_description_with_openai(self):
        """Test AI battle description generation with OpenAI client."""
        mock_client = Mock()
        mock_client.generate_completion.return_value = "Epic AI-generated description!"
        self.controller.openai_client = mock_client
        
        result = self.controller._generate_ai_battle_description(self.player, self.enemy, self.room)
        
        assert result == "Epic AI-generated description!"
        mock_client.generate_completion.assert_called_once()
    
    def test_generate_ai_battle_description_without_openai(self):
        """Test AI battle description generation without OpenAI client."""
        self.controller.openai_client = None
        
        result = self.controller._generate_ai_battle_description(self.player, self.enemy, self.room)
        
        # Should return fallback description
        assert self.player.name in result
        assert self.enemy.name in result
        assert self.room.name in result
    
    def test_generate_ai_battle_description_openai_error(self):
        """Test AI battle description when OpenAI throws an exception."""
        mock_client = Mock()
        mock_client.generate_completion.side_effect = Exception("API Error")
        self.controller.openai_client = mock_client
        
        result = self.controller._generate_ai_battle_description(self.player, self.enemy, self.room)
        
        # Should return fallback description
        assert self.player.name in result
        assert self.enemy.name in result
    
    def test_generate_critical_hit_description_with_openai(self):
        """Test critical hit description with OpenAI."""
        mock_client = Mock()
        mock_client.generate_completion.return_value = "A devastating critical strike!"
        self.controller.openai_client = mock_client
        
        result = self.controller._generate_critical_hit_description("Hero", "Goblin", 25, True)
        
        assert result == "A devastating critical strike!"
    
    def test_generate_critical_hit_description_without_openai(self):
        """Test critical hit description without OpenAI."""
        self.controller.openai_client = None
        
        with patch('app.controllers.combat.random.choice') as mock_choice:
            mock_choice.return_value = "A perfect strike finds its mark!"
            
            result = self.controller._generate_critical_hit_description("Hero", "Goblin", 25, True)
            
            assert result == "A perfect strike finds its mark!"
    
    @patch('app.controllers.combat.random.random')
    def test_check_critical_hit_true(self, mock_random):
        """Test critical hit check returning True."""
        mock_random.return_value = 0.05  # Less than 10% threshold
        
        result = self.controller._check_critical_hit()
        
        assert result is True
    
    @patch('app.controllers.combat.random.random')
    def test_check_critical_hit_false(self, mock_random):
        """Test critical hit check returning False."""
        mock_random.return_value = 0.15  # Greater than 10% threshold
        
        result = self.controller._check_critical_hit()
        
        assert result is False
    
    @patch('app.controllers.combat.calculate_damage_with_variance')
    def test_execute_ally_attack(self, mock_damage):
        """Test executing ally attack."""
        ally_data = {"name": "Test Ally", "attack_power": 12}
        self.player.current_ally = ally_data
        battle_log = []
        mock_damage.return_value = 20
        
        with patch.object(self.controller, '_check_critical_hit') as mock_crit:
            mock_crit.return_value = False
            
            damage = self.controller._execute_ally_attack(self.player, self.enemy, battle_log)
        
        assert damage == 20
        assert len(battle_log) == 1
        assert battle_log[0]["type"] == "ally_attack"
        assert battle_log[0]["attacker"] == f"{self.player.name} with {ally_data['name']}"
        assert battle_log[0]["is_critical"] is False
    
    @patch('app.controllers.combat.calculate_damage_with_variance')
    def test_execute_ally_attack_critical(self, mock_damage):
        """Test executing ally attack with critical hit."""
        ally_data = {"name": "Test Ally", "attack_power": 12}
        self.player.current_ally = ally_data
        battle_log = []
        mock_damage.return_value = 30  # Critical damage
        
        with patch.object(self.controller, '_check_critical_hit') as mock_crit:
            with patch.object(self.controller, '_generate_critical_hit_description') as mock_desc:
                mock_crit.return_value = True
                mock_desc.return_value = "Critical strike!"
                
                damage = self.controller._execute_ally_attack(self.player, self.enemy, battle_log)
        
        assert damage == 30
        assert battle_log[0]["is_critical"] is True
        assert "CRITICAL HIT" in battle_log[0]["description"]
    
    @patch('app.controllers.combat.calculate_damage_with_variance')
    def test_execute_player_attack(self, mock_damage):
        """Test executing regular player attack."""
        battle_log = []
        mock_damage.return_value = 18
        
        with patch.object(self.controller, '_check_critical_hit') as mock_crit:
            mock_crit.return_value = False
            
            damage = self.controller._execute_player_attack(self.player, self.enemy, battle_log)
        
        assert damage == 18
        assert len(battle_log) == 1
        assert battle_log[0]["type"] == "player_attack"
        assert battle_log[0]["is_critical"] is False
    
    @patch('app.controllers.combat.calculate_damage_with_variance')
    def test_execute_enemy_attack(self, mock_damage):
        """Test executing enemy attack."""
        battle_log = []
        mock_damage.return_value = 10
        
        with patch.object(self.controller, '_check_critical_hit') as mock_crit:
            mock_crit.return_value = False
            
            damage = self.controller._execute_enemy_attack(self.player, self.enemy, battle_log)
        
        assert damage == 10
        assert len(battle_log) == 1
        assert battle_log[0]["type"] == "enemy_attack"
        assert battle_log[0]["attacker"] == self.enemy.name
    
    def test_handle_player_defeat(self):
        """Test handling player defeat."""
        original_gold = self.player.gold
        self.player.health = 0
        
        result = self.controller._handle_player_defeat(self.player, self.enemy)
        
        assert result["outcome"] == "defeat"
        assert result["gold_lost"] <= original_gold // 4  # Max 25% loss
        assert result["gold_lost"] <= 50  # Max 50 gold loss
        assert self.player.health == 1  # Reset to 1, not 0
        assert result["remaining_gold"] == self.player.gold
    
    @patch('app.controllers.combat.random.random')
    def test_handle_enemy_defeat_no_healing(self, mock_random):
        """Test handling enemy defeat without healing found."""
        mock_random.return_value = 0.5  # Greater than 20% healing chance
        original_gold = self.player.gold
        original_exp = self.player.experience
        
        result = self.controller._handle_enemy_defeat(self.player, self.enemy)
        
        assert result["outcome"] == "victory"
        assert result["gold_earned"] > 0
        assert result["exp_earned"] > 0
        assert self.player.gold > original_gold
        assert self.player.experience > original_exp
        assert result["healing_found"] == 0
    
    @patch('app.controllers.combat.random.random')
    @patch('app.controllers.combat.random.randint')
    def test_handle_enemy_defeat_with_healing(self, mock_randint, mock_random):
        """Test handling enemy defeat with healing found."""
        mock_random.return_value = 0.1  # Less than 20% healing chance
        mock_randint.return_value = 15  # Healing amount
        original_health = self.player.health
        
        result = self.controller._handle_enemy_defeat(self.player, self.enemy)
        
        assert result["healing_found"] == 15
        assert self.player.health == min(self.player.max_health, original_health + 15)
    
    def test_handle_enemy_defeat_level_up(self):
        """Test handling enemy defeat that causes level up."""
        # Set player close to leveling up
        self.player.experience = 90  # Need 100 for level 2
        
        with patch.object(self.player, 'gain_experience') as mock_gain_exp:
            mock_gain_exp.return_value = True  # Indicates level up
            
            result = self.controller._handle_enemy_defeat(self.player, self.enemy)
        
        assert result["leveled_up"] is True
        assert "LEVEL UP" in result["message"]
    
    @patch('app.controllers.combat.random.choice')
    def test_generate_combat_description(self, mock_choice):
        """Test generating combat description."""
        expected_desc = f"Test description with {self.enemy.name}"
        mock_choice.return_value = expected_desc
        
        result = self.controller._generate_combat_description(self.player, self.enemy, self.room)
        
        assert result == expected_desc
    
    def test_check_encounter_chance(self):
        """Test checking encounter chance."""
        with patch.object(self.room, 'roll_for_encounter') as mock_roll:
            mock_roll.return_value = True
            
            result = self.controller.check_encounter_chance(self.room)
            
            assert result is True
            mock_roll.assert_called_once()
    
    @patch('app.controllers.combat.random.random')
    def test_flee_from_combat_successful(self, mock_random):
        """Test successful flee from combat."""
        mock_random.return_value = 0.6  # Within flee chance range
        
        success, result = self.controller.flee_from_combat(self.player, self.enemy)
        
        assert success is True
        assert result["error"] is False
        assert "successfully fled" in result["data"]["message"]
    
    @patch('app.controllers.combat.random.random')
    def test_flee_from_combat_failed(self, mock_random):
        """Test failed flee from combat."""
        mock_random.return_value = 1.0  # Above flee chance (fails)
        original_health = self.player.health
        
        with patch.object(self.controller, '_calculate_enemy_damage') as mock_damage:
            mock_damage.return_value = 10
            
            success, result = self.controller.flee_from_combat(self.player, self.enemy)
        
        assert success is False
        assert result["error"] is True
        assert "Failed to flee" in result["message"]
        # Account for player defense: actual damage = max(0, 10 - 5) = 5
        assert self.player.health == original_health - 5
    
    def test_use_ally_in_combat_invalid_index(self):
        """Test using ally with invalid index."""
        success, result = self.controller.use_ally_in_combat(self.player, -1, self.enemy)
        
        assert success is False
        assert result["error"] is True
        assert "Invalid ally selection" in result["message"]
    
    def test_use_ally_in_combat_valid(self):
        """Test using ally with valid ally object."""
        # Create a mock ally
        mock_ally = Mock()
        mock_ally.is_available.return_value = True
        mock_ally.use_attack.return_value = 20
        mock_ally.name = "Test Ally"
        mock_ally.description = "A helpful ally"
        
        self.player.allies = [mock_ally]
        
        success, result = self.controller.use_ally_in_combat(self.player, 0, self.enemy)
        
        assert success is True
        assert result["error"] is False
        assert result["data"]["ally_name"] == "Test Ally"
        assert result["data"]["damage_dealt"] == 20
        assert len(self.player.allies) == 0  # Ally should be removed after use
    
    @patch('app.controllers.combat.calculate_damage_with_variance')
    @patch('app.controllers.combat.roll_dice')
    def test_calculate_player_damage_normal(self, mock_roll, mock_variance):
        """Test calculating player damage without critical hit."""
        mock_variance.return_value = 12
        mock_roll.return_value = 50  # Above critical hit threshold
        
        damage = self.controller._calculate_player_damage(self.player)
        
        assert damage == 12
        mock_variance.assert_called_with(self.player.attack_power, 0.25)
    
    @patch('app.controllers.combat.calculate_damage_with_variance')
    @patch('app.controllers.combat.roll_dice')
    def test_calculate_player_damage_critical(self, mock_roll, mock_variance):
        """Test calculating player damage with critical hit."""
        mock_variance.return_value = 12
        mock_roll.return_value = 5  # Below critical hit threshold (10%)
        
        damage = self.controller._calculate_player_damage(self.player)
        
        assert damage == 18  # 12 * 1.5 = 18
    
    def test_calculate_enemy_damage(self):
        """Test calculating enemy damage."""
        with patch.object(self.enemy, 'attack') as mock_attack:
            mock_attack.return_value = 8
            
            damage = self.controller._calculate_enemy_damage(self.enemy)
            
            assert damage == 8
            mock_attack.assert_called_once()
    
    def test_execute_combat_round(self):
        """Test executing a complete combat round."""
        with patch.object(self.controller, '_calculate_player_damage') as mock_player_dmg:
            with patch.object(self.controller, '_calculate_enemy_damage') as mock_enemy_dmg:
                with patch('app.controllers.combat.format_combat_summary') as mock_summary:
                    mock_player_dmg.return_value = 15
                    mock_enemy_dmg.return_value = 8
                    mock_summary.return_value = "Test combat summary"
                    
                    result = self.controller._execute_combat_round(self.player, self.enemy, 1)
        
        assert result["round"] == 1
        assert result["player_action"]["damage_dealt"] == 15
        assert result["enemy_action"]["damage_dealt"] == 8
        assert result["summary"] == "Test combat summary"
    
    def test_execute_combat_round_enemy_defeated(self):
        """Test combat round where enemy is defeated."""
        # Set enemy health low
        self.enemy.health = 1
        
        with patch.object(self.controller, '_calculate_player_damage') as mock_player_dmg:
            with patch('app.controllers.combat.format_combat_summary') as mock_summary:
                mock_player_dmg.return_value = 15  # Enough to kill enemy
                mock_summary.return_value = "Enemy defeated!"
                
                result = self.controller._execute_combat_round(self.player, self.enemy, 1)
        
        assert result["enemy_action"]["action"] == "defeated"
        assert result["enemy_action"]["damage_dealt"] == 0
        assert self.enemy.health == 0


class TestCombatControllerIntegration:
    """Integration tests for CombatController with real objects."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.controller = CombatController()
        self.player = Player(name="Integration Hero")
        self.enemy = Enemy(name="Integration Goblin", floor=1)
        self.room = Room("int_room", "Integration Room", "A test room for integration", 1)
    
    def test_full_combat_flow_player_victory(self):
        """Test complete combat flow resulting in player victory."""
        original_gold = self.player.gold
        
        # Boost player stats to ensure victory
        self.player.attack_power = 50
        self.enemy.health = 20
        
        player, enemy, result = self.controller.initiate_combat(self.player, self.enemy, self.room)
        
        assert result["error"] is False
        assert result["data"]["winner"] == "player"
        assert player.gold > original_gold  # Should have gained gold
        assert not enemy.is_alive()
    
    def test_full_combat_flow_player_defeat(self):
        """Test complete combat flow resulting in player defeat."""
        original_gold = self.player.gold
        
        # Boost enemy stats and reduce player stats to ensure player defeat
        self.enemy.attack_power = 50
        self.enemy.health = 200  # Make enemy harder to kill
        self.player.health = 20
        self.player.attack_power = 1  # Significantly reduce player attack power
        
        player, enemy, result = self.controller.initiate_combat(self.player, self.enemy, self.room)
        
        assert result["error"] is False
        assert result["data"]["winner"] == "enemy"
        assert player.gold < original_gold or player.gold == 0  # Should have lost gold
        assert player.health == 1  # Should be restored to 1
    
    def test_turn_based_battle_complete_flow(self):
        """Test complete turn-based battle flow."""
        # Start battle
        start_result = self.controller.start_battle(self.player, self.enemy, self.room)
        assert start_result["error"] is False
        assert self.player.in_battle is True
        
        # Execute attacks until battle ends
        max_rounds = 20  # Safety limit
        rounds = 0
        
        while self.player.in_battle and rounds < max_rounds:
            attack_result = self.controller.execute_attack(self.player)
            assert attack_result["error"] is False
            
            if attack_result["data"]["battle_ended"]:
                break
            
            rounds += 1
        
        # Battle should have ended
        assert not self.player.in_battle
        assert rounds < max_rounds  # Shouldn't hit safety limit