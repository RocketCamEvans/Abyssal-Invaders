"""
Player class for the dungeon crawler game.
"""

import uuid
from typing import Optional


class Player:
    """
    Represents a player in the dungeon crawler game.
    """
    
    def __init__(self, session_id: Optional[str] = None, name: str = "Unknown Adventurer"):
        self.session_id = session_id or str(uuid.uuid4())
        self.name = name
        self.health = 100
        self.max_health = 100
        self.gold = 0
        self.attack_power = 10
        self.defense = 5
        self.speed = 10  # Speed stat for turn order and flee chance
        self.floor = 1
        self.room_id = "start"
        self.visited_rooms = set()
        self.allies = []  # List of ally objects that can help in combat
        self.inventory = []  # List of item objects
        
        # Dual element system for gear
        self.attack_element = "intern"  # Element for attacking (from weapon)
        self.defense_element = "intern"  # Element for defending (from armor)
        
        # Equipped gear slots
        self.equipped_weapon = None  # Gear object
        self.equipped_armor = None   # Gear object
        self.equipped_accessory = None  # Gear object
        
        # Experience system
        self.experience = 0
        self.level = 1
        
        # Battle state tracking
        self.in_battle = False
        self.current_enemy = None  # Current enemy data (dict)
        self.current_ally = None  # Current ally for this battle (if any)
        self.ally_used = False  # Whether ally has been used in current battle
        self.battle_room = None  # Room data where battle is taking place
        self.temp_attack_boost = 0  # Temporary attack boost from items
        self.temp_defense_boost = 0  # Temporary defense boost from items
        
        # Minimap data
        self.room_positions = {}  # Track room positions: { roomId: {x, y} }
        self.room_info = {}  # Track room features: { roomId: {hasStairs, isShop} }
        
        # Ailments
        self.ailments = []  # List of active ailments
        
        # Achievement tracking
        self.achievements = {}  # Dict of unlocked achievements: {achievement_id: timestamp}
        self.stats = {
            'enemies_defeated': 0,
            'rooms_visited': 0,
            'items_purchased': 0,
            'casino_winnings': 0,
            'allies_recruited': 0,
            'critical_hits_this_battle': 0,
            'consecutive_crits': 0,
            'max_consecutive_crits': 0,
            'damage_taken_this_battle': 0,
            'highest_floor_reached': 1,
            'max_damage_dealt': 0,
            'fully_equipped': 0,
            'perfect_timing_hits': 0,
            'consecutive_perfect_hits': 0,
            'max_consecutive_perfect_hits': 0,
            'items_used': 0,
            'all_legendary_equipped': 0,
            'all_allies_recruited': 0
        }
        
    def take_damage(self, damage: int) -> bool:
        """
        Apply damage to the player.
        
        Args:
            damage (int): Amount of damage to apply
            
        Returns:
            bool: True if player is still alive, False if dead
        """
        # Use total defense including gear bonuses
        total_stats = self.get_total_stats()
        total_defense = total_stats['defense']['total']
        actual_damage = max(0, damage - total_defense)
        self.health = max(0, self.health - actual_damage)
        return self.health > 0
    
    def heal(self, amount: int):
        """
        Heal the player.
        
        Args:
            amount (int): Amount of health to restore
        """
        self.health = min(self.max_health, self.health + amount)
    
    def add_gold(self, amount: int):
        """
        Add gold to the player's inventory.
        
        Args:
            amount (int): Amount of gold to add
        """
        self.gold += amount
    
    def add_ally(self, ally):
        """
        Add an ally to the player's party.
        Max 4 allies, no duplicates by name.
        
        Args:
            ally: Ally object to add
            
        Returns:
            dict: Result with success status and message
        """
        # Check if ally already exists
        for existing_ally in self.allies:
            if existing_ally.name == ally.name:
                return {
                    "success": False,
                    "message": f"{ally.name} is already in your party!"
                }
        
        # Check if at max capacity
        if len(self.allies) >= 4:
            return {
                "success": False,
                "message": "Your party is full! (Max 4 allies) Fire an ally to make room.",
                "at_capacity": True
            }
        
        self.allies.append(ally)
        return {
            "success": True,
            "message": f"{ally.name} joined your party!"
        }
    
    def remove_ally(self, ally_index: int):
        """
        Remove an ally from the player's party (fire them).
        
        Args:
            ally_index (int): Index of the ally to remove
            
        Returns:
            dict: Result with success status and message
        """
        if 0 <= ally_index < len(self.allies):
            ally = self.allies.pop(ally_index)
            return {
                "success": True,
                "message": f"{ally.name} has been fired and left the party."
            }
        return {
            "success": False,
            "message": "Invalid ally index."
        }
    
    def add_item(self, item):
        """
        Add an item to the player's inventory.
        
        Args:
            item: Item object to add
        """
        self.inventory.append(item)
    
    def remove_item(self, item_id: str) -> Optional['Item']:
        """
        Remove an item from inventory by ID.
        
        Args:
            item_id (str): ID of the item to remove
            
        Returns:
            Optional[Item]: The removed item, or None if not found
        """
        for i, item in enumerate(self.inventory):
            if item.item_id == item_id:
                return self.inventory.pop(i)
        return None
    
    def get_item(self, item_id: str) -> Optional['Item']:
        """
        Get an item from inventory by ID.
        
        Args:
            item_id (str): ID of the item to get
            
        Returns:
            Optional[Item]: The item, or None if not found
        """
        for item in self.inventory:
            if item.item_id == item_id:
                return item
        return None
    
    def equip_gear(self, gear):
        """
        Equip a piece of gear.
        
        Args:
            gear: Gear object to equip
            
        Returns:
            dict: Result with success status and message
        """
        from .gear import Gear
        
        if not isinstance(gear, Gear):
            return {"success": False, "message": "Invalid gear object."}
        
        # Unequip current gear in that slot if any
        old_gear = None
        if gear.gear_type == "weapon":
            old_gear = self.equipped_weapon
            self.equipped_weapon = gear
            self.attack_element = gear.element or "intern"
        elif gear.gear_type == "armor":
            old_gear = self.equipped_armor
            self.equipped_armor = gear
            self.defense_element = gear.element or "intern"
        elif gear.gear_type == "accessory":
            old_gear = self.equipped_accessory
            self.equipped_accessory = gear
        else:
            return {"success": False, "message": "Unknown gear type."}
        
        # Remove gear from inventory
        for i, inv_item in enumerate(self.inventory):
            # Handle both Gear objects and dicts
            if hasattr(inv_item, 'gear_id'):
                if inv_item.gear_id == gear.gear_id:
                    self.inventory.pop(i)
                    break
            elif isinstance(inv_item, dict) and 'gear_id' in inv_item:
                if inv_item['gear_id'] == gear.gear_id:
                    self.inventory.pop(i)
                    break
        
        # Add old gear back to inventory if there was one
        if old_gear:
            self.inventory.append(old_gear)
        
        # Check if fully equipped (weapon, armor, and accessory)
        if self.equipped_weapon and self.equipped_armor and self.equipped_accessory:
            self.stats['fully_equipped'] = 1.0
            # Check if all legendary
            weapon_legendary = hasattr(self.equipped_weapon, 'rarity') and self.equipped_weapon.rarity == 'legendary'
            armor_legendary = hasattr(self.equipped_armor, 'rarity') and self.equipped_armor.rarity == 'legendary'
            accessory_legendary = hasattr(self.equipped_accessory, 'rarity') and self.equipped_accessory.rarity == 'legendary'
            
            if weapon_legendary and armor_legendary and accessory_legendary:
                self.stats['all_legendary_equipped'] = 1.0
            else:
                self.stats['all_legendary_equipped'] = 0.0
        else:
            self.stats['fully_equipped'] = 0.0
            self.stats['all_legendary_equipped'] = 0.0
        
        return {
            "success": True,
            "message": f"Equipped {gear.name}!",
            "old_gear": old_gear.to_dict() if old_gear else None
        }
    
    def unequip_gear(self, gear_type: str):
        """
        Unequip gear from a slot.
        
        Args:
            gear_type: Type of gear to unequip ("weapon", "armor", "accessory")
            
        Returns:
            dict: Result with success status and message
        """
        gear = None
        if gear_type == "weapon":
            gear = self.equipped_weapon
            self.equipped_weapon = None
            self.attack_element = "intern"
        elif gear_type == "armor":
            gear = self.equipped_armor
            self.equipped_armor = None
            self.defense_element = "intern"
        elif gear_type == "accessory":
            gear = self.equipped_accessory
            self.equipped_accessory = None
        
        if gear:
            self.inventory.append(gear)
            
            # Check if still fully equipped
            if self.equipped_weapon and self.equipped_armor and self.equipped_accessory:
                self.stats['fully_equipped'] = 1.0
                # Check if all legendary
                weapon_legendary = hasattr(self.equipped_weapon, 'rarity') and self.equipped_weapon.rarity == 'legendary'
                armor_legendary = hasattr(self.equipped_armor, 'rarity') and self.equipped_armor.rarity == 'legendary'
                accessory_legendary = hasattr(self.equipped_accessory, 'rarity') and self.equipped_accessory.rarity == 'legendary'
                
                if weapon_legendary and armor_legendary and accessory_legendary:
                    self.stats['all_legendary_equipped'] = 1.0
                else:
                    self.stats['all_legendary_equipped'] = 0.0
            else:
                self.stats['fully_equipped'] = 0.0
                self.stats['all_legendary_equipped'] = 0.0
            
            return {
                "success": True,
                "message": f"Unequipped {gear.name}.",
                "gear": gear.to_dict()
            }
        
        return {"success": False, "message": f"No {gear_type} equipped."}
    
    def get_total_stats(self):
        """
        Calculate total stats including gear bonuses.
        
        Returns:
            dict: Total stats with base and bonus breakdown
        """
        base_attack = self.attack_power
        base_defense = self.defense
        base_speed = self.speed
        
        gear_attack = 0
        gear_defense = 0
        gear_speed = 0
        
        if self.equipped_weapon:
            gear_attack += self.equipped_weapon.attack_bonus
        if self.equipped_armor:
            gear_defense += self.equipped_armor.defense_bonus
            gear_speed += self.equipped_armor.speed_bonus
        if self.equipped_accessory:
            gear_attack += self.equipped_accessory.attack_bonus
            gear_defense += self.equipped_accessory.defense_bonus
            gear_speed += self.equipped_accessory.speed_bonus
        
        return {
            "attack": {
                "base": base_attack,
                "gear": gear_attack,
                "total": base_attack + gear_attack
            },
            "defense": {
                "base": base_defense,
                "gear": gear_defense,
                "total": base_defense + gear_defense
            },
            "speed": {
                "base": base_speed,
                "gear": gear_speed,
                "total": base_speed + gear_speed
            }
        }
    
    def use_ally_attack(self, ally_index: int) -> Optional[int]:
        """
        Use an ally's attack (one-time use).
        
        Args:
            ally_index (int): Index of the ally to use
            
        Returns:
            Optional[int]: Damage dealt by the ally, or None if invalid
        """
        if 0 <= ally_index < len(self.allies):
            ally = self.allies.pop(ally_index)  # Remove after use
            return ally.attack_power
        return None
    
    def move_to_room(self, room_id: str):
        """
        Move the player to a new room.
        
        Args:
            room_id (str): ID of the room to move to
        """
        self.visited_rooms.add(self.room_id)
        self.room_id = room_id
    
    def go_to_next_floor(self):
        """
        Move the player to the next floor.
        """
        self.floor += 1
        self.room_id = "start"  # Reset to start room of new floor
        self.visited_rooms.clear()  # Clear visited rooms for new floor
    
    def is_alive(self) -> bool:
        """
        Check if the player is still alive.
        
        Returns:
            bool: True if alive, False if dead
        """
        return self.health > 0
    
    def start_battle(self, enemy_data: dict, room_data: dict, ally_data: Optional[dict] = None):
        """
        Start a new battle with an enemy.
        
        Args:
            enemy_data (dict): Enemy data dictionary
            room_data (dict): Room data dictionary
            ally_data (Optional[dict]): Ally data if present
        """
        self.in_battle = True
        self.current_enemy = enemy_data
        self.battle_room = room_data
        self.current_ally = ally_data
        self.ally_used = False
        
        # Reset per-battle stats
        self.stats['critical_hits_this_battle'] = 0
        self.stats['damage_taken_this_battle'] = 0
        self.stats['consecutive_perfect_hits'] = 0
        self.stats['consecutive_crits'] = 0
        
        # Reset all allies' used status at the start of each battle
        # This allows allies to be used once per battle, not once ever
        for ally in self.allies:
            if hasattr(ally, 'used'):
                ally.used = False
    
    def end_battle(self):
        """
        End the current battle and reset battle state.
        """
        self.attack_power -= self.temp_attack_boost
        self.defense -= self.temp_defense_boost
        self.temp_attack_boost = 0
        self.temp_defense_boost = 0
        self.in_battle = False
        self.current_enemy = None
        self.battle_room = None
        self.current_ally = None
        self.ally_used = False
        
        # Reset all allies' "used" flag so they can be used in next battle
        for ally in self.allies:
            ally.used = False
        
        # Remove allies with no uses remaining
        self.allies = [ally for ally in self.allies if ally.uses_remaining > 0]
        
        # Clear ailments at end of battle
        self.clear_ailments()
    
    def flee_battle(self) -> int:
        """
        Flee from battle, losing half of current gold.
        
        Returns:
            int: Amount of gold lost
        """
        gold_lost = self.gold // 2
        self.gold -= gold_lost
        self.end_battle()
        return gold_lost
    
    def gain_experience(self, exp: int) -> bool:
        """
        Add experience and check for level up.
        
        Args:
            exp (int): Experience points to add
            
        Returns:
            bool: True if player leveled up, False otherwise
        """
        self.experience += exp
        exp_needed = self._calculate_exp_for_level(self.level + 1)
        
        if self.experience >= exp_needed:
            self._level_up()
            return True
        return False
    
    def _calculate_exp_for_level(self, level: int) -> int:
        """
        Calculate experience required for a given level.
        
        Args:
            level (int): Target level
            
        Returns:
            int: Experience required
        """
        # Simple exponential curve: level^2 * 100
        return (level - 1) ** 2 * 100
    
    def _level_up(self):
        """
        Level up the player and increase stats slightly.
        """
        self.level += 1
        
        # Small stat increases per level
        old_max_health = self.max_health
        self.max_health += 5  # +5 max health per level
        self.attack_power += 2  # +2 attack per level
        self.defense += 1  # +1 defense per level
        self.speed += 1  # +1 speed per level
        
        # Heal player to full on level up
        health_increase = self.max_health - old_max_health
        self.health += health_increase
        if self.health > self.max_health:
            self.health = self.max_health
    
    def get_current_level_progress(self) -> dict:
        """
        Get information about current level progress.
        
        Returns:
            dict: Level progress information
        """
        current_exp = self.experience
        current_level_exp = self._calculate_exp_for_level(self.level)
        next_level_exp = self._calculate_exp_for_level(self.level + 1)
        
        progress = current_exp - current_level_exp
        needed = next_level_exp - current_level_exp
        
        return {
            'level': self.level,
            'experience': self.experience,
            'progress': progress,
            'needed_for_next': needed,
            'progress_percentage': round((progress / needed) * 100, 1) if needed > 0 else 100
        }
    
    def add_ailment(self, ailment):
        """
        Add an ailment to the player.
        
        Args:
            ailment: Ailment object to add
        """
        # Check if player already has this type of ailment
        for existing in self.ailments:
            if existing.ailment_type == ailment.ailment_type:
                # Replace with new one if severity is higher
                if ailment.severity > existing.severity:
                    self.ailments.remove(existing)
                    self.ailments.append(ailment)
                return
        
        # Add new ailment
        self.ailments.append(ailment)
    
    def remove_ailment(self, ailment_type: str):
        """
        Remove an ailment by type.
        
        Args:
            ailment_type (str): Type of ailment to remove
        """
        self.ailments = [a for a in self.ailments if a.ailment_type != ailment_type]
    
    def clear_ailments(self):
        """Clear all ailments."""
        self.ailments = []
    
    def tick_ailments(self) -> list:
        """
        Update ailments, removing expired ones.
        
        Returns:
            list: List of ailments that expired this turn
        """
        expired = []
        still_active = []
        
        for ailment in self.ailments:
            if not ailment.tick_duration():
                expired.append(ailment)
            else:
                still_active.append(ailment)
        
        self.ailments = still_active
        return expired
    
    def get_ailment_display(self) -> str:
        """
        Get emoji display string for active ailments.
        
        Returns:
            str: Emoji string for ailments
        """
        if not self.ailments:
            return ""
        return " ".join([a.get_emoji() for a in self.ailments])
    
    def unlock_achievement(self, achievement_id: str) -> tuple[bool, int]:
        """
        Unlock an achievement and award its gold reward.
        
        Args:
            achievement_id: The ID of the achievement to unlock
            
        Returns:
            tuple: (was_newly_unlocked, gold_reward)
        """
        from .achievement import Achievement
        from datetime import datetime
        
        # Check if already unlocked
        if achievement_id in self.achievements:
            return False, 0
        
        # Get achievement data
        achievement = Achievement.get_achievement(achievement_id)
        if not achievement:
            return False, 0
        
        # Unlock achievement
        self.achievements[achievement_id] = datetime.now().isoformat()
        
        # Award gold (achievement is a dict)
        reward = achievement['reward']
        self.gold += reward
        
        return True, reward
    
    def check_achievements(self) -> list[dict]:
        """
        Check all achievements and unlock any that have been completed.
        
        Returns:
            list: List of newly unlocked achievements with their data
        """
        from .achievement import Achievement
        
        newly_unlocked = []
        all_achievements = Achievement.get_all()
        
        # Create a combined stats dict that includes gold for wealth achievements
        stats_with_gold = self.stats.copy()
        stats_with_gold['gold'] = self.gold
        
        for achievement in all_achievements:
            # Skip already unlocked (achievement is a dict)
            achievement_id = achievement['id']
            if achievement_id in self.achievements:
                continue
            
            # Check if requirements are met
            progress = Achievement.check_progress(achievement, stats_with_gold)
            if progress >= 1.0:  # Achievement completed
                was_unlocked, reward = self.unlock_achievement(achievement_id)
                if was_unlocked:
                    newly_unlocked.append({
                        "id": achievement_id,
                        "name": achievement['name'],
                        "description": achievement['description'],
                        "emoji": achievement['emoji'],
                        "reward": reward
                    })
        
        return newly_unlocked
    
    def to_dict(self) -> dict:
        """
        Convert player to dictionary for JSON serialization.
        
        Returns:
            dict: Player data as dictionary
        """
        return {
            "session_id": self.session_id,
            "name": self.name,
            "health": self.health,
            "max_health": self.max_health,
            "gold": self.gold,
            "attack_power": self.attack_power,
            "defense": self.defense,
            "speed": self.speed,
            "floor": self.floor,
            "room_id": self.room_id,
            "visited_rooms": list(self.visited_rooms),
            "allies": [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in self.allies],
            "inventory": [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.inventory],
            "experience": self.experience,
            "level": self.level,
            "attack_element": self.attack_element,
            "defense_element": self.defense_element,
            "equipped_weapon": self.equipped_weapon.to_dict() if self.equipped_weapon else None,
            "equipped_armor": self.equipped_armor.to_dict() if self.equipped_armor else None,
            "equipped_accessory": self.equipped_accessory.to_dict() if self.equipped_accessory else None,
            "in_battle": self.in_battle,
            "current_enemy": self.current_enemy,
            "current_ally": self.current_ally,
            "ally_used": self.ally_used,
            "battle_room": self.battle_room,
            "temp_attack_boost": self.temp_attack_boost,
            "temp_defense_boost": self.temp_defense_boost,
            "room_positions": self.room_positions,
            "room_info": self.room_info,
            "ailments": [ailment.to_dict() for ailment in self.ailments],
            "achievements": self.achievements,
            "stats": self.stats
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Player':
        """
        Create player from dictionary data.
        
        Args:
            data (dict): Player data dictionary
            
        Returns:
            Player: Player object created from data
        """
        from .ally import Ally  # Import here to avoid circular imports
        from .item import Item  # Import here to avoid circular imports
        from .gear import Gear  # Import here to avoid circular imports
        
        player = cls(session_id=data["session_id"], name=data["name"])
        player.health = data["health"]
        player.max_health = data["max_health"]
        player.gold = data["gold"]
        player.attack_power = data["attack_power"]
        player.defense = data["defense"]
        player.speed = data.get("speed", 10)  # Default to 10 for backward compatibility
        
        # Handle dual element system with backward compatibility
        if "attack_element" in data and "defense_element" in data:
            # New dual element system
            player.attack_element = data["attack_element"]
            player.defense_element = data["defense_element"]
        elif "element" in data:
            # Old single element system - convert to dual
            old_element = data["element"]
            player.attack_element = old_element
            player.defense_element = old_element
        else:
            # No element data - default to intern
            player.attack_element = "intern"
            player.defense_element = "intern"
        
        player.floor = data["floor"]
        player.room_id = data["room_id"]
        player.visited_rooms = set(data["visited_rooms"])
        player.allies = [Ally.from_dict(ally_data) for ally_data in data["allies"]]
        
        # Load inventory - handle both Item and Gear objects
        player.inventory = []
        for item_data in data.get("inventory", []):
            if "gear_type" in item_data:  # This is a Gear object
                player.inventory.append(Gear.from_dict(item_data))
            else:  # This is an Item object
                player.inventory.append(Item.from_dict(item_data))
        
        # Load equipped gear (with defaults for backward compatibility)
        player.equipped_weapon = Gear.from_dict(data["equipped_weapon"]) if data.get("equipped_weapon") else None
        player.equipped_armor = Gear.from_dict(data["equipped_armor"]) if data.get("equipped_armor") else None
        player.equipped_accessory = Gear.from_dict(data["equipped_accessory"]) if data.get("equipped_accessory") else None
        
        # Experience system (with defaults for backward compatibility)
        player.experience = data.get("experience", 0)
        player.level = data.get("level", 1)
        
        # Battle state (with defaults for backward compatibility)
        player.in_battle = data.get("in_battle", False)
        player.current_enemy = data.get("current_enemy", None)
        player.current_ally = data.get("current_ally", None)
        player.ally_used = data.get("ally_used", False)
        player.battle_room = data.get("battle_room", None)
        player.temp_attack_boost = data.get("temp_attack_boost", 0)
        player.temp_defense_boost = data.get("temp_defense_boost", 0)
        
        # Minimap data (with defaults for backward compatibility)
        player.room_positions = data.get("room_positions", {})
        player.room_info = data.get("room_info", {})
        
        # Ailments (with defaults for backward compatibility)
        from .ailment import Ailment
        player.ailments = [Ailment.from_dict(ailment_data) for ailment_data in data.get("ailments", [])]
        
        # Achievements and stats (with defaults for backward compatibility)
        player.achievements = data.get("achievements", {})
        player.stats = data.get("stats", {
            "enemies_defeated": 0,
            "rooms_visited": 0,
            "items_purchased": 0,
            "casino_winnings": 0,
            "allies_recruited": 0,
            "critical_hits_this_battle": 0,
            "consecutive_crits": 0,
            "max_consecutive_crits": 0,
            "damage_taken_this_battle": 0,
            "highest_floor_reached": 0,
            "max_damage_dealt": 0,
            "fully_equipped": 0,
            "perfect_timing_hits": 0,
            "consecutive_perfect_hits": 0,
            "max_consecutive_perfect_hits": 0,
            "items_used": 0,
            "all_legendary_equipped": 0,
            "all_allies_recruited": 0
        })
        
        return player