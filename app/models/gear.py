"""
Gear class for equipment system (weapons, armor, accessories).
"""

from typing import Optional, List
import uuid
import random


class Gear:
    """
    Represents equipable gear (weapon, armor, or accessory).
    """
    
    def __init__(
        self,
        gear_type: str,  # "weapon", "armor", "accessory"
        name: str,
        description: str,
        floor: int = 1,
        element: Optional[str] = None,
        attack_bonus: int = 0,
        defense_bonus: int = 0,
        speed_bonus: int = 0,
        ailment_type: Optional[str] = None,
        ailment_chance: float = 0.0,
        ailment_severity: int = 0,
        rarity: str = "common",
        gear_id: Optional[str] = None
    ):
        """
        Initialize gear.
        
        Args:
            gear_type: Type of gear ("weapon", "armor", "accessory")
            name: Display name
            description: Item description
            floor: Floor level (determines stat scaling)
            element: Element alignment (for weapons/armor)
            attack_bonus: Attack stat bonus
            defense_bonus: Defense stat bonus
            speed_bonus: Speed stat modifier
            ailment_type: Type of ailment (for weapons)
            ailment_chance: Chance to inflict ailment (0.0-1.0)
            ailment_severity: Ailment severity
            rarity: Item rarity
            gear_id: Unique identifier
        """
        self.gear_id = gear_id or str(uuid.uuid4())
        self.gear_type = gear_type
        self.name = name
        self.description = description
        self.floor = floor
        self.element = element
        self.attack_bonus = attack_bonus
        self.defense_bonus = defense_bonus
        self.speed_bonus = speed_bonus
        self.ailment_type = ailment_type
        self.ailment_chance = ailment_chance
        self.ailment_severity = ailment_severity
        self.rarity = rarity
    
    def get_gear_info(self) -> dict:
        """Get gear information for display."""
        info = {
            "gear_id": self.gear_id,
            "gear_type": self.gear_type,
            "name": self.name,
            "description": self.description,
            "floor": self.floor,
            "element": self.element,
            "attack_bonus": self.attack_bonus,
            "defense_bonus": self.defense_bonus,
            "speed_bonus": self.speed_bonus,
            "rarity": self.rarity
        }
        
        if self.ailment_type:
            info["ailment_type"] = self.ailment_type
            info["ailment_chance"] = self.ailment_chance
            info["ailment_severity"] = self.ailment_severity
        
        return info
    
    def to_dict(self) -> dict:
        """Convert gear to dictionary for JSON serialization."""
        return {
            "gear_id": self.gear_id,
            "gear_type": self.gear_type,
            "name": self.name,
            "description": self.description,
            "floor": self.floor,
            "element": self.element,
            "attack_bonus": self.attack_bonus,
            "defense_bonus": self.defense_bonus,
            "speed_bonus": self.speed_bonus,
            "ailment_type": self.ailment_type,
            "ailment_chance": self.ailment_chance,
            "ailment_severity": self.ailment_severity,
            "rarity": self.rarity
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Gear':
        """Create gear from dictionary data."""
        return cls(
            gear_type=data["gear_type"],
            name=data["name"],
            description=data["description"],
            floor=data.get("floor", 1),
            element=data.get("element"),
            attack_bonus=data.get("attack_bonus", 0),
            defense_bonus=data.get("defense_bonus", 0),
            speed_bonus=data.get("speed_bonus", 0),
            ailment_type=data.get("ailment_type"),
            ailment_chance=data.get("ailment_chance", 0.0),
            ailment_severity=data.get("ailment_severity", 0),
            rarity=data.get("rarity", "common"),
            gear_id=data.get("gear_id")
        )
    
    def get_item_info(self) -> dict:
        """Get gear info for frontend display (compatible with Item interface)."""
        return {
            "gear_id": self.gear_id,
            "item_id": self.gear_id,  # For compatibility with Item interface
            "name": self.name,
            "description": self.description,
            "gear_type": self.gear_type,
            "element": self.element,
            "attack_bonus": self.attack_bonus,
            "defense_bonus": self.defense_bonus,
            "speed_bonus": self.speed_bonus,
            "ailment": self.ailment_type,
            "ailment_chance": self.ailment_chance,
            "ailment_severity": self.ailment_severity,
            "weight": self.weight if hasattr(self, 'weight') else None,
            "rarity": self.rarity,
            "floor": self.floor
        }
    
    @classmethod
    def generate_weapon(cls, floor: int = 1) -> 'Gear':
        """Generate a random weapon scaled to floor."""
        elements = ["accounting", "it", "marketing", "hr", "sales", "legal", "management", "intern"]
        element = random.choice(elements)
        
        # Scale stats with floor
        base_attack = 5 + (floor * 2)
        attack_variance = random.randint(-2, 3)
        attack_bonus = max(1, base_attack + attack_variance)
        
        # Determine rarity based on floor
        rarity_roll = random.random()
        if floor >= 10 and rarity_roll < 0.15:
            rarity = "legendary"
            attack_bonus = int(attack_bonus * 1.5)
        elif floor >= 5 and rarity_roll < 0.3:
            rarity = "rare"
            attack_bonus = int(attack_bonus * 1.25)
        elif rarity_roll < 0.5:
            rarity = "uncommon"
            attack_bonus = int(attack_bonus * 1.1)
        else:
            rarity = "common"
        
        # Chance for ailment (increases with floor)
        ailment_roll = random.random()
        ailment_type = None
        ailment_chance = 0.0
        ailment_severity = 0
        
        if floor >= 3 and ailment_roll < (0.2 + floor * 0.03):
            ailment_types = ["poison", "paralysis", "weakened", "blinded"]
            ailment_type = random.choice(ailment_types)
            # Scale chance and severity with floor
            ailment_chance = min(0.5, 0.15 + (floor * 0.02))
            ailment_severity = min(5, 1 + (floor // 3))
        
        # Generate name based on element and rarity
        element_names = {
            "accounting": "Calculator", "it": "Server Rack", "marketing": "Billboard",
            "hr": "Handbook", "sales": "Briefcase", "legal": "Gavel",
            "management": "Corner Office Key", "intern": "Coffee Mug"
        }
        rarity_prefixes = {
            "common": "", "uncommon": "Enhanced", "rare": "Superior", "legendary": "Legendary"
        }
        
        base_name = element_names.get(element, "Weapon")
        prefix = rarity_prefixes.get(rarity, "")
        name = f"{prefix} {base_name}".strip() if prefix else base_name
        
        description = f"A {rarity} weapon imbued with {element} energy. +{attack_bonus} ATK."
        if ailment_type:
            description += f" {int(ailment_chance*100)}% chance to inflict {ailment_type} (Sev {ailment_severity})."
        
        return cls(
            gear_type="weapon",
            name=name,
            description=description,
            floor=floor,
            element=element,
            attack_bonus=attack_bonus,
            ailment_type=ailment_type,
            ailment_chance=ailment_chance,
            ailment_severity=ailment_severity,
            rarity=rarity
        )
    
    @classmethod
    def generate_armor(cls, floor: int = 1) -> 'Gear':
        """Generate random armor scaled to floor."""
        elements = ["accounting", "it", "marketing", "hr", "sales", "legal", "management", "intern"]
        element = random.choice(elements)
        
        # Scale stats with floor
        base_defense = 3 + (floor * 2)
        defense_variance = random.randint(-1, 2)
        defense_bonus = max(1, base_defense + defense_variance)
        
        # Armor affects speed (heavier = more defense, less speed)
        # Light armor: +speed, moderate defense
        # Heavy armor: -speed, high defense
        armor_weight = random.choice(["light", "medium", "heavy"])
        
        if armor_weight == "light":
            speed_bonus = random.randint(1, 2 + floor // 5)
            defense_bonus = int(defense_bonus * 0.8)
        elif armor_weight == "heavy":
            speed_bonus = -random.randint(1, 2 + floor // 8)
            defense_bonus = int(defense_bonus * 1.3)
        else:  # medium
            speed_bonus = 0
        
        # Determine rarity
        rarity_roll = random.random()
        if floor >= 10 and rarity_roll < 0.15:
            rarity = "legendary"
            defense_bonus = int(defense_bonus * 1.5)
        elif floor >= 5 and rarity_roll < 0.3:
            rarity = "rare"
            defense_bonus = int(defense_bonus * 1.25)
        elif rarity_roll < 0.5:
            rarity = "uncommon"
            defense_bonus = int(defense_bonus * 1.1)
        else:
            rarity = "common"
        
        # Generate name
        element_names = {
            "accounting": "Ledger", "it": "Firewall", "marketing": "Brand",
            "hr": "Policy", "sales": "Contract", "legal": "Statute",
            "management": "Executive", "intern": "Trainee"
        }
        weight_names = {"light": "Light", "medium": "", "heavy": "Heavy"}
        rarity_prefixes = {
            "common": "", "uncommon": "Enhanced", "rare": "Superior", "legendary": "Legendary"
        }
        
        base_name = f"{weight_names[armor_weight]} {element_names.get(element, 'Armor')}".strip()
        prefix = rarity_prefixes.get(rarity, "")
        name = f"{prefix} {base_name} Armor".strip() if prefix else f"{base_name} Armor"
        
        speed_text = f" +{speed_bonus} SPD" if speed_bonus > 0 else f" {speed_bonus} SPD" if speed_bonus < 0 else ""
        description = f"A {rarity} {armor_weight} armor with {element} protection. +{defense_bonus} DEF{speed_text}."
        
        return cls(
            gear_type="armor",
            name=name,
            description=description,
            floor=floor,
            element=element,
            defense_bonus=defense_bonus,
            speed_bonus=speed_bonus,
            rarity=rarity
        )
    
    @classmethod
    def generate_accessory(cls, floor: int = 1) -> 'Gear':
        """Generate random accessory with secondary effects."""
        # Accessories provide balanced or specialized bonuses
        accessory_types = [
            "balanced",  # Small bonuses to all stats
            "offensive", # Attack and speed
            "defensive", # Defense and health
            "swift"      # Speed focus
        ]
        
        acc_type = random.choice(accessory_types)
        
        # Scale with floor
        stat_scale = 1 + (floor // 2)
        
        if acc_type == "balanced":
            attack_bonus = stat_scale
            defense_bonus = stat_scale
            speed_bonus = stat_scale
            name_base = "Office Badge"
        elif acc_type == "offensive":
            attack_bonus = stat_scale * 2
            defense_bonus = 0
            speed_bonus = stat_scale
            name_base = "Performance Award"
        elif acc_type == "defensive":
            attack_bonus = 0
            defense_bonus = stat_scale * 2
            speed_bonus = 0
            name_base = "Safety Certificate"
        else:  # swift
            attack_bonus = stat_scale
            defense_bonus = 0
            speed_bonus = stat_scale * 2
            name_base = "Express Pass"
        
        # Determine rarity
        rarity_roll = random.random()
        if floor >= 8 and rarity_roll < 0.15:
            rarity = "legendary"
            attack_bonus = int(attack_bonus * 1.5)
            defense_bonus = int(defense_bonus * 1.5)
            speed_bonus = int(speed_bonus * 1.5)
        elif floor >= 4 and rarity_roll < 0.3:
            rarity = "rare"
            attack_bonus = int(attack_bonus * 1.3)
            defense_bonus = int(defense_bonus * 1.3)
            speed_bonus = int(speed_bonus * 1.3)
        elif rarity_roll < 0.5:
            rarity = "uncommon"
            attack_bonus = int(attack_bonus * 1.15)
            defense_bonus = int(defense_bonus * 1.15)
            speed_bonus = int(speed_bonus * 1.15)
        else:
            rarity = "common"
        
        rarity_prefixes = {
            "common": "", "uncommon": "Quality", "rare": "Premium", "legendary": "Legendary"
        }
        
        prefix = rarity_prefixes.get(rarity, "")
        name = f"{prefix} {name_base}".strip() if prefix else name_base
        
        stat_text = []
        if attack_bonus > 0:
            stat_text.append(f"+{attack_bonus} ATK")
        if defense_bonus > 0:
            stat_text.append(f"+{defense_bonus} DEF")
        if speed_bonus > 0:
            stat_text.append(f"+{speed_bonus} SPD")
        
        description = f"A {rarity} accessory. {', '.join(stat_text)}."
        
        return cls(
            gear_type="accessory",
            name=name,
            description=description,
            floor=floor,
            attack_bonus=attack_bonus,
            defense_bonus=defense_bonus,
            speed_bonus=speed_bonus,
            rarity=rarity
        )
    
    @classmethod
    def generate_random_gear(cls, floor: int = 1) -> 'Gear':
        """Generate random gear piece of any type."""
        gear_type = random.choice(["weapon", "armor", "accessory"])
        
        if gear_type == "weapon":
            return cls.generate_weapon(floor)
        elif gear_type == "armor":
            return cls.generate_armor(floor)
        else:
            return cls.generate_accessory(floor)
