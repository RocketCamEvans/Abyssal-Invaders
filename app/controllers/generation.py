"""
Generation controller for LLM-based name and description generation.
"""

from typing import Dict, Any, Optional, List
from ..models import Enemy, Ally, Room
from ..utils import create_error_response, create_success_response
import random
import os
import sys

# Add the utils directory to the path to import openai_client
utils_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'utils')
sys.path.insert(0, utils_dir)

try:
    from openai_client import OpenAIClient, create_openai_client, is_openai_configured
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class GenerationController:
    """
    Handles LLM-based generation of names and descriptions for game entities.
    
    Note: This is a mock implementation. In a real application, this would
    integrate with an actual LLM service like OpenAI GPT, Anthropic Claude, etc.
    """
    
    def __init__(self, llm_api_key: Optional[str] = None, use_openai: bool = True):
        """
        Initialize the generation controller.
        
        Args:
            llm_api_key (Optional[str]): API key for LLM service (not used in mock)
            use_openai (bool): Whether to use OpenAI for generation (falls back to templates)
        """
        self.llm_api_key = llm_api_key
        self.use_openai = use_openai and OPENAI_AVAILABLE
        self.openai_client = None
        
        print(f"DEBUG GEN CONTROLLER INIT: use_openai parameter={use_openai}, final use_openai={self.use_openai}")
        
        # Initialize OpenAI client if available and requested
        if self.use_openai:
            try:
                self.openai_client = create_openai_client()
                if not self.openai_client:
                    print("Warning: OpenAI not configured properly")
                    self.use_openai = False
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                self.use_openai = False
        
        print(f"DEBUG GEN CONTROLLER INIT: Final use_openai={self.use_openai}, will use {'OpenAI' if self.use_openai else 'TEMPLATES'}")
        
        # Load templates as fallback
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
        # Try OpenAI first if available
        if self.use_openai and self.openai_client:
            try:
                room_desc = room.description if room else ""
                return self.openai_client.generate_enemy_content(floor, room_desc)
            except Exception as e:
                print(f"OpenAI generation failed, falling back to templates: {e}")
        
        # Fallback to template-based generation
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
        # Try OpenAI first if available
        if self.use_openai and self.openai_client:
            try:
                room_desc = room.description if room else ""
                return self.openai_client.generate_ally_content(floor, room_desc)
            except Exception as e:
                print(f"OpenAI generation failed, falling back to templates: {e}")
        
        # Fallback to template-based generation
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
        print(f"DEBUG GEN CONTROLLER: generate_room_content called for floor {floor}, room {room_id}")
        print(f"DEBUG GEN CONTROLLER: FORCING TEMPLATE USE FOR ROOMS (OpenAI disabled for rooms only)")
        
        # ALWAYS use template-based generation for rooms (custom requirement)
        # OpenAI is still used for enemies and allies, just not rooms
        print(f"DEBUG GEN CONTROLLER: Using template-based generation")
        difficulty_modifier = self._get_difficulty_modifier(floor)
        print(f"DEBUG GEN CONTROLLER: Difficulty modifier for floor {floor}: '{difficulty_modifier}'")
        
        # Select room names based on floor difficulty
        room_names = self.room_name_templates.get(difficulty_modifier, self.room_name_templates["basic"])
        print(f"DEBUG GEN CONTROLLER: Available room names: {room_names}")
        
        name = random.choice(room_names)
        description = self._generate_room_description(name, floor, room_id)
        
        print(f"DEBUG GEN CONTROLLER: Selected room name: '{name}'")
        
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
                "Warped Hallway", "Deranged Buffalo Room", "Splintered Cossatot Room", "Abandoned Durham Room",
                "Narrow Hallway", "Cracked Mockingbird Room",
                "Empty Pettigrew Room", "Basic Razorback Room", "Dusty Bathroom", "Breakroom of DOOM",
                "Wizard's Cellar", "Featureless Chamber"
            ],
            "intermediate": [
                "Crystalized Hallway", "Iron-clad Buffalo Room", "Enchanted Durham Room",
                "Gloomy Hallway", "Ethereal Mockingbird Room", "Forgotten Ozark Room", "Spectral Panda Room",
                "Ancient Pettigrew Room", "Abandoned Elevator Shaft", "Crying Room",
                "Guardian's Rest", "Twisted Laboratory", "Damp Armory", "Sanctum of Echoes"
            ],
            "advanced": [
                "Demolished Hallway",
                "Hellish Hallway", "Forbidden Ozark Room", "Forsaken Panda Room",
                "Endless Pettigrew Room", "Screaming Razorback Room", "Crazed Clock Room", "Filthy Storage Closet",
                "Dimensional Rift", "Nightmare Realm", "Soul Prison", "Reality Fracture", "Abyssal Gateway", "Terror Sanctum", "Madness Chamber"
            ],
            "legendary": [
                "Hallway of Ancient Evils", "Hallway Between Infinite Worlds",
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