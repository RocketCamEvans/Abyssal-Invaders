"""
Ally class for the dungeon crawler game.
"""

import random
from typing import Optional


# Predefined allies with their types and effects
PREDEFINED_ALLIES = [
    # Healers
    {"name": "Freaky Fred", "type": "healer", "value": 18, "description": "Freaky Fred does a rather entrancing dance. The wicked moves that he brings forth gives you immense spirit!", "sprite": "player_dancer_skirt_entertainer_singer.png", "max_uses": 3},
    {"name": "Supreme Astrologer Kassidy", "type": "healer", "value": 22, "description": "Kassidy has bestowed a positive horoscope upon you, granting you a great boost in strength!", "sprite": "player_wizard_arcane_spectral_mage_magic_wand_astrologist.png", "max_uses": 2},
    
    # Attackers
    {"name": "Chugg the Conquerer", "type": "attacker", "value": 40, "description": "Chugg teleports the enemy onto an island, where the fish queen washes a tsunami over them!", "sprite": "player_pirate_sea_beard_hat_man.png", "max_uses": 1},
    {"name": "Vanguard Clayton", "type": "attacker", "value": 22, "description": "Clayton rides in on his great dane, slashing at the enemy!", "sprite": "player_knight_dog_sword_shield_armor_warrior_great.png", "max_uses": 3},
    {"name": "Moss Lurker", "type": "attacker", "value": 15, "description": "Originally an enemy, the Moss Lurker has seen the error of its ways and now aids you by releasing poisonous spores upon the enemies!", "sprite": "monster_grass_moss_creeper.png", "max_uses": 4},
    
    # Skippers
    {"name": "Mad Jester Juju", "type": "skipper", "value": 0, "description": "Juju gaslights the enemy into believing they already took their turn!", "sprite": "player_jester_silly_mad_insane_crazy_clown_harlequin.png", "max_uses": 2},
    {"name": "Sebastian", "type": "skipper", "value": 0, "description": "NOBODY does Sebastian. The enemy agrees and decides to give up their turn.", "sprite": "player_casual_office_worker_normal.png", "max_uses": 1},
    {"name": "Bridge Troll Spencer", "type": "skipper", "value": 0, "description": "Spencer tells the enemy that they will cross that bridge when they get there. The enemy skips their turn.", "sprite": "player_troll_monster_goblin_orc_ogre_green_brute.png", "max_uses": 1}
]


