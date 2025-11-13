"""
Combat controller for handling battles between players and enemies.
"""

from typing import Tuple, Dict, Any, Optional
from ..models import Player, Enemy, Room
from ..utils import create_error_response, create_success_response
from ..utils.helpers import calculate_damage_with_variance, format_combat_summary, roll_dice
import random


class CombatController:
    """
    Handles combat mechanics between players and enemies.
    """
    
    def __init__(self):
        """
        Initialize the combat controller.
        """
        pass
    
    def initiate_combat(self, player: Player, enemy: Enemy, room: Room) -> Tuple[Player, Enemy, Dict[str, Any]]:
        """
        Start combat between player and enemy.
        
        Args:
            player (Player): Player object
            enemy (Enemy): Enemy object
            room (Room): Room where combat takes place
            
        Returns:
            Tuple[Player, Enemy, Dict[str, Any]]: Updated player, enemy, and combat result
        """
        if not player.is_alive():
            return player, enemy, create_error_response("Player is already defeated!")
        
        # Generate combat description using room context
        combat_description = self._generate_combat_description(player, enemy, room)
        
        combat_log = []
        round_number = 1
        
        # Combat loop
        while player.is_alive() and enemy.is_alive():
            round_result = self._execute_combat_round(player, enemy, round_number)
            combat_log.append(round_result)
            round_number += 1
            
            # Prevent infinite combat (safety measure)
            if round_number > 50:
                break
        
        # Determine winner and handle rewards
        if enemy.is_alive():
            # Player defeated
            result = self._handle_player_defeat(player, enemy)
        else:
            # Enemy defeated
            result = self._handle_enemy_defeat(player, enemy)
        
        # Compile final combat result
        combat_result = {
            "description": combat_description,
            "combat_log": combat_log,
            "winner": "player" if player.is_alive() else "enemy",
            "result": result,
            "final_player_health": player.health,
            "final_enemy_health": enemy.health
        }
        
        return player, enemy, create_success_response(combat_result, "Combat completed")
    
    def _execute_combat_round(self, player: Player, enemy: Enemy, round_number: int) -> Dict[str, Any]:
        """
        Execute a single round of combat.
        
        Args:
            player (Player): Player object
            enemy (Enemy): Enemy object
            round_number (int): Current round number
            
        Returns:
            Dict[str, Any]: Round result information
        """
        round_log = {
            "round": round_number,
            "player_action": None,
            "enemy_action": None,
            "player_health_before": player.health,
            "enemy_health_before": enemy.health,
            "player_health_after": None,
            "enemy_health_after": None
        }
        
        # Player attacks first
        player_damage = self._calculate_player_damage(player)
        enemy_survived = enemy.take_damage(player_damage)
        
        round_log["player_action"] = {
            "action": "attack",
            "damage_dealt": player_damage,
            "target_health_remaining": enemy.health
        }
        
        # Enemy attacks back if still alive
        if enemy_survived:
            enemy_damage = self._calculate_enemy_damage(enemy)
            player_survived = player.take_damage(enemy_damage)
            
            round_log["enemy_action"] = {
                "action": "attack",
                "damage_dealt": enemy_damage,
                "target_health_remaining": player.health
            }
        else:
            round_log["enemy_action"] = {
                "action": "defeated",
                "damage_dealt": 0,
                "target_health_remaining": player.health
            }
        
        round_log["player_health_after"] = player.health
        round_log["enemy_health_after"] = enemy.health
        
        # Generate round summary
        round_log["summary"] = format_combat_summary(
            player_damage=player_damage,
            enemy_damage=round_log["enemy_action"]["damage_dealt"],
            player_health=player.health,
            enemy_health=enemy.health,
            player_name=player.name,
            enemy_name=enemy.name
        )
        
        return round_log
    
    def _calculate_player_damage(self, player: Player) -> int:
        """
        Calculate damage dealt by the player.
        
        Args:
            player (Player): Player object
            
        Returns:
            int: Damage amount
        """
        base_damage = player.attack_power
        
        # Add some randomness to attacks
        damage = calculate_damage_with_variance(base_damage, 0.25)
        
        # Critical hit chance (10%)
        if roll_dice(100) <= 10:
            damage = int(damage * 1.5)
        
        return max(1, damage)
    
    def _calculate_enemy_damage(self, enemy: Enemy) -> int:
        """
        Calculate damage dealt by the enemy.
        
        Args:
            enemy (Enemy): Enemy object
            
        Returns:
            int: Damage amount
        """
        return enemy.attack()
    
    def use_ally_in_combat(self, player: Player, ally_index: int, enemy: Enemy) -> Tuple[bool, Dict[str, Any]]:
        """
        Use an ally's attack in combat.
        
        Args:
            player (Player): Player object
            ally_index (int): Index of ally to use
            enemy (Enemy): Enemy being fought
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (Success, Result information)
        """
        if ally_index < 0 or ally_index >= len(player.allies):
            return False, create_error_response("Invalid ally selection.")
        
        ally = player.allies[ally_index]
        if not ally.is_available():
            return False, create_error_response("This ally has already been used.")
        
        # Use ally attack
        ally_damage = ally.use_attack()
        enemy_survived = enemy.take_damage(ally_damage)
        
        # Remove ally from player's list (one-time use)
        player.allies.pop(ally_index)
        
        result_data = {
            "ally_name": ally.name,
            "ally_description": ally.description,
            "damage_dealt": ally_damage,
            "enemy_health_remaining": enemy.health,
            "enemy_defeated": not enemy_survived
        }
        
        message = f"{ally.name} attacks for {ally_damage} damage!"
        if not enemy_survived:
            message += f" {enemy.name} is defeated!"
        
        return True, create_success_response(result_data, message)
    
    def _handle_player_defeat(self, player: Player, enemy: Enemy) -> Dict[str, Any]:
        """
        Handle player defeat in combat.
        
        Args:
            player (Player): Defeated player
            enemy (Enemy): Victorious enemy
            
        Returns:
            Dict[str, Any]: Defeat result information
        """
        # Player loses some gold (but not all)
        gold_lost = min(player.gold // 4, 50)  # Lose 25% of gold, max 50
        player.gold = max(0, player.gold - gold_lost)
        
        # Reset player health to 1 (don't permanently kill them)
        player.health = 1
        
        return {
            "outcome": "defeat",
            "gold_lost": gold_lost,
            "remaining_gold": player.gold,
            "health_restored": 1,
            "message": f"You have been defeated by {enemy.name}! You lost {gold_lost} gold but managed to escape with your life."
        }
    
    def _handle_enemy_defeat(self, player: Player, enemy: Enemy) -> Dict[str, Any]:
        """
        Handle enemy defeat in combat.
        
        Args:
            player (Player): Victorious player
            enemy (Enemy): Defeated enemy
            
        Returns:
            Dict[str, Any]: Victory result information
        """
        # Award gold
        gold_reward = enemy.get_gold_reward()
        player.add_gold(gold_reward)
        
        # Small chance of finding a healing item (20%)
        healing_found = 0
        if random.random() < 0.2:
            healing_found = random.randint(10, 25)
            player.heal(healing_found)
        
        return {
            "outcome": "victory",
            "gold_earned": gold_reward,
            "total_gold": player.gold,
            "healing_found": healing_found,
            "current_health": player.health,
            "max_health": player.max_health,
            "message": f"Victory! You defeated {enemy.name} and earned {gold_reward} gold." +
                      (f" You also found healing herbs and restored {healing_found} health!" if healing_found > 0 else "")
        }
    
    def _generate_combat_description(self, player: Player, enemy: Enemy, room: Room) -> str:
        """
        Generate a descriptive text for the combat encounter.
        
        Args:
            player (Player): Player object
            enemy (Enemy): Enemy object
            room (Room): Room where combat occurs
            
        Returns:
            str: Combat description
        """
        # In a real implementation, this would call the LLM generation service
        # For now, we'll use template-based descriptions
        
        room_context = room.description if room.description else "in this mysterious chamber"
        
        descriptions = [
            f"As you explore {room_context}, {enemy.name} suddenly emerges from the shadows! {enemy.description}",
            f"The atmosphere in {room.name} grows tense as {enemy.name} blocks your path. {enemy.description}",
            f"You hear a menacing growl echoing through {room.name}. {enemy.name} appears before you! {enemy.description}",
            f"The air grows cold as {enemy.name} materializes {room_context}. {enemy.description}",
            f"Your footsteps alert {enemy.name} to your presence in {room.name}. {enemy.description}"
        ]
        
        return random.choice(descriptions)
    
    def check_encounter_chance(self, room: Room) -> bool:
        """
        Check if an encounter occurs in the given room.
        
        Args:
            room (Room): Room to check for encounters
            
        Returns:
            bool: True if encounter occurs
        """
        return room.roll_for_encounter()
    
    def flee_from_combat(self, player: Player, enemy: Enemy) -> Tuple[bool, Dict[str, Any]]:
        """
        Attempt to flee from combat.
        
        Args:
            player (Player): Player attempting to flee
            enemy (Enemy): Enemy being fled from
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (Success, Result information)
        """
        # Base flee chance is 70%, modified by player health
        health_ratio = player.health / player.max_health
        flee_chance = 0.5 + (health_ratio * 0.3)  # 50-80% based on health
        
        if random.random() < flee_chance:
            # Successful flee
            return True, create_success_response({
                "outcome": "fled",
                "message": "You successfully fled from combat!"
            })
        else:
            # Failed flee - enemy gets a free attack
            damage = self._calculate_enemy_damage(enemy)
            player.take_damage(damage)
            
            return False, create_error_response(
                f"Failed to flee! {enemy.name} attacks you for {damage} damage as you try to escape. "
                f"You have {player.health} health remaining."
            )