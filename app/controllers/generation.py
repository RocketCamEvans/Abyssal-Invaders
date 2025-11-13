"""
Generation controller for LLM-based name and description generation.
"""

from typing import Dict, Any, Optional, List
from ..models import Enemy, Ally, Room
from ..utils import create_error_response, create_success_response
import random


class GenerationController:
    """
    Handles LLM-based generation of names and descriptions for game entities.
    
    Note: This is a mock implementation. In a real application, this would
    integrate with an actual LLM service like OpenAI GPT, Anthropic Claude, etc.
    """
    
    def __init__(self, llm_api_key: Optional[str] = None):
        """
        Initialize the generation controller.
        
        Args:
            llm_api_key (Optional[str]): API key for LLM service (not used in mock)
        """
        self.llm_api_key = llm_api_key
        self.enemy_name_templates = self._load_enemy_name_templates()
        self.ally_name_templates = self._load_ally_name_templates()
        self.room_name_templates = self._load_room_name_templates()
        self.description_templates = self._load_description_templates()
    
    def generate_enemy_content(self, floor: int, room: Optional[Room] = None) -> Dict[str, str]:
        """
        Generate name and description for an enemy.
        
        Args:
            floor (int): Current floor level
            room (Optional[Room]): Room context for generation
            
        Returns:
            Dict[str, str]: Generated name and description
        """
        # In a real implementation, this would call an LLM API
        # For now, we'll use template-based generation
        
        difficulty_modifier = self._get_difficulty_modifier(floor)
        room_context = self._get_room_context(room)
        
        # Select appropriate enemy templates based on floor
        enemy_names = self.enemy_name_templates.get(difficulty_modifier, self.enemy_name_templates["basic"])
        
        name = random.choice(enemy_names)
        description = self._generate_enemy_description(name, floor, room_context)
        
        return {
            "name": name,
            "description": description
        }
    
    def generate_ally_content(self, floor: int, room: Optional[Room] = None) -> Dict[str, str]:
        """
        Generate name and description for an ally.
        
        Args:
            floor (int): Current floor level
            room (Optional[Room]): Room context for generation
            
        Returns:
            Dict[str, str]: Generated name and description
        """
        room_context = self._get_room_context(room)
        
        name = random.choice(self.ally_name_templates)
        description = self._generate_ally_description(name, floor, room_context)
        
        return {
            "name": name,
            "description": description
        }
    
    def generate_room_content(self, floor: int, room_id: str) -> Dict[str, str]:
        """
        Generate name and description for a room.
        
        Args:
            floor (int): Floor level
            room_id (str): Room identifier
            
        Returns:
            Dict[str, str]: Generated name and description
        """
        difficulty_modifier = self._get_difficulty_modifier(floor)
        
        # Select room names based on floor difficulty
        room_names = self.room_name_templates.get(difficulty_modifier, self.room_name_templates["basic"])
        
        name = random.choice(room_names)
        description = self._generate_room_description(name, floor, room_id)
        
        return {
            "name": name,
            "description": description
        }
    
    def generate_combat_description(self, player_name: str, enemy_name: str, 
                                  room_description: str, action_type: str = "encounter") -> str:
        """
        Generate a combat description using room context.
        
        Args:
            player_name (str): Name of the player
            enemy_name (str): Name of the enemy
            room_description (str): Description of the room
            action_type (str): Type of combat action
            
        Returns:
            str: Generated combat description
        """
        # Mock LLM-style generation
        templates = {
            "encounter": [
                f"As {player_name} explores the area, {enemy_name} suddenly appears! The {room_description.lower()} provides an ominous backdrop for the impending battle.",
                f"The atmosphere grows tense as {enemy_name} emerges from within {room_description.lower()}. {player_name} prepares for combat!",
                f"{player_name} senses danger in this place. Sure enough, {enemy_name} blocks the path ahead, the {room_description.lower()} adding to the menace.",
                f"A shadow moves in {room_description.lower()}. {enemy_name} reveals itself, ready to challenge {player_name}!"
            ],
            "victory": [
                f"{player_name} stands victorious over {enemy_name}! The {room_description.lower()} seems less threatening now.",
                f"With {enemy_name} defeated, {player_name} can continue exploring. The {room_description.lower()} returns to its eerie silence.",
                f"{enemy_name} falls to {player_name}'s skill. The victory echoes through {room_description.lower()}."
            ]
        }
        
        return random.choice(templates.get(action_type, templates["encounter"]))
    
    def _get_difficulty_modifier(self, floor: int) -> str:
        """
        Get difficulty modifier based on floor level.
        
        Args:
            floor (int): Floor level
            
        Returns:
            str: Difficulty modifier
        """
        if floor <= 2:
            return "basic"
        elif floor <= 5:
            return "intermediate"
        elif floor <= 10:
            return "advanced"
        else:
            return "legendary"
    
    def _get_room_context(self, room: Optional[Room]) -> str:
        """
        Extract context from room for generation.
        
        Args:
            room (Optional[Room]): Room object
            
        Returns:
            str: Room context string
        """
        if room:
            return f"{room.name} - {room.description}"
        return "a mysterious chamber"
    
    def _generate_enemy_description(self, name: str, floor: int, room_context: str) -> str:
        """
        Generate enemy description based on name and context.
        
        Args:
            name (str): Enemy name
            floor (int): Floor level
            room_context (str): Room context
            
        Returns:
            str: Generated description
        """
        power_descriptors = {
            "basic": ["menacing", "dangerous", "hostile", "aggressive"],
            "intermediate": ["formidable", "deadly", "vicious", "fearsome"],
            "advanced": ["terrifying", "nightmarish", "devastating", "monstrous"],
            "legendary": ["apocalyptic", "otherworldly", "legendary", "mythical"]
        }
        
        difficulty = self._get_difficulty_modifier(floor)
        descriptor = random.choice(power_descriptors[difficulty])
        
        descriptions = [
            f"A {descriptor} creature that has claimed this domain as its own. Its presence fills the air with dread.",
            f"This {descriptor} being seems perfectly adapted to the dark environment. It eyes you with malevolent intelligence.",
            f"The {descriptor} {name.lower()} moves with predatory grace, clearly accustomed to the dangers of floor {floor}.",
            f"An ancient and {descriptor} entity, the {name.lower()} has survived in these depths through cunning and strength."
        ]
        
        return random.choice(descriptions)
    
    def _generate_ally_description(self, name: str, floor: int, room_context: str) -> str:
        """
        Generate ally description based on name and context.
        
        Args:
            name (str): Ally name
            floor (int): Floor level
            room_context (str): Room context
            
        Returns:
            str: Generated description
        """
        descriptions = [
            f"A brave soul who has somehow survived the perils of floor {floor}. {name} offers to aid you in battle.",
            f"This seasoned adventurer recognizes a kindred spirit in you. {name} is willing to lend their strength to your cause.",
            f"Despite the dangers lurking everywhere, {name} maintains hope and courage. They stand ready to fight alongside you.",
            f"The trials of the dungeon have forged {name} into a reliable ally. Their experience could prove invaluable."
        ]
        
        return random.choice(descriptions)
    
    def _generate_room_description(self, name: str, floor: int, room_id: str) -> str:
        """
        Generate room description based on name and context.
        
        Args:
            name (str): Room name
            floor (int): Floor level
            room_id (str): Room ID
            
        Returns:
            str: Generated description
        """
        atmosphere_elements = [
            "The air is thick with ancient dust and mystery.",
            "Strange echoes bounce off the weathered walls.",
            "A cold draft whispers through hidden passages.",
            "The stones seem to hold memories of ages past.",
            "An otherworldly energy permeates this space.",
            "Shadows dance in the flickering torchlight.",
            "The silence here is both peaceful and unnerving."
        ]
        
        base_description = random.choice(atmosphere_elements)
        
        floor_context = ""
        if floor > 1:
            floor_context = f" The deeper you venture into floor {floor}, the more alien everything becomes."
        
        return base_description + floor_context
    
    def _load_enemy_name_templates(self) -> Dict[str, List[str]]:
        """
        Load enemy name templates organized by difficulty.
        
        Returns:
            Dict[str, List[str]]: Enemy name templates
        """
        return {
            "basic": [
                "Shadowling", "Cave Rat", "Tunnel Worm", "Stone Spider", "Moss Crawler",
                "Dark Beetle", "Sewer Ghoul", "Rusty Golem", "Feral Cat", "Dungeon Bat"
            ],
            "intermediate": [
                "Crimson Wraith", "Iron Sentinel", "Venom Stalker", "Bone Crusher", "Flame Imp",
                "Crystal Guardian", "Thunder Lizard", "Void Phantom", "Toxic Slime", "War Hound"
            ],
            "advanced": [
                "Abyssal Terror", "Soul Reaper", "Chaos Beast", "Nightmare Spawn", "Dread Knight",
                "Infernal Warden", "Void Dragon", "Death Stalker", "Shadow Tyrant", "Doom Bringer"
            ],
            "legendary": [
                "Ancient Evil", "Primordial Horror", "Eternal Destroyer", "Cosmic Aberration", "Divine Nemesis",
                "Reality Ripper", "Time Devourer", "Dimensional Lord", "Apocalypse Herald", "Oblivion Master"
            ]
        }
    
    def _load_ally_name_templates(self) -> List[str]:
        """
        Load ally name templates.
        
        Returns:
            List[str]: Ally name templates
        """
        return [
            "Brave Warrior", "Lost Scholar", "Mysterious Mage", "Seasoned Explorer", "Noble Knight",
            "Wandering Healer", "Skilled Archer", "Ancient Spirit", "Friendly Ghost", "Wise Hermit",
            "Battle-Scarred Veteran", "Hopeful Apprentice", "Traveling Merchant", "Escaped Prisoner",
            "Guardian Angel", "Helpful Sprite", "Determined Survivor", "Kindred Soul"
        ]
    
    def _load_room_name_templates(self) -> Dict[str, List[str]]:
        """
        Load room name templates organized by difficulty.
        
        Returns:
            Dict[str, List[str]]: Room name templates
        """
        return {
            "basic": [
                "Stone Chamber", "Dusty Corridor", "Old Storage Room", "Abandoned Cell", "Narrow Passage",
                "Cracked Hall", "Forgotten Alcove", "Simple Antechamber", "Empty Vault", "Basic Sanctum"
            ],
            "intermediate": [
                "Crystal Cavern", "Iron Gallery", "Mystic Archive", "Enchanted Library", "Guardian's Rest",
                "Ethereal Sanctum", "Twisted Laboratory", "Ancient Armory", "Spectral Chamber", "Elemental Forge"
            ],
            "advanced": [
                "Dimensional Rift", "Void Observatory", "Nightmare Realm", "Chaos Laboratory", "Temporal Nexus",
                "Soul Prison", "Reality Fracture", "Abyssal Gateway", "Terror Sanctum", "Madness Chamber"
            ],
            "legendary": [
                "Cosmic Throne Room", "Divine Judgment Hall", "Eternal Battlefield", "Primordial Nexus", "Reality Core",
                "Infinite Labyrinth", "Omniversal Archive", "Celestial Observatory", "Apocalypse Chamber", "Creation Forge"
            ]
        }
    
    def _load_description_templates(self) -> Dict[str, List[str]]:
        """
        Load description templates for various contexts.
        
        Returns:
            Dict[str, List[str]]: Description templates
        """
        return {
            "atmospheric": [
                "The air hangs heavy with ancient secrets.",
                "Whispers of forgotten ages echo through the space.",
                "An otherworldly energy pulses through the very stones.",
                "Time seems to move differently in this place.",
                "The boundaries between reality and nightmare blur here."
            ],
            "dangerous": [
                "A sense of imminent danger pervades the atmosphere.",
                "Every shadow could conceal a lurking threat.",
                "The silence is broken only by distant, ominous sounds.",
                "This place has claimed many lives before yours.",
                "Death has left its mark on every surface."
            ]
        }