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
            "winner": "player" if result['outcome'] == 'victory' else "enemy",
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
            "message": "Battle started!",
            "description": battle_description,
            "player": {
                "health": f"{player.health}/{player.max_health}",
                "in_battle": player.in_battle,
                "is_alive": player.is_alive(),
                "allies": [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies],
                "ally_used": player.ally_used
            },
            "enemy": enemy.to_dict(),
            "ally": ally_data
        }, "Battle initiated")
    
    def execute_attack(self, player: Player, use_ally: bool = False, ally_index: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a player attack in turn-based combat.
        
        Args:
            player (Player): Player object
            use_ally (bool): Whether to use ally special attack
            ally_index (Optional[int]): Index of the ally to use from player's allies list
            
        Returns:
            Dict[str, Any]: Attack result
        """
        if not player.in_battle or not player.current_enemy:
            return create_error_response("Player is not in battle!")
        
        # Create enemy object from stored data
        enemy = Enemy.from_dict(player.current_enemy)
        
        battle_log = []
        
        # Player attack (with ally if requested)
        if use_ally and ally_index is not None and 0 <= ally_index < len(player.allies):
            print(f"DEBUG COMBAT: Player has {len(player.allies)} allies, using index {ally_index}")
            
            # Check if ally was already used this battle
            if player.ally_used:
                return create_error_response("You can only use one ally per battle!")
            
            # Get the ally from player's allies list
            from ..models.ally import Ally
            ally_data = player.allies[ally_index]
            
            print(f"DEBUG COMBAT: Ally data type: {type(ally_data)}")
            
            # Handle both Ally objects and dicts
            if isinstance(ally_data, Ally):
                ally = ally_data
            elif isinstance(ally_data, dict):
                ally = Ally.from_dict(ally_data)
            else:
                return create_error_response("Invalid ally data")
            
            print(f"DEBUG COMBAT: Using ally {ally.name}")
            
            if not ally.is_available():
                return create_error_response("This ally has already been used!")
            
            # Use the ally's ability
            result = ally.use_ability()
            
            # Apply ally effect based on type
            if result['type'] == 'healer':
                # Heal player
                old_health = player.health
                player.heal(result['value'])
                actual_heal = player.health - old_health
                battle_log.append({
                    "type": "ally_heal",
                    "ally": ally.name,
                    "heal_amount": actual_heal,
                    "description": f"{result['description']} You recover {actual_heal} HP! {result['message']}"
                })
            elif result['type'] == 'attacker':
                # Damage enemy
                damage = calculate_damage_with_variance(result['value'])
                enemy.take_damage(damage)
                battle_log.append({
                    "type": "ally_attack",
                    "attacker": ally.name,
                    "target": enemy.name,
                    "damage": damage,
                    "description": f"{result['description']} {ally.name} deals {damage} damage! {result['message']}"
                })
            elif result['type'] == 'skipper':
                # Skip enemy turn
                enemy.skip_next_turn = True
                battle_log.append({
                    "type": "ally_skip",
                    "ally": ally.name,
                    "target": enemy.name,
                    "description": f"{result['description']} {result['message']}"
                })
            
            # Mark ally as used this battle (but don't remove from player's list - allies are permanent!)
            player.ally_used = True
            
            # Update the ally in player's allies list to persist the used state
            player.allies[ally_index] = ally
            
            print(f"DEBUG COMBAT: After using ally, player still has {len(player.allies)} allies")
            
        else:
            damage = self._execute_player_attack(player, enemy, battle_log)
        
        # Check if enemy is defeated
        if not enemy.is_alive():
            reward = self._handle_enemy_defeat(player, enemy)
            
            print(f"DEBUG COMBAT END: Enemy defeated. Player has {len(player.allies)} allies")
            print(f"DEBUG COMBAT END: Allies: {[a.name if hasattr(a, 'name') else str(a) for a in player.allies]}")
            
            # Get room information before ending battle
            room_data = player.battle_room
            room = Room.from_dict(room_data) if room_data else None
            
            player.end_battle()
            
            # Include room directions in victory response
            response_data = {
                "messages": battle_log,
                "battle_ended": True,
                "victory": True,
                "gold_reward": reward.get('gold_earned', 0),
                "exp_reward": reward.get('exp_earned', 0),
                "player": {
                    "health": f"{player.health}/{player.max_health}",
                    "gold": player.gold,
                    "level": player.level,
                    "in_battle": player.in_battle,
                    "is_alive": player.is_alive(),
                    "allies": [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies],
                    "ally_used": player.ally_used
                },
                "enemy": enemy.to_dict()
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
        
        print(f"DEBUG COMBAT TURN END: After enemy attack, player has {len(player.allies)} allies")
        print(f"DEBUG COMBAT TURN END: Allies: {[a.name if hasattr(a, 'name') else str(a) for a in player.allies]}")
        
        # Update stored enemy data
        player.current_enemy = enemy.to_dict()
        
        # Check if player is defeated
        if not player.is_alive():
            player.end_battle()
            
            return create_success_response({
                "messages": battle_log,
                "battle_ended": True,
                "victory": False,
                "player": {
                    "health": f"{player.health}/{player.max_health}",
                    "gold": player.gold,
                    "level": player.level,
                    "in_battle": player.in_battle,
                    "is_alive": player.is_alive(),
                    "allies": [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies],
                    "ally_used": player.ally_used
                },
                "enemy": enemy.to_dict()
            }, "Player defeated!")
        
        return create_success_response({
            "messages": battle_log,
            "battle_ended": False,
            "player": {
                "health": f"{player.health}/{player.max_health}",
                "gold": player.gold,
                "level": player.level,
                "in_battle": player.in_battle,
                "is_alive": player.is_alive(),
                "allies": [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies],
                "ally_used": player.ally_used
            },
            "enemy": enemy.to_dict(),
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
            "messages": [f"You fled from battle and lost {gold_lost} gold!"],
            "gold_lost": gold_lost,
            "battle_ended": True,
            "fled": True,
            "player": {
                "health": f"{player.health}/{player.max_health}",
                "gold": player.gold,
                "level": player.level,
                "in_battle": player.in_battle,
                "is_alive": player.is_alive(),
                "allies": [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies],
                "ally_used": player.ally_used
            }
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
        Generate AI-powered battle description.
        
        Args:
            player (Player): Player object
            enemy (Enemy): Enemy object
            room (Room): Room object
            
        Returns:
            str: Battle description
        """
        if self.openai_client:
            try:
                prompt = f"""You are narrating a whimsical fantasy battle in a cursed office building!

An evil wizard turned Rocket Software into a monster-filled labyrinth. Employees fight back with fantasy powers!

Player: {player.name} (HP: {player.health})
Enemy: {enemy.name} - {enemy.description}
Location: {room.name}

Describe the battle starting in 1-2 SHORT sentences (MAX 200 characters total). Be fantastical, slightly funny, and whimsical. Keep it brief!"""

                description = self.openai_client.generate_completion(prompt, max_tokens=60, temperature=0.8, generation_type="battle_description")
                if description and len(description) <= 250:
                    return description[:250]  # Enforce limit
            except Exception as e:
                print(f"OpenAI battle description failed: {e}")
        
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
                attacker_type = "office warrior" if is_player else "cursed office creature"
                prompt = f"""CRITICAL HIT in the cursed Rocket Software building!

{attacker_name} ({attacker_type}) lands a devastating blow on {target_name} for {damage} damage!

Write a SHORT, exciting critical hit description (MAX 150 characters). Be whimsical, slightly funny, and fantastical. Explain what made this hit so perfect!

Keep it BRIEF and punchy!"""

                description = self.openai_client.generate_completion(prompt, max_tokens=40, temperature=0.9, generation_type="critical_hit")
                if description and len(description) <= 200:
                    return description[:200]  # Enforce limit
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
        Execute ally special ability (attack, heal, or skip).
        
        Args:
            player (Player): Player object
            enemy (Enemy): Enemy object
            battle_log (list): Battle log to append to
            
        Returns:
            int: Damage dealt (0 for healers and skippers)
        """
        ally_data = player.current_ally
        ally_type = ally_data.get('type', 'attacker')
        ally_value = ally_data.get('value', 0)
        ally_name = ally_data.get('name', 'Unknown Ally')
        
        # Create leaving work message
        leaving_message = f"{ally_name} has put in their hours and is leaving work."
        
        damage_dealt = 0
        
        if ally_type == 'healer':
            # Heal the player
            heal_amount = ally_value
            old_health = player.health
            player.heal(heal_amount)
            actual_heal = player.health - old_health
            
            description = f"{ally_data['description']} You recover {actual_heal} HP! {leaving_message}"
            
            battle_log.append({
                "type": "ally_heal",
                "ally": ally_name,
                "heal_amount": actual_heal,
                "description": description
            })
            
        elif ally_type == 'attacker':
            # Deal damage to enemy
            damage_dealt = ally_value
            
            # Add some variance
            damage_dealt = calculate_damage_with_variance(damage_dealt)
            enemy.take_damage(damage_dealt)
            
            description = f"{ally_data['description']} {ally_name} deals {damage_dealt} damage! {leaving_message}"
            
            battle_log.append({
                "type": "ally_attack",
                "attacker": ally_name,
                "target": enemy.name,
                "damage": damage_dealt,
                "is_critical": False,
                "description": description
            })
            
        elif ally_type == 'skipper':
            # Skip enemy's next turn
            enemy.skip_next_turn = True  # We'll need to add this flag to Enemy model
            
            description = f"{ally_data['description']} The enemy is stunned and will skip their next turn! {leaving_message}"
            
            battle_log.append({
                "type": "ally_skip",
                "ally": ally_name,
                "target": enemy.name,
                "description": description
            })
        
        return damage_dealt
    
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
        # Check if enemy should skip this turn
        if hasattr(enemy, 'skip_next_turn') and enemy.skip_next_turn:
            enemy.skip_next_turn = False  # Reset the flag
            battle_log.append({
                "type": "enemy_skip",
                "attacker": enemy.name,
                "description": f"{enemy.name} is stunned and skips their turn!"
            })
            return 0
        
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
        
        # Don't remove ally from player's list - allies are permanent party members!
        # They just can't be used again in the same battle
        
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
        # Reset temporary boosts from items
        player.attack_power -= player.temp_attack_boost
        player.defense -= player.temp_defense_boost
        player.temp_attack_boost = 0
        player.temp_defense_boost = 0
        
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