class Ally:
    """
    Represents an ally that can help the player in combat.
    Allies persist between battles until used.
    """
    
    def __init__(self, name: str = "", ally_type: str = "attacker", value: int = 0, description: str = "", floor: int = 1, sprite: str = "", max_uses: int = None):
        self.name = name or "Mysterious Helper"
        self.ally_type = ally_type  # 'healer', 'attacker', or 'skipper'
        self.value = value  # Healing amount, damage amount, or 0 for skipper
        self.description = description or "A helpful coworker appears to aid you."
        self.floor = floor
        self.used = False
        self.sprite = sprite or "ally_warrior_human_male.png"  # Default sprite
        self.max_uses = max_uses if max_uses is not None else 3  # Default to 3 if not specified
        self.uses_remaining = self.max_uses  # Start with full uses
        
        # For backwards compatibility
        self.attack_power = value if ally_type == "attacker" else 0
    
    def use_attack(self) -> int:
        """
        Use the ally's attack (marks ally as used).
        DEPRECATED: Use use_ability() instead.
        
        Returns:
            int: Damage dealt by the ally
        """
        if self.used:
            return 0
        
        self.used = True
        # Add some randomness to ally attacks
        variation = random.randint(-2, 4)
        return max(5, self.attack_power + variation)
    
    def use_ability(self) -> dict:
        """
        Use the ally's ability (marks ally as used for this battle and decrements uses_remaining).
        
        Returns:
            dict: Result containing type, value, and message
        """
        if self.used:
            return {"type": "error", "value": 0, "message": "Ally already used this battle"}
        
        if self.uses_remaining <= 0:
            return {"type": "error", "value": 0, "message": "Ally has no uses remaining"}
        
        self.used = True
        self.uses_remaining -= 1
        
        # Create the "leaving work" message
        if self.uses_remaining > 0:
            leaving_message = f"{self.name} takes a break. ({self.uses_remaining} uses left)"
        else:
            leaving_message = f"{self.name} has put in their hours and is leaving work permanently."
        
        return {
            "type": self.ally_type,
            "value": self.value,
            "message": leaving_message,
            "description": self.description
        }
    
    def is_available(self) -> bool:
        """
        Check if the ally is still available for use.
        
        Returns:
            bool: True if ally hasn't been used in this battle and has uses remaining
        """
        return not self.used and self.uses_remaining > 0
    
    def to_dict(self) -> dict:
        """
        Convert ally to dictionary for JSON serialization.
        
        Returns:
            dict: Ally data as dictionary
        """
        return {
            "name": self.name,
            "type": self.ally_type,
            "value": self.value,
            "description": self.description,
            "floor": self.floor,
            "used": self.used,
            "sprite": self.sprite,
            "uses_remaining": self.uses_remaining,
            "max_uses": self.max_uses,
            # For backwards compatibility with old code
            "attack_power": self.value if self.ally_type == "attacker" else 0
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Ally':
        """
        Create ally from dictionary data.
        
        Args:
            data (dict): Ally data dictionary
            
        Returns:
            Ally: Ally object created from data
        """
        ally = cls(
            name=data.get("name", "Mysterious Helper"),
            ally_type=data.get("type", "attacker"),
            value=data.get("value", 0),
            description=data.get("description", "A helpful coworker."),
            floor=data.get("floor", 1),
            sprite=data.get("sprite", "ally_warrior_human_male.png"),
            max_uses=data.get("max_uses", 3)
        )
        ally.used = data.get("used", False)
        # Use stored uses_remaining, or default to max_uses if not found
        ally.uses_remaining = data.get("uses_remaining", ally.max_uses)
        return ally
    
    @classmethod
    def create_random_ally(cls, floor: int = 1, name: str = "", description: str = "") -> 'Ally':
        """
        Create a random ally from the predefined list.
        
        Args:
            floor (int): Floor level (not used for scaling anymore)
            name (str): Ignored - name comes from predefined list
            description (str): Ignored - description comes from predefined list
            
        Returns:
            Ally: Newly created ally
        """
        ally_template = random.choice(PREDEFINED_ALLIES)
        
        return cls(
            name=ally_template["name"],
            ally_type=ally_template["type"],
            value=ally_template["value"],
            description=ally_template["description"],
            floor=floor,
            sprite=ally_template.get("sprite", "ally_warrior_human_male.png"),
            max_uses=ally_template.get("max_uses", 3)
        )
    
    @classmethod
    def create_specific_ally(cls, name: str, floor: int = 1) -> Optional['Ally']:
        """
        Create a specific ally by name.
        
        Args:
            name (str): Name of the ally to create
            floor (int): Floor level
            
        Returns:
            Optional[Ally]: Ally if found, None otherwise
        """
        for ally_template in PREDEFINED_ALLIES:
            if ally_template["name"].lower() == name.lower():
                return cls(
                    name=ally_template["name"],
                    ally_type=ally_template["type"],
                    value=ally_template["value"],
                    description=ally_template["description"],
                    floor=floor,
                    sprite=ally_template.get("sprite", "ally_warrior_human_male.png"),
                    max_uses=ally_template.get("max_uses", 3)
                )
        return None
    
    def get_ally_info(self) -> dict:
        """
        Get ally information suitable for display.
        
        Returns:
            dict: Ally information
        """
        return {
            "name": self.name,
            "type": self.ally_type,
            "value": self.value,
            "description": self.description,
            "available": self.is_available(),
            "sprite": self.sprite
        }