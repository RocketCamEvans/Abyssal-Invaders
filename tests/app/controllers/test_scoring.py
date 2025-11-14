"""
Unit tests for ScoringController in app/controllers/scoring.py
Tests scoring mechanics, gold rewards, and high score management.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Import the controller and dependencies
from app.controllers.scoring import ScoringController
from app.models import Player, Enemy
from app.utils import HighScoreDB, create_error_response, create_success_response


class TestScoringController:
    """Test cases for ScoringController class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock HighScoreDB to avoid file I/O during tests
        self.mock_highscore_db = Mock(spec=HighScoreDB)
        self.controller = ScoringController(highscore_db=self.mock_highscore_db)
        
        # Create test player
        self.player = Player(name="TestPlayer")
        self.player.gold = 100
        self.player.floor = 2
        self.player.health = 80
        self.player.max_health = 100
        self.player.visited_rooms = {"room1", "room2", "room3"}
        
        # Create test enemy
        self.enemy = Enemy(name="Test Goblin", floor=2)
        self.enemy.max_health = 25
        self.enemy.attack_power = 8
        self.enemy.gold_reward = 20
    
    def test_init_with_default_highscore_db(self):
        """Test controller initialization with default HighScoreDB."""
        with patch('app.controllers.scoring.HighScoreDB') as mock_db_class:
            controller = ScoringController()
            mock_db_class.assert_called_once()
            assert controller.highscore_db is not None
    
    def test_init_with_custom_highscore_db(self):
        """Test controller initialization with custom HighScoreDB."""
        custom_db = Mock(spec=HighScoreDB)
        controller = ScoringController(highscore_db=custom_db)
        assert controller.highscore_db is custom_db
    
    def test_calculate_enemy_gold_reward_basic(self):
        """Test basic enemy gold reward calculation."""
        player_floor = 2
        result = self.controller.calculate_enemy_gold_reward(self.enemy, player_floor)
        
        # Expected calculation:
        # base_reward = 20 (enemy.get_gold_reward())
        # floor_bonus = 20 * (2-1) * 0.1 = 2
        # difficulty_bonus = (25 + 8) * 0.5 = 16.5
        # total = 20 + 2 + 16.5 = 38.5 -> int(38.5) = 38
        # max(5, 38) = 38
        expected = 38
        assert result == expected
    
    def test_calculate_enemy_gold_reward_minimum(self):
        """Test enemy gold reward has minimum of 5 gold."""
        # Create weak enemy with very low rewards
        weak_enemy = Enemy(name="Weak Enemy", floor=1)
        weak_enemy.gold_reward = 1
        weak_enemy.max_health = 1
        weak_enemy.attack_power = 1
        
        result = self.controller.calculate_enemy_gold_reward(weak_enemy, 1)
        assert result >= 5
    
    def test_calculate_enemy_gold_reward_floor_scaling(self):
        """Test enemy gold reward scales with player floor."""
        base_result = self.controller.calculate_enemy_gold_reward(self.enemy, 1)
        higher_floor_result = self.controller.calculate_enemy_gold_reward(self.enemy, 5)
        
        # Higher floor should give more gold due to floor bonus
        assert higher_floor_result > base_result
    
    def test_award_exploration_gold_new_room(self):
        """Test awarding gold for exploring new rooms."""
        result = self.controller.award_exploration_gold(self.player, new_room=True)
        
        # Expected: 2 + player.floor = 2 + 2 = 4
        expected = 4
        assert result == expected
    
    def test_award_exploration_gold_visited_room(self):
        """Test no gold awarded for previously visited rooms."""
        result = self.controller.award_exploration_gold(self.player, new_room=False)
        assert result == 0
    
    def test_award_exploration_gold_floor_scaling(self):
        """Test exploration gold scales with floor level."""
        self.player.floor = 5
        result = self.controller.award_exploration_gold(self.player, new_room=True)
        
        # Expected: 2 + 5 = 7
        expected = 7
        assert result == expected
    
    def test_award_floor_completion_bonus(self):
        """Test floor completion bonus calculation."""
        result = self.controller.award_floor_completion_bonus(self.player)
        
        # Expected: player.floor * 25 = 2 * 25 = 50
        expected = 50
        assert result == expected
    
    def test_award_floor_completion_bonus_scaling(self):
        """Test floor completion bonus scales with floor level."""
        self.player.floor = 5
        result = self.controller.award_floor_completion_bonus(self.player)
        
        # Expected: 5 * 25 = 125
        expected = 125
        assert result == expected
    
    def test_calculate_survival_bonus(self):
        """Test survival bonus calculation."""
        rooms_visited = 3
        result = self.controller.calculate_survival_bonus(self.player, rooms_visited)
        
        # Expected calculation:
        # health_ratio = 80 / 100 = 0.8
        # room_bonus = 3 * 3 = 9
        # health_bonus = int(20 * 0.8) = 16
        # total = 9 + 16 = 25
        expected = 25
        assert result == expected
    
    def test_calculate_survival_bonus_full_health(self):
        """Test survival bonus with full health."""
        self.player.health = 100
        rooms_visited = 5
        result = self.controller.calculate_survival_bonus(self.player, rooms_visited)
        
        # Expected calculation:
        # health_ratio = 100 / 100 = 1.0
        # room_bonus = 5 * 3 = 15
        # health_bonus = int(20 * 1.0) = 20
        # total = 15 + 20 = 35
        expected = 35
        assert result == expected
    
    def test_calculate_survival_bonus_low_health(self):
        """Test survival bonus with low health."""
        self.player.health = 10
        rooms_visited = 2
        result = self.controller.calculate_survival_bonus(self.player, rooms_visited)
        
        # Expected calculation:
        # health_ratio = 10 / 100 = 0.1
        # room_bonus = 2 * 3 = 6
        # health_bonus = int(20 * 0.1) = 2
        # total = 6 + 2 = 8
        expected = 8
        assert result == expected
    
    def test_submit_high_score_success_makes_leaderboard(self):
        """Test successful high score submission that makes leaderboard."""
        # Mock successful database operations
        self.mock_highscore_db.add_score.return_value = True
        
        # Mock get_high_scores to return data with player in top 10
        mock_high_scores = create_success_response([
            {"rank": 5, "name": "TestPlayer", "gold": 100, "floor": 2}
        ])
        
        with patch.object(self.controller, 'get_high_scores', return_value=mock_high_scores):
            with patch.object(self.controller, '_find_player_rank', return_value=5):
                success, result = self.controller.submit_high_score(self.player)
        
        assert success is True
        assert result["error"] is False
        assert result["data"]["player_score"] == 100
        assert result["data"]["player_floor"] == 2
        assert result["data"]["player_rank"] == 5
        assert result["data"]["made_leaderboard"] is True
        assert "Rank #5" in result["message"]
        
        # Verify database call
        self.mock_highscore_db.add_score.assert_called_once_with(
            player_name="TestPlayer", score=100, floor=2
        )
    
    def test_submit_high_score_success_no_leaderboard(self):
        """Test successful high score submission that doesn't make leaderboard."""
        # Mock successful database operations
        self.mock_highscore_db.add_score.return_value = True
        
        # Mock get_high_scores to return data without player in top 10
        mock_high_scores = create_success_response([])
        
        with patch.object(self.controller, 'get_high_scores', return_value=mock_high_scores):
            with patch.object(self.controller, '_find_player_rank', return_value=15):
                success, result = self.controller.submit_high_score(self.player)
        
        assert success is True
        assert result["error"] is False
        assert result["data"]["made_leaderboard"] is False
        assert "Rank #" not in result["message"]
    
    def test_submit_high_score_database_failure(self):
        """Test high score submission with database failure."""
        # Mock database failure
        self.mock_highscore_db.add_score.return_value = False
        
        success, result = self.controller.submit_high_score(self.player)
        
        assert success is False
        assert result["error"] is True
        assert "Failed to submit score to database" in result["message"]
    
    def test_submit_high_score_exception(self):
        """Test high score submission with exception."""
        # Mock database exception
        self.mock_highscore_db.add_score.side_effect = Exception("Database error")
        
        success, result = self.controller.submit_high_score(self.player)
        
        assert success is False
        assert result["error"] is True
        assert "Error submitting score: Database error" in result["message"]
    
    def test_get_high_scores_success(self):
        """Test successful high scores retrieval."""
        # Mock database response
        mock_scores = [
            {"name": "Player1", "gold": 150, "floor": 3},
            {"name": "Player2", "gold": 120, "floor": 2},
            {"name": "Player3", "gold": 100, "floor": 2}
        ]
        self.mock_highscore_db.get_high_scores.return_value = mock_scores
        
        result = self.controller.get_high_scores()
        
        assert result["error"] is False
        assert len(result["data"]) == 3
        
        # Check first score formatting
        first_score = result["data"][0]
        assert first_score["rank"] == 1
        assert first_score["name"] == "Player1"
        assert first_score["gold"] == 150
        assert first_score["floor"] == 3
        assert first_score["score_display"] == "150 gold (Floor 3)"
        
        self.mock_highscore_db.get_high_scores.assert_called_once_with(10)
    
    def test_get_high_scores_custom_limit(self):
        """Test high scores retrieval with custom limit."""
        self.mock_highscore_db.get_high_scores.return_value = []
        
        result = self.controller.get_high_scores(limit=5)
        
        self.mock_highscore_db.get_high_scores.assert_called_once_with(5)
    
    def test_get_high_scores_exception(self):
        """Test high scores retrieval with exception."""
        self.mock_highscore_db.get_high_scores.side_effect = Exception("Database error")
        
        result = self.controller.get_high_scores()
        
        assert result["error"] is True
        assert "Error retrieving high scores: Database error" in result["message"]
    
    def test_get_player_statistics(self):
        """Test comprehensive player statistics retrieval."""
        # Add some allies to player
        ally1 = Mock()
        ally1.name = "TestAlly"
        self.player.allies = [ally1]
        
        result = self.controller.get_player_statistics(self.player)
        
        assert result["error"] is False
        data = result["data"]
        
        # Check basic stats
        basic_stats = data["basic_stats"]
        assert basic_stats["name"] == "TestPlayer"
        assert basic_stats["current_gold"] == 100
        assert basic_stats["current_floor"] == 2
        assert basic_stats["health"] == "80/100"
        assert basic_stats["attack_power"] == 10
        assert basic_stats["defense"] == 5
        
        # Check progress stats
        progress_stats = data["progress_stats"]
        assert progress_stats["rooms_visited"] == 3
        assert progress_stats["allies_found"] == 1
        assert progress_stats["current_room"] == "start"
        
        # Check calculated stats
        calculated_stats = data["calculated_stats"]
        assert calculated_stats["health_percentage"] == 80.0
        assert calculated_stats["exploration_score"] == 6  # 3 rooms * 2 floor
        assert calculated_stats["survival_score"] == 200  # 100 gold + (2 * 50)
        assert calculated_stats["is_alive"] is True
    
    def test_calculate_death_penalty_normal_case(self):
        """Test death penalty calculation for normal case."""
        self.player.gold = 200
        self.player.floor = 3
        
        result = self.controller.calculate_death_penalty(self.player)
        
        # Expected calculation:
        # gold_penalty = min(100, max(0, 200 // 4)) = min(100, 50) = 50
        # new_gold = max(0, 200 - 50) = 150
        # floor_penalty = 1 (since floor > 1)
        # new_floor = max(1, 3 - 1) = 2
        
        assert result["gold_lost"] == 50
        assert result["gold_remaining"] == 150
        assert result["floors_lost"] == 1
        assert result["new_floor"] == 2
        assert result["respawn_location"] == "start"
        assert result["health_restored"] == 50  # max_health // 2
        assert "Lost 50 gold and 1 floor" in result["message"]
    
    def test_calculate_death_penalty_floor_one(self):
        """Test death penalty calculation on floor 1."""
        self.player.floor = 1
        
        result = self.controller.calculate_death_penalty(self.player)
        
        assert result["floors_lost"] == 0
        assert result["new_floor"] == 1
    
    def test_calculate_death_penalty_max_gold_loss(self):
        """Test death penalty with maximum gold loss cap."""
        self.player.gold = 1000  # Very high gold
        
        result = self.controller.calculate_death_penalty(self.player)
        
        # Gold penalty should be capped at 100
        assert result["gold_lost"] == 100
        assert result["gold_remaining"] == 900
    
    def test_calculate_death_penalty_low_gold(self):
        """Test death penalty with low gold amount."""
        self.player.gold = 10
        
        result = self.controller.calculate_death_penalty(self.player)
        
        # Gold penalty = min(100, max(0, 10 // 4)) = min(100, 2) = 2
        assert result["gold_lost"] == 2
        assert result["gold_remaining"] == 8
    
    def test_apply_death_penalty(self):
        """Test applying death penalty to player."""
        self.player.gold = 200
        self.player.floor = 3
        self.player.room_id = "battle_room"
        self.player.visited_rooms = {"room1", "room2", "room3"}
        
        result = self.controller.apply_death_penalty(self.player)
        
        # Check penalty was applied
        assert result.gold == 150  # 200 - 50
        assert result.floor == 2   # 3 - 1
        assert result.room_id == "start"
        assert result.health == 50  # max_health // 2
        assert len(result.visited_rooms) == 0  # Should be cleared
        
        # Allies should be kept
        assert result.allies == self.player.allies
    
    def test_find_player_rank_found(self):
        """Test finding player rank in high scores."""
        high_scores = [
            {"rank": 1, "name": "Player1", "gold": 200},
            {"rank": 2, "name": "TestPlayer", "gold": 100},
            {"rank": 3, "name": "Player3", "gold": 80}
        ]
        
        rank = self.controller._find_player_rank("TestPlayer", 100, high_scores)
        assert rank == 2
    
    def test_find_player_rank_not_found(self):
        """Test finding player rank when not in high scores."""
        high_scores = [
            {"rank": 1, "name": "Player1", "gold": 200},
            {"rank": 2, "name": "Player2", "gold": 150}
        ]
        
        rank = self.controller._find_player_rank("TestPlayer", 100, high_scores)
        assert rank is None
    
    def test_find_player_rank_multiple_matches(self):
        """Test finding player rank with multiple score matches."""
        high_scores = [
            {"rank": 1, "name": "TestPlayer", "gold": 100},
            {"rank": 2, "name": "TestPlayer", "gold": 90}
        ]
        
        # Should return first match
        rank = self.controller._find_player_rank("TestPlayer", 100, high_scores)
        assert rank == 1
    
    def test_get_score_summary(self):
        """Test comprehensive score summary generation."""
        # Setup player with some progress
        self.player.allies = [Mock(), Mock()]  # 2 allies
        
        result = self.controller.get_score_summary(self.player)
        
        assert result["error"] is False
        data = result["data"]
        
        # Check current session data
        current_session = data["current_session"]
        assert current_session["gold_earned"] == 100
        assert current_session["floors_reached"] == 2
        assert current_session["rooms_explored"] == 3
        assert current_session["allies_recruited"] == 2
        
        # Check potential bonuses (these call other methods)
        potential_bonuses = data["potential_bonuses"]
        assert "exploration_bonus" in potential_bonuses
        assert "survival_bonus" in potential_bonuses
        assert "floor_bonus" in potential_bonuses
        
        # Check performance metrics
        performance_metrics = data["performance_metrics"]
        assert performance_metrics["gold_per_floor"] == 50.0  # 100 / 2
        assert performance_metrics["survival_rate"] == "80.0%"
        assert performance_metrics["exploration_efficiency"] == 1.5  # 3 / 2


