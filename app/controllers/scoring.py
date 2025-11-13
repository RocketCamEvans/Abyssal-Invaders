"""
Scoring controller for handling gold rewards and high score management.
"""

from typing import List, Dict, Any, Tuple, Optional
from ..models import Player, Enemy
from ..utils import HighScoreDB, create_error_response, create_success_response
from datetime import datetime
import json


class ScoringController:
    """
    Handles scoring mechanics, gold rewards, and high score tracking.
    """
    
    def __init__(self, highscore_db: Optional[HighScoreDB] = None):
        """
        Initialize the scoring controller.
        
        Args:
            highscore_db (Optional[HighScoreDB]): High score database instance
        """
        self.highscore_db = highscore_db or HighScoreDB()
    
    def calculate_enemy_gold_reward(self, enemy: Enemy, player_floor: int) -> int:
        """
        Calculate gold reward for defeating an enemy.
        
        Args:
            enemy (Enemy): Defeated enemy
            player_floor (int): Current player floor (for bonus calculation)
            
        Returns:
            int: Gold reward amount
        """
        base_reward = enemy.get_gold_reward()
        
        # Floor bonus: 10% extra per floor
        floor_bonus = base_reward * (player_floor - 1) * 0.1
        
        # Enemy difficulty bonus based on stats
        difficulty_bonus = (enemy.max_health + enemy.attack_power) * 0.5
        
        total_reward = int(base_reward + floor_bonus + difficulty_bonus)
        
        return max(5, total_reward)  # Minimum 5 gold
    
    def award_exploration_gold(self, player: Player, new_room: bool = True) -> int:
        """
        Award gold for exploration (entering new rooms).
        
        Args:
            player (Player): Player object
            new_room (bool): Whether this is a new room
            
        Returns:
            int: Gold awarded for exploration
        """
        if not new_room:
            return 0
        
        base_exploration = 2 + player.floor  # More gold on higher floors
        return base_exploration
    
    def award_floor_completion_bonus(self, player: Player) -> int:
        """
        Award bonus gold for completing a floor (finding staircase).
        
        Args:
            player (Player): Player object
            
        Returns:
            int: Bonus gold for floor completion
        """
        floor_bonus = player.floor * 25  # 25 gold per floor completed
        return floor_bonus
    
    def calculate_survival_bonus(self, player: Player, rooms_visited: int) -> int:
        """
        Calculate survival bonus based on rooms visited and health remaining.
        
        Args:
            player (Player): Player object
            rooms_visited (int): Number of rooms visited on current floor
            
        Returns:
            int: Survival bonus
        """
        health_ratio = player.health / player.max_health
        room_bonus = rooms_visited * 3
        health_bonus = int(20 * health_ratio)
        
        return room_bonus + health_bonus
    
    def submit_high_score(self, player: Player) -> Tuple[bool, Dict[str, Any]]:
        """
        Submit player's score to the high score table.
        
        Args:
            player (Player): Player object with final score
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (Success, Response data)
        """
        try:
            success = self.highscore_db.add_score(
                player_name=player.name,
                score=player.gold,
                floor=player.floor
            )
            
            if success:
                # Get updated high scores to see if player made the leaderboard
                high_scores = self.get_high_scores()
                player_rank = self._find_player_rank(player.name, player.gold, high_scores["data"])
                
                response_data = {
                    "player_score": player.gold,
                    "player_floor": player.floor,
                    "player_rank": player_rank,
                    "made_leaderboard": player_rank is not None and player_rank <= 10
                }
                
                message = f"Score submitted! Final score: {player.gold} gold, reached floor {player.floor}"
                if response_data["made_leaderboard"]:
                    message += f" - Rank #{player_rank} on leaderboard!"
                
                return True, create_success_response(response_data, message)
            else:
                return False, create_error_response("Failed to submit score to database")
                
        except Exception as e:
            return False, create_error_response(f"Error submitting score: {str(e)}")
    
    def get_high_scores(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get the current high score leaderboard.
        
        Args:
            limit (int): Maximum number of scores to return
            
        Returns:
            Dict[str, Any]: High scores data
        """
        try:
            scores = self.highscore_db.get_high_scores(limit)
            
            # Format scores for display
            formatted_scores = []
            for i, score in enumerate(scores, 1):
                formatted_scores.append({
                    "rank": i,
                    "name": score["name"],
                    "gold": score["gold"],
                    "floor": score["floor"],
                    "score_display": f"{score['gold']} gold (Floor {score['floor']})"
                })
            
            return create_success_response(formatted_scores, f"Retrieved top {len(formatted_scores)} scores")
            
        except Exception as e:
            return create_error_response(f"Error retrieving high scores: {str(e)}")
    
    def get_player_statistics(self, player: Player) -> Dict[str, Any]:
        """
        Get comprehensive player statistics.
        
        Args:
            player (Player): Player object
            
        Returns:
            Dict[str, Any]: Player statistics
        """
        stats = {
            "basic_stats": {
                "name": player.name,
                "current_gold": player.gold,
                "current_floor": player.floor,
                "health": f"{player.health}/{player.max_health}",
                "attack_power": player.attack_power,
                "defense": player.defense
            },
            "progress_stats": {
                "rooms_visited": len(player.visited_rooms),
                "allies_found": len(player.allies),
                "current_room": player.room_id
            },
            "calculated_stats": {
                "health_percentage": round((player.health / player.max_health) * 100, 1),
                "exploration_score": len(player.visited_rooms) * player.floor,
                "survival_score": player.gold + (player.floor * 50),
                "is_alive": player.is_alive()
            }
        }
        
        return create_success_response(stats, "Player statistics retrieved")
    
    def calculate_death_penalty(self, player: Player) -> Dict[str, Any]:
        """
        Calculate penalties for player death.
        
        Args:
            player (Player): Player who died
            
        Returns:
            Dict[str, Any]: Death penalty information
        """
        # Calculate gold loss (25% of current gold, minimum 0, maximum 100)
        gold_penalty = min(100, max(0, player.gold // 4))
        new_gold = max(0, player.gold - gold_penalty)
        
        # Calculate floor penalty (go back 1 floor, minimum floor 1)
        floor_penalty = 1 if player.floor > 1 else 0
        new_floor = max(1, player.floor - floor_penalty)
        
        penalty_info = {
            "gold_lost": gold_penalty,
            "gold_remaining": new_gold,
            "floors_lost": floor_penalty,
            "new_floor": new_floor,
            "respawn_location": "start",
            "health_restored": player.max_health // 2,  # Respawn with half health
            "message": f"Death penalty: Lost {gold_penalty} gold and {floor_penalty} floor(s). You respawn on floor {new_floor}."
        }
        
        return penalty_info
    
    def apply_death_penalty(self, player: Player) -> Player:
        """
        Apply death penalty to player and reset their state.
        
        Args:
            player (Player): Player who died
            
        Returns:
            Player: Player with penalties applied
        """
        penalty = self.calculate_death_penalty(player)
        
        # Apply penalties
        player.gold = penalty["gold_remaining"]
        player.floor = penalty["new_floor"]
        player.room_id = penalty["respawn_location"]
        player.health = penalty["health_restored"]
        
        # Clear visited rooms for new floor
        player.visited_rooms.clear()
        
        # Keep allies (they help you recover)
        
        return player
    
    def _find_player_rank(self, player_name: str, player_score: int, high_scores: List[Dict]) -> Optional[int]:
        """
        Find player's rank in the high score list.
        
        Args:
            player_name (str): Player's name
            player_score (int): Player's score
            high_scores (List[Dict]): Current high scores
            
        Returns:
            Optional[int]: Player's rank or None if not found
        """
        for score_entry in high_scores:
            if score_entry["name"] == player_name and score_entry["gold"] == player_score:
                return score_entry["rank"]
        return None
    
    def get_score_summary(self, player: Player) -> Dict[str, Any]:
        """
        Get a comprehensive score summary for the player.
        
        Args:
            player (Player): Player object
            
        Returns:
            Dict[str, Any]: Score summary
        """
        summary = {
            "current_session": {
                "gold_earned": player.gold,
                "floors_reached": player.floor,
                "rooms_explored": len(player.visited_rooms),
                "allies_recruited": len(player.allies)
            },
            "potential_bonuses": {
                "exploration_bonus": self.award_exploration_gold(player, True) * len(player.visited_rooms),
                "survival_bonus": self.calculate_survival_bonus(player, len(player.visited_rooms)),
                "floor_bonus": self.award_floor_completion_bonus(player) if player.floor > 1 else 0
            },
            "performance_metrics": {
                "gold_per_floor": round(player.gold / max(1, player.floor), 2),
                "survival_rate": f"{round((player.health / player.max_health) * 100, 1)}%",
                "exploration_efficiency": round(len(player.visited_rooms) / max(1, player.floor), 2)
            }
        }
        
        return create_success_response(summary, "Score summary generated")