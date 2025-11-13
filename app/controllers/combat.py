"""
Combat controller for handling battles between players and enemies.
"""

from typing import Tuple, Dict, Any, Optional
from ..models import Player, Enemy, Room
from ..utils import create_error_response, create_success_response
from ..utils.helpers import calculate_damage_with_variance, format_combat_summary, roll_dice
import random
import os
import sys

# Add the utils directory to the path to import openai_client
utils_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'utils')
sys.path.insert(0, utils_dir)

try:
    from openai_client import create_openai_client
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class CombatController:
    """
    Handles combat mechanics between players and enemies.
    """
    
    def __init__(self):
        """
        Initialize the combat controller.
        """
        self.openai_client = create_openai_client() if OPENAI_AVAILABLE else None
    
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
    
    def start_battle(self, player: Player, enemy: Enemy, room: Room, ally_data: Optional[dict] = None) -> Dict[str, Any]:
        """
        Start a turn-based battle between player and enemy.
        
        Args:
            player (Player): Player object
            enemy (Enemy): Enemy object
            room (Room): Room where battle takes place
            ally_data (Optional[dict]): Ally data if present
            
        Returns:
            Dict[str, Any]: Battle initiation result
        """
        if not player.is_alive():
            return create_error_response("Player is already defeated!")
        
        # Set up battle state in player
        player.start_battle(enemy.to_dict(), room.to_dict(), ally_data)
        
        # Generate AI battle description
        battle_description = self._generate_ai_battle_description(player, enemy, room)
        
        return create_success_response({
            "battle_started": True,
            "message": "Battle started!",
            "description": battle_description,
            "player_health": player.health,
            "enemy_health": enemy.health,
            "enemy_name": enemy.name,
            "enemy": enemy.to_dict(),
            "ally_available": ally_data is not None,
            "ally_name": ally_data.get('name') if ally_data else None
        }, "Battle initiated")
    
    def execute_attack(self, player: Player, use_ally: bool = False) -> Dict[str, Any]:
        """
        Execute a player attack in turn-based combat.
        
        Args:
            player (Player): Player object
            use_ally (bool): Whether to use ally special attack
            
        Returns:
            Dict[str, Any]: Attack result
        """
        if not player.in_battle or not player.current_enemy:
            return create_error_response("Player is not in battle!")
        
        # Create enemy object from stored data
        enemy = Enemy.from_dict(player.current_enemy)
        
        battle_log = []
        
        # Player attack (with ally if requested)
        if use_ally and player.current_ally and not player.ally_used:
            damage = self._execute_ally_attack(player, enemy, battle_log)
            player.ally_used = True
        else:
            damage = self._execute_player_attack(player, enemy, battle_log)
        
        # Check if enemy is defeated
        if not enemy.is_alive():
            reward = self._handle_enemy_defeat(player, enemy)
            
            # Get room information before ending battle
            room_data = player.battle_room
            room = Room.from_dict(room_data) if room_data else None
            
            player.end_battle()
            
            # Include room directions in victory response
            response_data = {
                "battle_log": battle_log,
                "battle_ended": True,
                "victory": True,
                "reward": reward,
                "player_health": player.health,
                "enemy_health": enemy.health
            }
            
            # Add room direction info after victory
            if room:
                response_data["room_info"] = {
                    "current_room": room.get_room_info(),
                    "available_directions": room.get_available_directions(),
                    "message": "Victory! You can now explore the room or move to adjacent areas."
                }
            
            return create_success_response(response_data, "Enemy defeated!")
        
        # Enemy counterattack
        self._execute_enemy_attack(player, enemy, battle_log)
        
        # Update stored enemy data
        player.current_enemy = enemy.to_dict()
        
        # Check if player is defeated
        if not player.is_alive():
            player.end_battle()
            
            return create_success_response({
                "battle_log": battle_log,
                "battle_ended": True,
                "victory": False,
                "player_health": player.health,
                "enemy_health": enemy.health
            }, "Player defeated!")
        
        return create_success_response({
            "battle_log": battle_log,
            "battle_ended": False,
            "player_health": player.health,
            "enemy_health": enemy.health,
            "ally_available": player.current_ally and not player.ally_used
        }, "Attack executed")
    
    def execute_flee(self, player: Player) -> Dict[str, Any]:
        """
        Execute fleeing from battle.
        
        Args:
            player (Player): Player object
            
        Returns:
            Dict[str, Any]: Flee result
        """
        if not player.in_battle:
            return create_error_response("Player is not in battle!")
        
        # Get room information before fleeing
        room_data = player.battle_room
        room = Room.from_dict(room_data) if room_data else None
        
        gold_lost = player.flee_battle()
        
        response_data = {
            "message": f"You fled from battle and lost {gold_lost} gold!",
            "gold_lost": gold_lost,
            "current_gold": player.gold,
            "battle_ended": True
        }
        
        # Add room direction info after fleeing
        if room:
            response_data["room_info"] = {
                "current_room": room.get_room_info(),
                "available_directions": room.get_available_directions(),
                "message": "You escaped! You can now explore the room or move to safety."
            }
        
        return create_success_response(response_data, "Fled from battle")
    
    def _generate_ai_battle_description(self, player: Player, enemy: Enemy, room: Room) -> str:
        """
        Generate AI-powered battle description with a 15-second timeout and robust fallback.
        """
        prompt = f"""You are a fantasy narrator with charm and wit. Describe the start of a battle in 2 sentences maximum.

Player: {player.name} (Health: {player.health}, Attack: {player.attack_power}, Defense: {player.defense})
Enemy: {enemy.name} - {enemy.description}
Location: {room.name} - {room.description}

Write a brief, atmospheric description of the encounter starting. Make it feel like a classic fantasy adventure with a touch of personality."""
        if self.openai_client:
            import concurrent.futures
            import logging
            logging.info("[Combat] Requesting OpenAI battle description...")
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self.openai_client.generate_completion, prompt, "gpt-3.5-turbo", 80, 0.8)
                    description = future.result(timeout=15)
                if description:
                    logging.info("[Combat] OpenAI battle description received.")
                    return description
                else:
                    logging.warning("[Combat] OpenAI returned no description, using fallback.")
            except Exception as e:
                logging.error(f"[Combat] OpenAI battle description failed or timed out: {e}")
        else:
            import logging
            logging.info("[Combat] OpenAI client not available, using fallback description.")
        # Fallback description
        return f"{player.name} faces {enemy.name} in the {room.name}. The battle is about to begin!"
    
    def _generate_critical_hit_description(self, attacker_name: str, target_name: str, 
                                         damage: int, is_player: bool = True) -> str:
        """
        Generate AI-powered critical hit description.
        
        Args:
            attacker_name (str): Name of the attacker
            target_name (str): Name of the target
            damage (int): Damage dealt
            is_player (bool): Whether attacker is player
            
        Returns:
            str: Critical hit description
        """
        if self.openai_client:
            try:
                attacker_type = "heroic adventurer" if is_player else "fearsome creature"
                prompt = f"""You are a fantasy combat narrator. A {attacker_type} named {attacker_name} just scored a critical hit against {target_name}, dealing {damage} damage.

Write a brief, exciting description (1-2 sentences) explaining WHY this was a critical hit. Focus on skill, luck, or a perfect strike. Make it feel epic and satisfying.

Examples:
- "A perfect strike finds the gap in armor!"
- "Lightning-fast reflexes catch the enemy off-guard!"
- "A surge of adrenaline guides the blade true!"

Keep it short and punchy."""

                description = self.openai_client.generate_completion(prompt, max_tokens=50, temperature=0.9)
                if description:
                    return description
            except Exception as e:
                print(f"OpenAI critical hit description failed: {e}")
        
        # Fallback critical hit descriptions
        fallbacks = [
            "A perfect strike finds its mark!",
            "Lightning reflexes guide the attack!",
            "A surge of power flows through the strike!",
            "The attack lands with devastating precision!",
            "Fortune favors the bold in this moment!"
        ]
        return random.choice(fallbacks)
    
    def _check_critical_hit(self) -> bool:
        """
        Check if an attack is a critical hit (10% chance).
        
        Returns:
            bool: True if critical hit
        """
        return random.random() < 0.10  # 10% critical hit chance
    
    def _execute_ally_attack(self, player: Player, enemy: Enemy, battle_log: list) -> int:
        """
        Execute ally special attack.
        
        Args:
            player (Player): Player object
            enemy (Enemy): Enemy object
            battle_log (list): Battle log to append to
            
        Returns:
            int: Damage dealt
        """
        ally_data = player.current_ally
        base_damage = player.attack_power
        ally_bonus = ally_data.get('attack_power', 15)  # Allies give bonus damage
        total_damage = base_damage + ally_bonus
        
        # Check for critical hit
        is_critical = self._check_critical_hit()
        if is_critical:
            total_damage = int(total_damage * 1.5)  # 50% bonus for critical
        
        # Add some variance
        damage = calculate_damage_with_variance(total_damage)
        enemy.take_damage(damage)
        
        # Generate description
        base_description = f"{ally_data['name']} unleashes their special move, dealing {damage} damage!"
        if is_critical:
            crit_desc = self._generate_critical_hit_description(ally_data['name'], enemy.name, damage, True)
            description = f"{base_description} **CRITICAL HIT!** {crit_desc}"
        else:
            description = base_description
        
        battle_log.append({
            "type": "ally_attack",
            "attacker": f"{player.name} with {ally_data['name']}",
            "target": enemy.name,
            "damage": damage,
            "is_critical": is_critical,
            "description": description
        })
        
        return damage
    
    def _execute_player_attack(self, player: Player, enemy: Enemy, battle_log: list) -> int:
        """
        Execute regular player attack.
        
        Args:
            player (Player): Player object
            enemy (Enemy): Enemy object
            battle_log (list): Battle log to append to
            
        Returns:
            int: Damage dealt
        """
        # Check for critical hit
        is_critical = self._check_critical_hit()
        base_damage = player.attack_power
        
        if is_critical:
            base_damage = int(base_damage * 1.5)  # 50% bonus for critical
        
        damage = calculate_damage_with_variance(base_damage)
        enemy.take_damage(damage)
        
        # Generate description
        base_description = f"{player.name} attacks {enemy.name} for {damage} damage!"
        if is_critical:
            crit_desc = self._generate_critical_hit_description(player.name, enemy.name, damage, True)
            description = f"{base_description} **CRITICAL HIT!** {crit_desc}"
        else:
            description = base_description
        
        battle_log.append({
            "type": "player_attack",
            "attacker": player.name,
            "target": enemy.name,
            "damage": damage,
            "is_critical": is_critical,
            "description": description
        })
        
        return damage
    
    def _execute_enemy_attack(self, player: Player, enemy: Enemy, battle_log: list) -> int:
        """
        Execute enemy attack on player.
        
        Args:
            player (Player): Player object
            enemy (Enemy): Enemy object
            battle_log (list): Battle log to append to
            
        Returns:
            int: Damage dealt
        """
        # Check for critical hit
        is_critical = self._check_critical_hit()
        base_damage = enemy.attack_power
        
        if is_critical:
            base_damage = int(base_damage * 1.5)  # 50% bonus for critical
        
        damage = calculate_damage_with_variance(base_damage)
        player.take_damage(damage)
        
        # Generate description
        base_description = f"{enemy.name} attacks {player.name} for {damage} damage!"
        if is_critical:
            crit_desc = self._generate_critical_hit_description(enemy.name, player.name, damage, False)
            description = f"{base_description} **CRITICAL HIT!** {crit_desc}"
        else:
            description = base_description
        
        battle_log.append({
            "type": "enemy_attack",
            "attacker": enemy.name,
            "target": player.name,
            "damage": damage,
            "is_critical": is_critical,
            "description": description
        })
        
        return damage
    
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
        # Award gold and experience
        gold_reward = enemy.get_gold_reward()
        exp_reward = enemy.exp_reward
        player.add_gold(gold_reward)
        
        # Award experience and check for level up
        leveled_up = player.gain_experience(exp_reward)
        
        # Small chance of finding a healing item (20%)
        healing_found = 0
        if random.random() < 0.2:
            healing_found = random.randint(10, 25)
            player.heal(healing_found)
        
        message = f"Victory! You defeated {enemy.name} and earned {gold_reward} gold and {exp_reward} experience."
        if leveled_up:
            message += f" **LEVEL UP!** You are now level {player.level}!"
        if healing_found > 0:
            message += f" You also found healing herbs and restored {healing_found} health!"
        
        return {
            "outcome": "victory",
            "gold_earned": gold_reward,
            "exp_earned": exp_reward,
            "leveled_up": leveled_up,
            "new_level": player.level if leveled_up else None,
            "total_gold": player.gold,
            "healing_found": healing_found,
            "current_health": player.health,
            "max_health": player.max_health,
            "level_progress": player.get_current_level_progress(),
            "message": message
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