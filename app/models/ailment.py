"""
Ailment system for status effects in combat.
"""

import random
from typing import Dict, Any


class Ailment:
    """
    Represents a status ailment (poison, paralysis, etc.) that affects an entity.
    """
    
    AILMENT_TYPES = {
        "poison": {
            "name": "Poison",
            "emoji": "🧪",
            "description": "Takes damage over time"
        },
        "paralysis": {
            "name": "Paralysis", 
            "emoji": "⚡",
            "description": "May skip turns"
        },
        "weakened": {
            "name": "Weakened",
            "emoji": "💔",
            "description": "Attack power reduced",
            "stat_emoji": "⚠️"
        },
        "irradiated": {
            "name": "Irradiated",
            "emoji": "☢️",
            "description": "Defense reduced",
            "stat_emoji": "☢️"
        },
        "shackled": {
            "name": "Shackled",
            "emoji": "⛓️",
            "description": "Speed reduced",
            "stat_emoji": "⛓️"
        },
        "infatuated": {
            "name": "Infatuated",
            "emoji": "💖",
            "description": "Cannot use allies (player only)",
            "player_only": True
        },
        "blinded": {
            "name": "Blinded",
            "emoji": "🙈",
            "description": "May miss attacks"
        }
    }
    
    def __init__(self, ailment_type: str, severity: int, duration: int):
        """
        Initialize an ailment.
        
        Args:
            ailment_type (str): Type of ailment ('poison' or 'paralysis')
            severity (int): Severity level (0-5)
            duration (int): Number of turns the ailment lasts
        """
        self.ailment_type = ailment_type
        self.severity = min(5, max(0, severity))  # Clamp between 0 and 5
        self.duration = duration
        self.turns_remaining = duration
        
    def get_emoji(self) -> str:
        """Get the emoji representation of this ailment."""
        return self.AILMENT_TYPES.get(self.ailment_type, {}).get("emoji", "❓")
    
    def get_name(self) -> str:
        """Get the name of this ailment."""
        return self.AILMENT_TYPES.get(self.ailment_type, {}).get("name", "Unknown")
    
    def apply_poison_damage(self, base_health: int) -> int:
        """
        Calculate poison damage based on severity.
        
        Args:
            base_health (int): Base health of the entity
            
        Returns:
            int: Damage to apply
        """
        if self.ailment_type != "poison":
            return 0
        
        # Damage scales with severity: 2-5 base damage per severity level
        min_damage = 2 + self.severity
        max_damage = 5 + (self.severity * 2)
        damage = random.randint(min_damage, max_damage)
        
        return damage
    
    def check_paralysis(self) -> bool:
        """
        Check if paralysis causes turn skip.
        
        Returns:
            bool: True if turn should be skipped
        """
        if self.ailment_type != "paralysis":
            return False
        
        # Paralysis chance: 15% + (severity * 10%), max 65% at severity 5
        paralysis_chance = 15 + (self.severity * 10)
        paralysis_chance = min(65, paralysis_chance)  # Cap at 65%
        
        roll = random.randint(1, 100)
        return roll <= paralysis_chance
    
    def get_stat_reduction_percentage(self, stat_type: str) -> float:
        """
        Get the stat reduction percentage for weakened, irradiated, or shackled ailments.
        
        Args:
            stat_type (str): 'weakened' for attack, 'irradiated' for defense, 'shackled' for speed
            
        Returns:
            float: Reduction multiplier (e.g., 0.8 for 20% reduction)
        """
        if self.ailment_type != stat_type:
            return 1.0  # No reduction
        
        # Reduction: 10% + (severity * 8%), max 50% at severity 5
        reduction_percent = 10 + (self.severity * 8)
        reduction_percent = min(50, reduction_percent)
        
        return 1.0 - (reduction_percent / 100.0)
    
    def check_blind_miss(self) -> bool:
        """
        Check if blinded ailment causes attack to miss.
        
        Returns:
            bool: True if attack should miss
        """
        if self.ailment_type != "blinded":
            return False
        
        # Miss chance: 10% + (severity * 8%), max 50% at severity 5
        miss_chance = 10 + (self.severity * 8)
        miss_chance = min(50, miss_chance)
        
        roll = random.randint(1, 100)
        return roll <= miss_chance
    
    def prevents_ally_use(self) -> bool:
        """
        Check if this ailment prevents ally usage (infatuated).
        
        Returns:
            bool: True if ally usage is prevented
        """
        return self.ailment_type == "infatuated"
    
    def get_stat_emoji(self) -> str:
        """Get the stat emoji for stat-modifying ailments."""
        return self.AILMENT_TYPES.get(self.ailment_type, {}).get("stat_emoji", "")
    
    def is_player_only(self) -> bool:
        """Check if this ailment is player-only."""
        return self.AILMENT_TYPES.get(self.ailment_type, {}).get("player_only", False)
    
    def tick_duration(self) -> bool:
        """
        Decrease duration by 1 turn.
        
        Returns:
            bool: True if ailment is still active, False if expired
        """
        self.turns_remaining -= 1
        return self.turns_remaining > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ailment to dictionary."""
        return {
            "type": self.ailment_type,
            "severity": self.severity,
            "duration": self.duration,
            "turns_remaining": self.turns_remaining,
            "emoji": self.get_emoji(),
            "name": self.get_name()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Ailment':
        """Create ailment from dictionary."""
        ailment = cls(
            ailment_type=data.get("type", "poison"),
            severity=data.get("severity", 1),
            duration=data.get("duration", 3)
        )
        ailment.turns_remaining = data.get("turns_remaining", ailment.duration)
        return ailment


def calculate_ailment_severity(floor: int) -> int:
    """
    Calculate ailment severity based on floor level.
    Severity increases every 5 floors.
    
    Args:
        floor (int): Current floor number
        
    Returns:
        int: Severity level (0-5)
    """
    # Base severity increases every 5 floors
    base_severity = floor // 5
    
    # Add some randomness within the range
    if floor <= 5:
        severity = random.randint(0, 1)
    elif floor <= 10:
        severity = random.randint(1, 2)
    elif floor <= 15:
        severity = random.randint(2, 3)
    elif floor <= 20:
        severity = random.randint(3, 4)
    else:
        severity = random.randint(4, 5)
    
    return min(5, severity)


def calculate_ailment_duration(severity: int) -> int:
    """
    Calculate ailment duration based on severity.
    
    Args:
        severity (int): Ailment severity
        
    Returns:
        int: Duration in turns
    """
    # Duration: 2-4 turns for low severity, up to 5-7 turns for high severity
    base_duration = 2 + severity
    variation = random.randint(0, 2)
    return base_duration + variation


def should_enemy_have_ailment(enemy_name: str, enemy_description: str) -> tuple[bool, str]:
    """
    Determine if an enemy should have an ailment ability based on name and description.
    Maximum 35% of enemies should have ailments.
    
    Args:
        enemy_name (str): Name of the enemy
        enemy_description (str): Description of the enemy
        
    Returns:
        tuple[bool, str]: (has_ailment, ailment_type)
    """
    # First, random check - only 35% chance maximum
    if random.randint(1, 100) > 35:
        return False, ""
    
    # Combine name and description for analysis
    text = (enemy_name + " " + enemy_description).lower()
    
    # Keywords for poison
    poison_keywords = [
        "poison", "venom", "toxic", "acid", "bile", "slime", "ooze",
        "spore", "fungus", "mushroom", "rot", "decay", "putrid",
        "disease", "plague", "miasma", "noxious", "corrosive"
    ]
    
    # Keywords for paralysis
    paralysis_keywords = [
        "paralyze", "paralysis", "electric", "lightning", "shock",
        "stun", "freeze", "ice", "frost", "cold", "chill",
        "web", "spider", "entangle", "bind", "slow"
    ]
    
    # Keywords for weakened
    weakened_keywords = [
        "weak", "drain", "sap", "exhaust", "tire", "fatigue",
        "curse", "hex", "debilitate", "enfeeble"
    ]
    
    # Keywords for irradiated
    irradiated_keywords = [
        "radiat", "nuclear", "gamma", "melt", "corrode", "erode",
        "decay", "decompose", "break", "shatter"
    ]
    
    # Keywords for shackled
    shackled_keywords = [
        "shackle", "chain", "bind", "restrict", "impede", "hinder",
        "slow", "heavy", "burden", "weight", "anchor"
    ]
    
    # Keywords for blinded
    blinded_keywords = [
        "blind", "dark", "shadow", "obscure", "fog", "mist",
        "smoke", "ash", "dust", "flash", "dazzle", "glare"
    ]
    
    # Note: infatuated is player-only, so not included here
    
    # Check for keywords
    scores = {
        "poison": sum(1 for keyword in poison_keywords if keyword in text),
        "paralysis": sum(1 for keyword in paralysis_keywords if keyword in text),
        "weakened": sum(1 for keyword in weakened_keywords if keyword in text),
        "irradiated": sum(1 for keyword in irradiated_keywords if keyword in text),
        "shackled": sum(1 for keyword in shackled_keywords if keyword in text),
        "blinded": sum(1 for keyword in blinded_keywords if keyword in text)
    }
    
    # Find highest scoring ailment
    max_score = max(scores.values())
    
    if max_score > 0:
        # Get all ailments with max score
        top_ailments = [ailment for ailment, score in scores.items() if score == max_score]
        # Randomly pick one if there's a tie
        return True, random.choice(top_ailments)
    
    return False, ""
