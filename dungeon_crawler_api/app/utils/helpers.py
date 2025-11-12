"""
Common utility functions and helpers for the dungeon crawler game.
"""

import random
import string
import uuid
from typing import List, Dict, Any, Optional


def generate_session_id() -> str:
    """
    Generate a unique session ID.
    
    Returns:
        str: Unique session ID
    """
    return str(uuid.uuid4())


def generate_room_id(floor: int, base_name: str = "") -> str:
    """
    Generate a room ID based on floor and optional base name.
    
    Args:
        floor (int): Floor number
        base_name (str): Optional base name for the room
        
    Returns:
        str: Generated room ID
    """
    if base_name:
        # Clean the base name to make it URL-safe
        clean_name = "".join(c.lower() if c.isalnum() else "_" for c in base_name)
        return f"floor_{floor}_{clean_name}"
    else:
        # Generate random room ID
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return f"floor_{floor}_room_{random_suffix}"


def calculate_encounter_chance(floor: int, base_chance: float = 0.3) -> float:
    """
    Calculate encounter chance based on floor level.
    
    Args:
        floor (int): Current floor
        base_chance (float): Base encounter chance
        
    Returns:
        float: Calculated encounter chance (0.0 to 1.0)
    """
    # Increase encounter chance slightly with each floor
    floor_modifier = (floor - 1) * 0.05
    return min(0.8, base_chance + floor_modifier)  # Cap at 80%


def roll_dice(sides: int = 20) -> int:
    """
    Roll a dice with specified number of sides.
    
    Args:
        sides (int): Number of sides on the dice
        
    Returns:
        int: Random number between 1 and sides
    """
    return random.randint(1, sides)


def calculate_damage_with_variance(base_damage: int, variance_percent: float = 0.2) -> int:
    """
    Calculate damage with random variance.
    
    Args:
        base_damage (int): Base damage amount
        variance_percent (float): Percentage variance (0.0 to 1.0)
        
    Returns:
        int: Damage with variance applied (minimum 1)
    """
    variance = int(base_damage * variance_percent)
    damage = base_damage + random.randint(-variance, variance)
    return max(1, damage)


def format_player_stats(player) -> Dict[str, Any]:
    """
    Format player statistics for API responses.
    
    Args:
        player: Player object
        
    Returns:
        Dict[str, Any]: Formatted player statistics
    """
    return {
        "name": player.name,
        "health": f"{player.health}/{player.max_health}",
        "gold": player.gold,
        "attack_power": player.attack_power,
        "defense": player.defense,
        "floor": player.floor,
        "room_id": player.room_id,
        "allies_count": len(player.allies),
        "is_alive": player.is_alive()
    }


def format_combat_summary(player_damage: int, enemy_damage: int, 
                         player_health: int, enemy_health: int,
                         player_name: str = "Player", enemy_name: str = "Enemy") -> str:
    """
    Format a combat summary message.
    
    Args:
        player_damage (int): Damage dealt by player
        enemy_damage (int): Damage dealt by enemy
        player_health (int): Player's remaining health
        enemy_health (int): Enemy's remaining health
        player_name (str): Player's name
        enemy_name (str): Enemy's name
        
    Returns:
        str: Formatted combat summary
    """
    summary = f"{player_name} deals {player_damage} damage to {enemy_name}. "
    
    if enemy_health <= 0:
        summary += f"{enemy_name} is defeated!"
    else:
        summary += f"{enemy_name} has {enemy_health} health remaining. "
        summary += f"{enemy_name} attacks for {enemy_damage} damage. "
        
        if player_health <= 0:
            summary += f"{player_name} is defeated!"
        else:
            summary += f"{player_name} has {player_health} health remaining."
    
    return summary


def validate_direction(direction: str) -> Optional[str]:
    """
    Validate and normalize a movement direction.
    
    Args:
        direction (str): Direction string to validate
        
    Returns:
        Optional[str]: Normalized direction or None if invalid
    """
    direction_map = {
        'n': 'north', 'north': 'north',
        's': 'south', 'south': 'south',
        'e': 'east', 'east': 'east',
        'w': 'west', 'west': 'west',
        'up': 'up', 'down': 'down'  # For staircases
    }
    
    return direction_map.get(direction.lower())


def create_error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        message (str): Error message
        status_code (int): HTTP status code
        
    Returns:
        Dict[str, Any]: Error response dictionary
    """
    return {
        "error": True,
        "message": message,
        "status_code": status_code
    }


def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data (Any): Response data
        message (str): Success message
        
    Returns:
        Dict[str, Any]: Success response dictionary
    """
    response = {
        "error": False,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    return response


def get_random_room_names() -> List[str]:
    """
    Get a list of possible room name templates.
    
    Returns:
        List[str]: List of room name templates
    """
    return [
        "Ancient Chamber",
        "Forgotten Corridor",
        "Mysterious Hall",
        "Dark Passage",
        "Stone Sanctum",
        "Echoing Cavern",
        "Twilight Chamber",
        "Shadow Gallery",
        "Crumbling Vault",
        "Hidden Alcove",
        "Dusty Archive",
        "Silent Crypt",
        "Moonlit Antechamber",
        "Abandoned Study",
        "Spectral Library"
    ]


def get_random_room_descriptions() -> List[str]:
    """
    Get a list of possible room description templates.
    
    Returns:
        List[str]: List of room description templates
    """
    return [
        "The air here is thick with ancient dust and forgotten memories.",
        "Strange symbols glow faintly on the weathered stone walls.",
        "A cold breeze whispers through cracks in the ancient masonry.",
        "The floor is covered in a carpet of fallen leaves and debris.",
        "Torch sconces line the walls, their flames flickering mysteriously.",
        "The ceiling stretches high above, lost in shadows.",
        "Ancient tapestries hang in tatters from the walls.",
        "The sound of dripping water echoes from somewhere unseen.",
        "Moss and vines have begun to reclaim the stone surfaces.",
        "A sense of unease pervades this forgotten place."
    ]


def sanitize_input(text: str, max_length: int = 100) -> str:
    """
    Sanitize user input text.
    
    Args:
        text (str): Input text to sanitize
        max_length (int): Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove any potentially harmful characters
    sanitized = "".join(c for c in text if c.isprintable())
    
    # Trim to maximum length
    return sanitized[:max_length].strip()