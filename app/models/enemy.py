"""
Enemy class for the dungeon crawler game.
"""

import random
from typing import Optional


class Enemy:
    """
    Represents an enemy in the dungeon crawler game.
    """
    
    def __init__(self, name: str = "", description: str = "", floor: int = 1):
        self.name = name or "Unknown Creature"
        self.description = description or "A mysterious creature lurks in the shadows."
        self.floor = floor
        
        # Scale stats based on floor level - slightly increased difficulty
        base_health = 22 + (floor * 7)  # Increased from 20 + floor * 6
        base_attack = 6 + (floor * 1.8)  # Increased from 5 + floor * 1.5
        base_defense = 1 + (floor * 0.6)  # Increased from 1 + floor * 0.5
        base_speed = 8 + (floor * 0.8)  # Speed scales with floor
        base_gold = 15 + (floor * 8)  # Gold reward unchanged
        base_exp = 25 + (floor * 10)  # Experience reward unchanged
        
        # Add some randomness to stats
        self.max_health = int(base_health + random.randint(-3, 6))
        self.health = self.max_health
        self.attack_power = int(base_attack + random.randint(-1, 4))
        self.defense = int(base_defense + random.randint(0, 2))
        self.speed = int(base_speed + random.randint(-2, 3))
        self.gold_reward = base_gold + random.randint(0, floor * 2)
        self.exp_reward = base_exp + random.randint(0, floor * 5)
        
        # Ensure minimum values
        self.max_health = max(15, self.max_health)
        self.health = self.max_health
        self.attack_power = max(3, self.attack_power)
        self.defense = max(0, self.defense)
        self.speed = max(5, self.speed)
        self.gold_reward = max(10, self.gold_reward)
        self.exp_reward = max(20, self.exp_reward)
        
        # Status effects
        self.skip_next_turn = False  # For skipper allies
        
        # Ailments - enemies can inflict multiple types
        self.ailments = []  # List of active ailments on this enemy
        self.ailment_inflict_types = []  # List of ailment types this enemy can inflict
        self.ailment_inflict_chance = 0  # Chance to inflict ailment (0.0 to 1.0 decimal, e.g. 0.5 = 50%)
        self.ailment_inflict_severity = None  # Optional: Override severity (0-5), None = use floor-based calculation
    
    def take_damage(self, damage: int) -> bool:
        """
        Apply damage to the enemy.
        
        Args:
            damage (int): Amount of damage to apply
            
        Returns:
            bool: True if enemy is still alive, False if dead
        """
        actual_damage = max(1, damage - self.defense)  # Minimum 1 damage
        self.health = max(0, self.health - actual_damage)
        return self.health > 0
    
    def attack(self) -> int:
        """
        Perform an attack and return damage dealt.
        
        Returns:
            int: Damage dealt by the enemy
        """
        # Add some randomness to attacks
        base_damage = self.attack_power
        variation = random.randint(-2, 3)
        return max(1, base_damage + variation)
    
    def is_alive(self) -> bool:
        """
        Check if the enemy is still alive.
        
        Returns:
            bool: True if alive, False if dead
        """
        return self.health > 0
    
    def add_ailment(self, ailment):
        """
        Add an ailment to the enemy.
        
        Args:
            ailment: Ailment object to add
        """
        # Check if enemy already has this type of ailment
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
    
    def set_ailment_ability(self, ailment_type: str, floor: int):
        """
        Give this enemy the ability to inflict a specific ailment.
        
        Args:
            ailment_type (str): Type of ailment (e.g., 'poison', 'paralysis', etc.)
            floor (int): Current floor for scaling
        """
        from .ailment import calculate_ailment_severity
        
        # Add to list if not already present
        if ailment_type not in self.ailment_inflict_types:
            self.ailment_inflict_types.append(ailment_type)
        
        # Base 25% chance + 2% per floor, capped at 50%
        # Store as decimal (0.0 to 1.0) for consistency with frontend
        percentage = min(50, 25 + (floor * 2))
        self.ailment_inflict_chance = percentage / 100.0
    
    def get_gold_reward(self) -> int:
        """
        Get the gold reward for defeating this enemy.
        
        Returns:
            int: Gold reward amount
        """
        return self.gold_reward
    
    def to_dict(self) -> dict:
        """
        Convert enemy to dictionary for JSON serialization.
        
        Returns:
            dict: Enemy data as dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "floor": self.floor,
            "health": self.health,
            "max_health": self.max_health,
            "attack_power": self.attack_power,
            "defense": self.defense,
            "speed": self.speed,
            "gold_reward": self.gold_reward,
            "exp_reward": self.exp_reward,
            "skip_next_turn": self.skip_next_turn,
            "ailments": [ailment.to_dict() for ailment in self.ailments],
            "ailment_inflict_types": self.ailment_inflict_types,
            "ailment_inflict_chance": self.ailment_inflict_chance,
            "ailment_inflict_severity": self.ailment_inflict_severity
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Enemy':
        """
        Create enemy from dictionary data.
        
        Args:
            data (dict): Enemy data dictionary
            
        Returns:
            Enemy: Enemy object created from data
        """
        enemy = cls(
            name=data["name"],
            description=data["description"],
            floor=data["floor"]
        )
        enemy.health = data["health"]
        enemy.max_health = data["max_health"]
        enemy.attack_power = data["attack_power"]
        enemy.defense = data["defense"]
        enemy.speed = data.get("speed", 8 + (data["floor"] * 0.8))  # Backward compatibility
        enemy.gold_reward = data["gold_reward"]
        enemy.exp_reward = data.get("exp_reward", 25 + (data["floor"] * 10))  # Backward compatibility
        enemy.skip_next_turn = data.get("skip_next_turn", False)  # Restore skip status
        
        # Ailments (with defaults for backward compatibility)
        from .ailment import Ailment
        enemy.ailments = [Ailment.from_dict(ailment_data) for ailment_data in data.get("ailments", [])]
        
        # Support both old single type and new multiple types
        if "ailment_inflict_types" in data:
            enemy.ailment_inflict_types = data.get("ailment_inflict_types", [])
        elif "ailment_inflict_type" in data and data["ailment_inflict_type"]:
            # Backward compatibility: convert single type to list
            enemy.ailment_inflict_types = [data["ailment_inflict_type"]]
        else:
            enemy.ailment_inflict_types = []
        
        enemy.ailment_inflict_chance = data.get("ailment_inflict_chance", 0)
        enemy.ailment_inflict_severity = data.get("ailment_inflict_severity", None)
        
        return enemy
    
    @classmethod
    def create_random_enemy(cls, floor: int = 1, name: str = "", description: str = "") -> 'Enemy':
        """
        Create a random enemy for the given floor.
        
        Args:
            floor (int): Floor level for scaling difficulty
            name (str): Optional custom name
            description (str): Optional custom description
            
        Returns:
            Enemy: Newly created enemy
        """
        # If no name/description provided, these will be generated by LLM in generation.py
        return cls(name=name, description=description, floor=floor)
    
    def get_combat_info(self) -> dict:
        """
        Get enemy information suitable for combat display.
        
        Returns:
            dict: Combat-relevant enemy information
        """
        return {
            "name": self.name,
            "description": self.description,
            "health": self.health,
            "max_health": self.max_health,
            "attack_power": self.attack_power,
            "defense": self.defense
        }