class TestScoringControllerEdgeCases:
    """Test edge cases and error conditions for ScoringController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_highscore_db = Mock(spec=HighScoreDB)
        self.controller = ScoringController(highscore_db=self.mock_highscore_db)
    
    def test_calculate_enemy_gold_reward_zero_stats(self):
        """Test gold reward calculation with zero enemy stats."""
        enemy = Mock()
        enemy.get_gold_reward.return_value = 0
        enemy.max_health = 0
        enemy.attack_power = 0
        
        result = self.controller.calculate_enemy_gold_reward(enemy, 1)
        
        # Should still return minimum of 5
        assert result == 5
    
    def test_award_exploration_gold_zero_floor(self):
        """Test exploration gold with floor 0 (edge case)."""
        player = Mock()
        player.floor = 0
        
        result = self.controller.award_exploration_gold(player, new_room=True)
        
        # Expected: 2 + 0 = 2
        assert result == 2
    
    def test_calculate_survival_bonus_zero_health(self):
        """Test survival bonus with zero health."""
        player = Mock()
        player.health = 0
        player.max_health = 100
        
        result = self.controller.calculate_survival_bonus(player, 5)
        
        # Expected calculation:
        # health_ratio = 0 / 100 = 0.0
        # room_bonus = 5 * 3 = 15
        # health_bonus = int(20 * 0.0) = 0
        # total = 15 + 0 = 15
        assert result == 15
    
    def test_calculate_survival_bonus_zero_max_health(self):
        """Test survival bonus with zero max health (edge case)."""
        player = Mock()
        player.health = 50
        player.max_health = 0  # Edge case that shouldn't happen normally
        
        # This would cause division by zero, but let's see how it handles it
        with pytest.raises(ZeroDivisionError):
            self.controller.calculate_survival_bonus(player, 3)
    
    def test_get_player_statistics_with_dead_player(self):
        """Test player statistics for a dead player."""
        player = Player(name="DeadPlayer")
        player.health = 0
        player.max_health = 100
        
        result = self.controller.get_player_statistics(player)
        
        assert result["error"] is False
        calculated_stats = result["data"]["calculated_stats"]
        assert calculated_stats["is_alive"] is False
        assert calculated_stats["health_percentage"] == 0.0
    
    def test_get_score_summary_division_by_zero_protection(self):
        """Test score summary handles division by zero cases."""
        player = Player(name="TestPlayer")
        player.gold = 100
        player.floor = 0  # Edge case
        player.visited_rooms = set()
        
        result = self.controller.get_score_summary(player)
        
        assert result["error"] is False
        performance_metrics = result["data"]["performance_metrics"]
        
        # Should use max(1, floor) to prevent division by zero
        assert performance_metrics["gold_per_floor"] == 100.0  # 100 / max(1, 0)
        assert performance_metrics["exploration_efficiency"] == 0.0  # 0 / max(1, 0)


class TestScoringControllerIntegration:
    """Integration tests using real objects without mocking dependencies."""
    
    def setup_method(self):
        """Set up real objects for integration testing."""
        # Use real HighScoreDB but mock its file operations
        with patch('app.utils.file_db.HighScoreDB.load_data'), \
             patch('app.utils.file_db.HighScoreDB.save_data'), \
             patch('app.utils.file_db.HighScoreDB.__init__', return_value=None):
            self.real_highscore_db = HighScoreDB()
            self.controller = ScoringController(highscore_db=self.real_highscore_db)
        
        # Create real player and enemy objects
        self.player = Player(name="IntegrationTestPlayer")
        self.player.gold = 150
        self.player.floor = 3
        self.player.health = 75
        self.player.max_health = 100
        self.player.visited_rooms = {"room1", "room2", "room3", "room4"}
        
        self.enemy = Enemy(name="Integration Test Monster", floor=3)
    
    def test_full_scoring_workflow(self):
        """Test complete scoring workflow with real objects."""
        # Test gold reward calculation
        gold_reward = self.controller.calculate_enemy_gold_reward(self.enemy, self.player.floor)
        assert gold_reward > 0
        
        # Test exploration gold
        exploration_gold = self.controller.award_exploration_gold(self.player, new_room=True)
        assert exploration_gold == 5  # 2 + 3 (floor)
        
        # Test floor completion bonus
        floor_bonus = self.controller.award_floor_completion_bonus(self.player)
        assert floor_bonus == 75  # 3 * 25
        
        # Test survival bonus
        survival_bonus = self.controller.calculate_survival_bonus(self.player, len(self.player.visited_rooms))
        expected_survival = (4 * 3) + int(20 * 0.75)  # room_bonus + health_bonus
        assert survival_bonus == expected_survival
        
        # Test player statistics
        stats = self.controller.get_player_statistics(self.player)
        assert stats["error"] is False
        assert stats["data"]["basic_stats"]["current_gold"] == 150
        
        # Test score summary
        summary = self.controller.get_score_summary(self.player)
        assert summary["error"] is False
        assert summary["data"]["current_session"]["floors_reached"] == 3
    
    def test_death_penalty_workflow(self):
        """Test complete death penalty workflow with real player."""
        original_gold = self.player.gold
        original_floor = self.player.floor
        
        # Calculate penalty
        penalty_info = self.controller.calculate_death_penalty(self.player)
        
        # Apply penalty
        updated_player = self.controller.apply_death_penalty(self.player)
        
        # Verify penalty was applied correctly
        assert updated_player.gold < original_gold
        assert updated_player.floor <= original_floor
        assert updated_player.room_id == "start"
        assert len(updated_player.visited_rooms) == 0
        assert updated_player.health == self.player.max_health // 2
    
    def test_realistic_game_session_scoring(self):
        """Test scoring for a realistic game session."""
        # Simulate a player who has played for a while
        player = Player(name="GameSession")
        player.gold = 300
        player.floor = 5
        player.health = 60
        player.max_health = 120  # Leveled up
        player.visited_rooms = {"start", "room1", "room2", "room3", "room4", "room5", "room6"}
        
        # Test various scoring methods
        enemy = Enemy(name="Boss Monster", floor=5)
        
        gold_reward = self.controller.calculate_enemy_gold_reward(enemy, player.floor)
        exploration_gold = self.controller.award_exploration_gold(player, new_room=True)
        floor_bonus = self.controller.award_floor_completion_bonus(player)
        survival_bonus = self.controller.calculate_survival_bonus(player, len(player.visited_rooms))
        
        # All values should be reasonable for a floor 5 player
        assert gold_reward >= 20  # Should get decent reward
        assert exploration_gold == 7  # 2 + 5
        assert floor_bonus == 125  # 5 * 25
        assert survival_bonus > 20  # Should get decent survival bonus
        
        # Test statistics show progression
        stats = self.controller.get_player_statistics(player)
        basic_stats = stats["data"]["basic_stats"]
        assert basic_stats["current_floor"] == 5
        assert basic_stats["current_gold"] == 300
        
        # Performance metrics should reflect advanced play
        summary = self.controller.get_score_summary(player)
        metrics = summary["data"]["performance_metrics"]
        assert metrics["gold_per_floor"] == 60.0  # 300 / 5
        assert metrics["exploration_efficiency"] == 1.4  # 7 / 5