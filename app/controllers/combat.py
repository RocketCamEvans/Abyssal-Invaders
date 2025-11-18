"""
Combat controller for handling battles between players and enemies.
"""

from typing import Tuple, Dict, Any, Optional
from ..models import Player, Enemy, Room
from ..models.element import get_element_effectiveness, get_element_matchup_text
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
    
    def execute_attack(self, player: Player, use_ally: bool = False, ally_index: Optional[int] = None, timing_multiplier: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute a player attack in turn-based combat.
        
        Args:
            player (Player): Player object
            use_ally (bool): Whether to use ally special attack
            ally_index (Optional[int]): Index of the ally to use from player's allies list
            timing_multiplier (Optional[float]): Damage multiplier from timing mini-game (0.7, 0.9, 1.0, 1.15)
            
        Returns:
            Dict[str, Any]: Attack result
        """
        if not player.in_battle or not player.current_enemy:
            return create_error_response("Player is not in battle!")
        
        # Create enemy object from stored data
        enemy = Enemy.from_dict(player.current_enemy)
        
        battle_log = []
        
        # Store timing multiplier for use in _execute_player_attack
        self.timing_multiplier = timing_multiplier
        
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
                # Skip enemy turn - set to 2 so enemy skips this turn and the next
                enemy.skip_next_turn = 2
                battle_log.append({
                    "type": "ally_skip",
                    "ally": ally.name,
                    "target": enemy.name,
                    "description": f"{result['description']} {result['message']}"
                })
            elif result['type'] == 'caster_poison' or result['type'] == 'caster_paralysis':
                # Inflict ailment on enemy
                from ..models.ailment import Ailment, calculate_ailment_duration
                
                ailment_type = 'poison' if result['type'] == 'caster_poison' else 'paralysis'
                severity = result['value']  # Ally's value is the severity
                duration = calculate_ailment_duration(severity)
                
                ailment = Ailment(ailment_type, severity, duration)
                enemy.add_ailment(ailment)
                
                ailment_emoji = ailment.get_emoji()
                battle_log.append({
                    "type": "ally_caster",
                    "ally": ally.name,
                    "target": enemy.name,
                    "ailment": ailment_type,
                    "severity": severity,
                    "description": f"{result['description']} {enemy.name} is afflicted with {ailment.get_name()} {ailment_emoji} (Severity {severity})! {result['message']}"
                })
            
            # Mark ally as used this battle (but don't remove from player's list - allies are permanent!)
            player.ally_used = True
            
            # Update the ally in player's allies list to persist the used state
            player.allies[ally_index] = ally
            
            print(f"DEBUG COMBAT: After using ally, player still has {len(player.allies)} allies")
            
        else:
            # Determine turn order and double attack based on speed
            # Apply shackled reduction to speed
            player_speed = self._get_effective_stat(player, 'speed', player.speed)
            enemy_speed = self._get_effective_stat(enemy, 'speed', enemy.speed)
            
            # Check for 3x speed advantage (double attack)
            player_double_attack = player_speed >= enemy_speed * 3
            enemy_double_attack = enemy_speed >= player_speed * 3
            
            player_goes_first = player_speed >= enemy_speed
            
            print(f"DEBUG COMBAT: Player speed={player_speed}, Enemy speed={enemy_speed}")
            print(f"DEBUG COMBAT: Player double attack={player_double_attack}, Enemy double attack={enemy_double_attack}")
            
            if player_double_attack:
                # Player is 3x faster - attacks twice before enemy can respond
                battle_log.append({
                    "type": "speed_advantage",
                    "description": f"⚡ Your incredible speed allows you to strike twice before {enemy.name} can react!"
                })
                
                # First player attack
                damage1 = self._execute_player_attack(player, enemy, battle_log)
                
                # Check if enemy is still alive for second attack
                if enemy.is_alive():
                    # Second player attack
                    damage2 = self._execute_player_attack(player, enemy, battle_log)
                    
                    # Enemy gets one attack if still alive
                    if enemy.is_alive():
                        self._execute_enemy_attack(player, enemy, battle_log)
                        
            elif enemy_double_attack:
                # Enemy is 3x faster - attacks twice before player can respond
                battle_log.append({
                    "type": "speed_advantage",
                    "description": f"⚡ {enemy.name}'s blinding speed allows it to strike twice before you can react!"
                })
                
                # First enemy attack
                self._execute_enemy_attack(player, enemy, battle_log)
                
                # Check if player is still alive for second attack
                if player.is_alive():
                    # Second enemy attack
                    self._execute_enemy_attack(player, enemy, battle_log)
                    
                    # Player gets one attack if still alive
                    if player.is_alive():
                        damage = self._execute_player_attack(player, enemy, battle_log)
                        
            elif player_goes_first:
                # Normal speed - player attacks first
                damage = self._execute_player_attack(player, enemy, battle_log)
                
                # Check if enemy is defeated
                if enemy.is_alive():
                    # Enemy attacks second (if still alive)
                    self._execute_enemy_attack(player, enemy, battle_log)
            else:
                # Normal speed - enemy attacks first
                self._execute_enemy_attack(player, enemy, battle_log)
                
                # Check if player is still alive for their attack
                if player.is_alive():
                    # Player attacks second (if still alive)
                    damage = self._execute_player_attack(player, enemy, battle_log)
        
        # Check if enemy is defeated after all attacks
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
                    "ally_used": player.ally_used,
                    "ailments": [ailment.to_dict() for ailment in player.ailments]
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
        
        # Update stored enemy data
        player.current_enemy = enemy.to_dict()
        
        # Check if player is defeated after all attacks
        if not player.is_alive():
            # Get proper defeat result with custom death message
            defeat_result = self._handle_player_defeat(player, enemy)
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
                    "ally_used": player.ally_used,
                    "ailments": [ailment.to_dict() for ailment in player.ailments]
                },
                "enemy": enemy.to_dict(),
                "defeat_result": defeat_result
            }, defeat_result.get('message', 'Player defeated!'))
        
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
                "ally_used": player.ally_used,
                "ailments": [ailment.to_dict() for ailment in player.ailments]
            },
            "enemy": enemy.to_dict(),
            "ally_available": player.current_ally and not player.ally_used
        }, "Attack executed")
    
    def execute_flee(self, player: Player) -> Dict[str, Any]:
        """
        Execute fleeing from battle using speed-based formula.
        
        Args:
            player (Player): Player object
            
        Returns:
            Dict[str, Any]: Flee result
        """
        if not player.in_battle:
            return create_error_response("Player is not in battle!")
        
        # Reconstruct enemy from player's current_enemy data
        if not player.current_enemy:
            return create_error_response("No enemy data found!")
        
        enemy = Enemy.from_dict(player.current_enemy)
        
        # Get room information
        room_data = player.battle_room
        room = Room.from_dict(room_data) if room_data else None
        
        # Use the new speed-based flee system
        success, result = self.flee_from_combat(player, enemy)
        
        # Add room direction info after fleeing (only if successful)
        if success and room:
            result_data = result.get('data', {})
            if result_data:
                result_data["room_info"] = {
                    "current_room": room.get_room_info(),
                    "available_directions": room.get_available_directions(),
                    "message": "You escaped! You can now explore the room or move to safety."
                }
        
        return result
    
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
                prompt = f"""Battle starting in cursed office building!

Player: {player.name} (HP:{player.health})
Enemy: {enemy.name} - {enemy.description}
Location: {room.name}

Write 1-2 dramatic sentences (MAX 200 chars) setting the scene. Make it tense and atmospheric, fitting the office-fantasy theme."""

                description = self.openai_client.generate_completion(prompt, max_tokens=60, temperature=0.7, generation_type="battle_description")
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
                attacker_type = "office warrior" if is_player else "cursed creature"
                prompt = f"""CRITICAL HIT in the cursed office!

{attacker_name} ({attacker_type}) lands a devastating blow on {target_name} for {damage} damage!

Describe what made this hit critical (MAX 150 chars). Be dramatic and exciting, fitting the office-fantasy setting."""

                description = self.openai_client.generate_completion(prompt, max_tokens=40, temperature=0.75, generation_type="critical_hit")
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
        Check if an attack is a critical hit (2% chance).
        
        Returns:
            bool: True if critical hit
        """
        return random.random() < 0.02  # 2% critical hit chance
    
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
            
            # Apply elemental effectiveness if ally has an element
            ally_element = ally_data.get('element')
            enemy_element = getattr(enemy, 'element', 'intern')
            element_multiplier = 1.0
            element_desc = ""
            
            if ally_element:
                element_multiplier = get_element_effectiveness(ally_element, enemy_element)
                damage_dealt = int(damage_dealt * element_multiplier)
                element_desc = get_element_matchup_text(ally_element, enemy_element)
                if element_desc:
                    element_desc = f" {element_desc}"
            
            enemy.take_damage(damage_dealt)
            
            description = f"{ally_data['description']} {ally_name} deals {damage_dealt} damage!{element_desc} {leaving_message}"
            
            battle_log.append({
                "type": "ally_attack",
                "attacker": ally_name,
                "target": enemy.name,
                "damage": damage_dealt,
                "is_critical": False,
                "element_multiplier": element_multiplier,
                "description": description
            })
            
        elif ally_type == 'skipper':
            # Skip enemy's next 2 turns (this turn + next turn)
            enemy.skip_next_turn = 2
            
            description = f"{ally_data['description']} The enemy is stunned and will skip their next turn! {leaving_message}"
            
            battle_log.append({
                "type": "ally_skip",
                "ally": ally_name,
                "target": enemy.name,
                "description": description
            })
        
        return damage_dealt
    
    def _process_ailments_start_of_turn(self, entity, entity_name: str, battle_log: list):
        """
        Process ailments at the start of an entity's turn.
        
        Args:
            entity: Player or Enemy object
            entity_name (str): Name for display
            battle_log (list): Battle log to append to
        """
        if not hasattr(entity, 'ailments') or not entity.ailments:
            return
        
        # Process each active ailment
        for ailment in entity.ailments:
            # Apply poison damage
            if ailment.ailment_type == 'poison':
                damage = ailment.apply_poison_damage(entity.max_health)
                entity.health = max(0, entity.health - damage)
                
                battle_log.append({
                    "type": "ailment_damage",
                    "target": entity_name,
                    "ailment": "poison",
                    "damage": damage,
                    "description": f"{ailment.get_emoji()} {entity_name} takes {damage} poison damage! (Turns left: {ailment.turns_remaining})"
                })
    
    def _check_paralysis(self, entity, entity_name: str, battle_log: list) -> bool:
        """
        Check if entity is paralyzed and should skip turn.
        
        Args:
            entity: Player or Enemy object
            entity_name (str): Name for display
            battle_log (list): Battle log to append to
            
        Returns:
            bool: True if entity should skip turn
        """
        if not hasattr(entity, 'ailments') or not entity.ailments:
            return False
        
        for ailment in entity.ailments:
            if ailment.ailment_type == 'paralysis':
                if ailment.check_paralysis():
                    battle_log.append({
                        "type": "ailment_skip",
                        "target": entity_name,
                        "ailment": "paralysis",
                        "description": f"{ailment.get_emoji()} {entity_name} is paralyzed and cannot move!"
                    })
                    return True
        
        return False
    
    def _check_blindness(self, entity, entity_name: str, battle_log: list) -> bool:
        """
        Check if entity is blinded and misses their attack.
        
        Args:
            entity: Player or Enemy object
            entity_name (str): Name for display
            battle_log (list): Battle log to append to
            
        Returns:
            bool: True if attack should miss
        """
        if not hasattr(entity, 'ailments') or not entity.ailments:
            return False
        
        for ailment in entity.ailments:
            if ailment.ailment_type == 'blinded':
                if ailment.check_blind_miss():
                    battle_log.append({
                        "type": "ailment_miss",
                        "target": entity_name,
                        "ailment": "blinded",
                        "description": f"{ailment.get_emoji()} {entity_name} is blinded and misses their attack!"
                    })
                    return True
        
        return False
    
    def _get_effective_stat(self, entity, stat_name: str, base_value: int) -> int:
        """
        Get the effective stat value after applying ailment reductions.
        
        Args:
            entity: Player or Enemy object
            stat_name (str): Stat type ('attack_power', 'defense', 'speed')
            base_value (int): Base stat value
            
        Returns:
            int: Effective stat value after reductions
        """
        if not hasattr(entity, 'ailments') or not entity.ailments:
            return base_value
        
        multiplier = 1.0
        
        for ailment in entity.ailments:
            if stat_name == 'attack_power' and ailment.ailment_type == 'weakened':
                multiplier *= ailment.get_stat_reduction_percentage('weakened')
            elif stat_name == 'defense' and ailment.ailment_type == 'irradiated':
                multiplier *= ailment.get_stat_reduction_percentage('irradiated')
            elif stat_name == 'speed' and ailment.ailment_type == 'shackled':
                multiplier *= ailment.get_stat_reduction_percentage('shackled')
        
        return int(base_value * multiplier)
    
    def _can_use_allies(self, player) -> bool:
        """
        Check if player can use allies (not infatuated).
        
        Args:
            player: Player object
            
        Returns:
            bool: True if player can use allies
        """
        if not hasattr(player, 'ailments') or not player.ailments:
            return True
        
        for ailment in player.ailments:
            if ailment.prevents_ally_use():
                return False
        
        return True
    
    def _tick_ailments_end_of_turn(self, entity, entity_name: str, battle_log: list):
        """
        Tick down ailments at end of turn and remove expired ones.
        
        Args:
            entity: Player or Enemy object
            entity_name (str): Name for display
            battle_log (list): Battle log to append to
        """
        if not hasattr(entity, 'ailments'):
            return
        
        expired = entity.tick_ailments()
        for ailment in expired:
            battle_log.append({
                "type": "ailment_expired",
                "target": entity_name,
                "ailment": ailment.ailment_type,
                "description": f"{entity_name}'s {ailment.get_name()} has worn off."
            })
    
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
        # Process player ailments at start of turn
        self._process_ailments_start_of_turn(player, player.name, battle_log)
        
        # Check if player dies from poison
        if not player.is_alive():
            return 0
        
        # Check if player is paralyzed
        if self._check_paralysis(player, player.name, battle_log):
            # Tick ailments even if paralyzed
            self._tick_ailments_end_of_turn(player, player.name, battle_log)
            return 0
        
        # Check if player is blinded and misses
        if self._check_blindness(player, player.name, battle_log):
            # Tick ailments even if missed
            self._tick_ailments_end_of_turn(player, player.name, battle_log)
            return 0
        
        # Check for critical hit
        is_critical = self._check_critical_hit()
        
        # Get total stats including gear bonuses
        total_stats = player.get_total_stats()
        
        # Get effective attack power (after weakened reduction, using total with gear)
        effective_attack = self._get_effective_stat(player, 'attack_power', total_stats['attack']['total'])
        base_damage = effective_attack
        
        if is_critical:
            base_damage = int(base_damage * 1.5)  # 50% bonus for critical
        
        damage = calculate_damage_with_variance(base_damage)
        
        # Apply timing multiplier if present
        timing_multiplier = getattr(self, 'timing_multiplier', None)
        if timing_multiplier is not None:
            damage = int(damage * timing_multiplier)
            print(f"DEBUG COMBAT: Applied timing multiplier {timing_multiplier}x, damage after timing: {damage}")
        
        # Apply elemental effectiveness using player's attack element (from weapon)
        player_attack_element = getattr(player, 'attack_element', 'intern')
        enemy_element = getattr(enemy, 'element', 'intern')
        element_multiplier = get_element_effectiveness(player_attack_element, enemy_element)
        
        if element_multiplier != 1.0:
            damage = int(damage * element_multiplier)
            print(f"DEBUG COMBAT: Applied element multiplier {element_multiplier}x ({player_attack_element} vs {enemy_element}), final damage: {damage}")
        
        enemy.take_damage(damage)
        
        # Generate description
        timing_desc = ""
        if timing_multiplier is not None:
            if timing_multiplier >= 1.15:
                timing_desc = " **PERFECT TIMING!**"
            elif timing_multiplier >= 1.0:
                timing_desc = " *Good timing.*"
            elif timing_multiplier >= 0.9:
                timing_desc = " *Slightly off.*"
            else:
                timing_desc = " *Poorly timed.*"
        
        element_desc = get_element_matchup_text(player_attack_element, enemy_element) or ""
        if element_desc:
            element_desc = " " + element_desc
        
        base_description = f"{player.name} attacks {enemy.name} for {damage} damage!{timing_desc}{element_desc}"
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
            "timing_multiplier": timing_multiplier,
            "element_multiplier": element_multiplier,
            "description": description
        })
        
        # Clear timing multiplier after use
        if hasattr(self, 'timing_multiplier'):
            delattr(self, 'timing_multiplier')
        
        # Tick ailments at end of turn
        self._tick_ailments_end_of_turn(player, player.name, battle_log)
        
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
        # Process enemy ailments at start of turn
        self._process_ailments_start_of_turn(enemy, enemy.name, battle_log)
        
        # Check if enemy dies from poison
        if not enemy.is_alive():
            return 0
        
        # Check if enemy is paralyzed
        if self._check_paralysis(enemy, enemy.name, battle_log):
            # Tick ailments even if paralyzed
            self._tick_ailments_end_of_turn(enemy, enemy.name, battle_log)
            return 0
        
        # Check if enemy should skip this turn (from skipper ally)
        if hasattr(enemy, 'skip_next_turn') and enemy.skip_next_turn:
            if isinstance(enemy.skip_next_turn, int):
                # Decrement the counter
                enemy.skip_next_turn -= 1
            else:
                # Legacy boolean support - convert to counter
                enemy.skip_next_turn = 0
            
            battle_log.append({
                "type": "enemy_skip",
                "attacker": enemy.name,
                "description": f"{enemy.name} is stunned and skips their turn!"
            })
            return 0
        
        # Check if enemy is blinded and misses
        if self._check_blindness(enemy, enemy.name, battle_log):
            # Tick ailments even if missed
            self._tick_ailments_end_of_turn(enemy, enemy.name, battle_log)
            return 0
        
        # Check for critical hit
        is_critical = self._check_critical_hit()
        
        # Get effective attack power (after weakened reduction)
        effective_attack = self._get_effective_stat(enemy, 'attack_power', enemy.attack_power)
        base_damage = effective_attack
        
        if is_critical:
            base_damage = int(base_damage * 1.5)  # 50% bonus for critical
        
        damage = calculate_damage_with_variance(base_damage)
        
        # Apply elemental effectiveness (enemy attacking player, use player's defense element from armor)
        enemy_element = getattr(enemy, 'element', 'intern')
        player_defense_element = getattr(player, 'defense_element', 'intern')
        element_multiplier = get_element_effectiveness(enemy_element, player_defense_element)
        damage = int(damage * element_multiplier)
        
        player.take_damage(damage)
        
        # Generate description with elemental effectiveness
        base_description = f"{enemy.name} attacks {player.name} for {damage} damage!"
        element_desc = get_element_matchup_text(enemy_element, player_defense_element)
        if element_desc:
            base_description += f" {element_desc}"
        
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
            "element_multiplier": element_multiplier,
            "description": description
        })
        
        # Try to inflict ailments if enemy has that ability
        # Support both old single type and new multiple types for backward compatibility
        ailment_types_to_try = []
        if hasattr(enemy, 'ailment_inflict_types') and enemy.ailment_inflict_types:
            ailment_types_to_try = enemy.ailment_inflict_types
        elif hasattr(enemy, 'ailment_inflict_type') and enemy.ailment_inflict_type:
            # Backward compatibility
            ailment_types_to_try = [enemy.ailment_inflict_type]
        
        if ailment_types_to_try and hasattr(enemy, 'ailment_inflict_chance') and enemy.ailment_inflict_chance > 0:
            import random
            from ..models.ailment import Ailment, calculate_ailment_severity, calculate_ailment_duration
            
            # ailment_inflict_chance is stored as a decimal (0.0 to 1.0)
            # Convert to percentage for random check
            chance_percentage = enemy.ailment_inflict_chance * 100
            
            for ailment_type in ailment_types_to_try:
                print(f"DEBUG: Enemy {enemy.name} trying to inflict {ailment_type} - chance={enemy.ailment_inflict_chance} ({chance_percentage}%)")
                
                if random.randint(1, 100) <= chance_percentage:
                    # Use custom severity if set, otherwise calculate based on floor
                    if hasattr(enemy, 'ailment_inflict_severity') and enemy.ailment_inflict_severity is not None:
                        severity = max(0, min(5, enemy.ailment_inflict_severity))  # Clamp to 0-5
                    else:
                        severity = calculate_ailment_severity(enemy.floor)
                    
                    duration = calculate_ailment_duration(severity)
                    ailment = Ailment(ailment_type, severity, duration)
                    player.add_ailment(ailment)
                    
                    print(f"DEBUG: ✅ Enemy {enemy.name} successfully inflicted {ailment_type} on player! (Severity {severity})")
                    
                    battle_log.append({
                        "type": "enemy_ailment_inflict",
                        "attacker": enemy.name,
                        "target": player.name,
                        "ailment": ailment_type,
                        "severity": severity,
                        "description": f"{ailment.get_emoji()} {enemy.name} inflicts {ailment.get_name()} on {player.name}! (Severity {severity})"
                    })
                else:
                    print(f"DEBUG: ❌ Enemy {enemy.name} failed to inflict {ailment_type}")
        
        
        # Tick ailments at end of turn
        self._tick_ailments_end_of_turn(enemy, enemy.name, battle_log)
        
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
        # Get total stats including gear bonuses
        total_stats = player.get_total_stats()
        base_damage = total_stats['attack']['total']
        
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
        # Check if player is infatuated and cannot use allies
        if not self._can_use_allies(player):
            return False, create_error_response("💖 You are infatuated and cannot use allies!")
        
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
        
        # Mark player as dead (health = 0) for game over screen
        player.health = 0
        
        # Generate custom death message using LLM
        death_message = f"You have been defeated by {enemy.name}! You lost {gold_lost} gold."
        
        if self.openai_client:
            try:
                prompt = f"""Player defeated and killed in cursed office dungeon!

Defeated by: {enemy.name} - {enemy.description}

Write a dramatic death message (1-2 sentences). The player was KILLED and DIED - they lost {gold_lost} gold. Make it dark and final. Fit the office-fantasy setting. DO NOT mention surviving or escaping."""
                
                custom_message = self.openai_client.generate_completion(
                    prompt, 
                    max_tokens=80, 
                    temperature=0.75, 
                    generation_type="death_message"
                )
                
                if custom_message and len(custom_message.strip()) > 10:
                    death_message = custom_message.strip()
            except Exception as e:
                print(f"Failed to generate custom death message: {e}")
        
        return {
            "outcome": "defeat",
            "gold_lost": gold_lost,
            "remaining_gold": player.gold,
            "health_restored": 1,
            "message": death_message
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
        # Calculate flee chance based on formula:
        # 50% + 3.5*(player_speed - enemy_speed) - floor(current_floor_number/5)
        import math
        import random
        
        # Check if enemy has skip_next_turn active (from skipper ally)
        # If enemy is skipped, fleeing is guaranteed with no cost
        if hasattr(enemy, 'skip_next_turn') and enemy.skip_next_turn > 0:
            print(f"DEBUG FLEE: Enemy turn is skipped by ally! Guaranteed escape with no cost.")
            
            # End the battle without losing gold or taking damage
            player.end_battle()
            
            return True, create_success_response({
                "outcome": "fled",
                "message": "With the enemy distracted by your ally, you slip away unnoticed! No gold lost.",
                "gold_lost": 0,
                "player": {
                    "health": f"{player.health}/{player.max_health}",
                    "gold": player.gold,
                    "in_battle": player.in_battle,
                    "is_alive": player.is_alive(),
                    "allies": [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies]
                }
            })
        
        speed_difference = player.speed - enemy.speed
        floor_penalty = math.floor(player.floor / 5)
        
        # Calculate components (using percentages as decimals)
        base_chance = 0.50  # 50%
        speed_modifier = speed_difference * 0.035  # 3.5% per speed difference
        floor_modifier = floor_penalty * 0.01  # 1% per 5 floors
        
        flee_chance = base_chance + speed_modifier - floor_modifier
        
        # Clamp flee chance between 10% and 95%
        flee_chance_unclamped = flee_chance
        flee_chance = max(0.10, min(0.95, flee_chance))
        
        # Generate random roll
        random_roll = random.random()
        
        print(f"DEBUG FLEE: Player speed: {player.speed}, Enemy speed: {enemy.speed}")
        print(f"DEBUG FLEE: Speed diff: {speed_difference}, Floor: {player.floor}, Floor penalty: {floor_penalty}")
        print(f"DEBUG FLEE: Base: {base_chance*100:.1f}%, Speed mod: {speed_modifier*100:.1f}%, Floor mod: -{floor_modifier*100:.1f}%")
        print(f"DEBUG FLEE: Calculated chance: {flee_chance_unclamped*100:.1f}% -> Clamped: {flee_chance*100:.1f}%")
        print(f"DEBUG FLEE: Random roll: {random_roll:.4f}, Success threshold: {flee_chance:.4f}")
        print(f"DEBUG FLEE: Result: {'SUCCESS' if random_roll < flee_chance else 'FAILURE'}")
        
        if random_roll < flee_chance:
            # Successful flee - lose half of current gold
            gold_lost = player.gold // 2
            player.gold -= gold_lost
            
            # End the battle
            player.end_battle()
            
            return True, create_success_response({
                "outcome": "fled",
                "message": f"You successfully fled from combat! You lost {gold_lost} gold in your hasty retreat.",
                "gold_lost": gold_lost,
                "player": {
                    "health": f"{player.health}/{player.max_health}",
                    "gold": player.gold,
                    "in_battle": player.in_battle,
                    "is_alive": player.is_alive(),
                    "allies": [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies]
                }
            })
        else:
            # Failed flee - enemy gets a free attack (bypasses defense)
            base_damage = enemy.attack()
            # Apply damage directly without defense reduction (player is caught off-guard)
            player.health = max(0, player.health - base_damage)
            
            message = (f"Failed to flee! {enemy.name} catches you off-guard and attacks for {base_damage} damage! "
                      f"You have {player.health} health remaining.")
            
            # Check if player died from the flee attempt
            if not player.is_alive():
                player.end_battle()
                return False, create_success_response({
                    "messages": [message, "You have been defeated!"],
                    "battle_ended": True,
                    "fled": False,
                    "victory": False,
                    "player": {
                        "health": f"{player.health}/{player.max_health}",
                        "gold": player.gold,
                        "level": player.level,
                        "in_battle": player.in_battle,
                        "is_alive": player.is_alive(),
                        "allies": [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies]
                    },
                    "enemy": enemy.to_dict()
                }, "Player defeated while fleeing!")
            
            # Return updated player state on failed flee (battle continues)
            return False, create_success_response({
                "messages": [message],
                "battle_ended": False,
                "fled": False,
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
            }, "Failed to flee!")