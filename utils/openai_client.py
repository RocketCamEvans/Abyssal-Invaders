"""
OpenAI API utilities for generating game content using the official OpenAI Python library.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from llm_logger import log_llm_generation

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()


class OpenAIClient:
    """
    Client for making requests to OpenAI's API using the official Python library.
    """
    
    def __init__(self):
        """
        Initialize the OpenAI client with API key from environment.
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
            
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key or self.api_key == 'your_openai_api_key_here':
            raise ValueError("OPENAI_API_KEY not found or not set in environment variables")
        
        # Initialize the OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate_completion(self, prompt: str, model: str = "gpt-3.5-turbo", 
                           max_tokens: int = 150, temperature: float = 0.7,
                           generation_type: str = "general") -> Optional[str]:
        """
        Generate a completion using OpenAI's chat completions API.
        
        Args:
            prompt (str): The input prompt
            model (str): The model to use (default: gpt-3.5-turbo)
            max_tokens (int): Maximum tokens in response
            temperature (float): Creativity level (0.0 to 1.0)
            generation_type (str): Type of generation for logging
            
        Returns:
            Optional[str]: Generated text or None if error
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            generated_text = response.choices[0].message.content.strip()
            
            # Log the generation to CSV for evaluation (simplified format)
            log_llm_generation(
                generated_text=generated_text,
                prompt=prompt
            )
            
            return generated_text
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return None
    
    def generate_enemy_content(self, floor: int, room_description: str = "") -> Dict[str, str]:
        """
        Generate enemy name and description for the dungeon crawler.
        
        Args:
            floor (int): Current floor level
            room_description (str): Description of the room for context
            
        Returns:
            Dict[str, str]: Dictionary with 'name' and 'description' keys
        """
        room_context = f" in {room_description}" if room_description else ""
        
        prompt = f"""You're creating enemies for a cursed office building dungeon crawler. Floor {floor}{room_context}.

THEME: An evil wizard cursed Rocket Software into a monster labyrinth. Mix office elements with fantasy.

STYLE: Whimsical, creative, but COHERENT. The enemy should make sense for this setting.

IMPORTANT: Create UNIQUE, VARIED enemies. Don't repeat common tropes. Think of creative combinations!

EXAMPLES: "Sentient Copier" that shoots paper cuts, "Coffee Elemental" that scalds enemies, "Suited Vampire" draining motivation, "Filing Cabinet Mimic" that ambushes workers.

Higher floors = more dangerous/creative enemies.

Return JSON:
{{"name":"2-4 words","description":"Brief, fitting description under 200 chars"}}"""

        response = self.generate_completion(prompt, max_tokens=120, temperature=0.8, generation_type="enemy_content")
        
        if response:
            try:
                import json
                # Try to extract JSON if there's extra text
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    content = json.loads(json_str)
                    if "name" in content and "description" in content:
                        # Enforce character limit
                        if len(content["description"]) > 250:
                            content["description"] = content["description"][:247] + "..."
                        return content
            except json.JSONDecodeError:
                pass
        
        # Fallback with creative names if API fails or returns invalid JSON
        creative_fallbacks = [
            {"name": "Corrupted Intern", "description": "Once a fresh-faced worker, now twisted by the curse into a mindless corporate drone."},
            {"name": "Paper Swarm", "description": "A whirlwind of cursed documents that slice through the air with deadly precision."},
            {"name": "Possessed Desk Chair", "description": "An ergonomic nightmare that rolls toward victims with malevolent intent."},
            {"name": "Phantom Manager", "description": "A spectral supervisor that drains morale and life force with endless meetings."},
            {"name": "Stapler Demon", "description": "A nightmarish fusion of office supplies that fires cursed staples at intruders."},
            {"name": "Coffee Elemental", "description": "A scalding entity formed from the break room's darkest brews, bitter and dangerous."},
            {"name": "Filing Beast", "description": "A monstrous creature made of metal cabinets that ambushes the unprepared."},
            {"name": "Keyboard Wraith", "description": "A ghostly entity that types curses into reality with ethereal keystrokes."}
        ]
        import random
        return random.choice(creative_fallbacks)
    
    def generate_ally_content(self, floor: int, room_description: str = "") -> Dict[str, str]:
        """
        Generate ally name and description for the dungeon crawler.
        
        Args:
            floor (int): Current floor level
            room_description (str): Description of the room for context
            
        Returns:
            Dict[str, str]: Dictionary with 'name' and 'description' keys
        """
        room_context = f" in {room_description}" if room_description else ""
        
        prompt = f"""Create an ally for a cursed office building dungeon. Floor {floor}{room_context}.

SETTING: Rocket Software building cursed by evil wizard. Employees fight back with newfound powers.

TONE: Whimsical but coherent. They should feel like actual office workers or objects turned heroic.

IMPORTANT: Be CREATIVE and VARIED! Don't use the same archetypes. Think of unique combinations!

EXAMPLES: "Brave Intern" with uncanny enthusiasm, "Enchanted Stapler" that binds enemies, "Ex-Janitor Wizard" who knows secret passages, "IT Support Mage" who debugs reality.

Create someone fitting this world who wants to help.

JSON:
{{"name":"2-3 words","description":"Why they're helping (1-2 clear sentences)"}}"""

        response = self.generate_completion(prompt, max_tokens=100, temperature=0.8, generation_type="ally_content")
        
        if response:
            try:
                import json
                content = json.loads(response)
                if "name" in content and "description" in content:
                    return content
            except json.JSONDecodeError:
                pass
        
        # Fallback if API fails or returns invalid JSON
        return {
            "name": "Mysterious Helper",
            "description": "A brave soul who has survived the perils of this floor and offers to aid you in battle."
        }
    
    def generate_room_content(self, floor: int, room_type: str = "chamber") -> Dict[str, str]:
        """
        Generate room name and description for the dungeon crawler.
        
        Args:
            floor (int): Floor number
            room_type (str): Type of room (chamber, corridor, etc.)
            
        Returns:
            Dict[str, str]: Dictionary with 'name' and 'description' keys
        """
        prompt = f"""Create a {room_type} for floor {floor} of a fantasy dungeon crawler game.

Please respond with a JSON object containing:
- "name": A short, atmospheric room name (2-4 words)
- "description": A brief, immersive description (1-2 sentences)

The room should feel appropriate for floor {floor}. Deeper floors should be more mysterious and dangerous.

Example format:
{{"name": "Echoing Sanctum", "description": "Ancient stone walls covered in faded murals whisper secrets of forgotten ages."}}"""

        response = self.generate_completion(prompt, max_tokens=100, temperature=0.8, generation_type="room_content")
        
        if response:
            try:
                import json
                content = json.loads(response)
                if "name" in content and "description" in content:
                    return content
            except json.JSONDecodeError:
                pass
        
        # Fallback if API fails or returns invalid JSON
        return {
            "name": f"Floor {floor} {room_type.title()}",
            "description": f"A mysterious {room_type} on floor {floor}, filled with the echoes of ancient secrets."
        }
    
    def generate_combat_description(self, player_name: str, enemy_name: str, 
                                  room_name: str, action: str = "encounter") -> str:
        """
        Generate a combat description for dramatic effect.
        
        Args:
            player_name (str): Name of the player
            enemy_name (str): Name of the enemy
            room_name (str): Name of the room
            action (str): Type of action (encounter, victory, etc.)
            
        Returns:
            str: Generated combat description
        """
        prompt = f"""Write a brief, dramatic combat {action} description for a dungeon crawler game.

Context:
- Player: {player_name}
- Enemy: {enemy_name}
- Location: {room_name}
- Action: {action}

Write 1-2 sentences that are exciting and immersive. Keep it concise but atmospheric."""

        response = self.generate_completion(prompt, max_tokens=80, temperature=0.9, generation_type="combat_description")
        
        if response:
            return response
        
        # Fallback description
        if action == "encounter":
            return f"{player_name} encounters {enemy_name} in the {room_name}!"
        elif action == "victory":
            return f"{player_name} emerges victorious over {enemy_name}!"
        else:
            return f"{player_name} and {enemy_name} clash in the {room_name}!"


def is_openai_configured() -> bool:
    """
    Check if OpenAI is properly configured.
    
    Returns:
        bool: True if OpenAI is available and configured
    """
    if not OPENAI_AVAILABLE:
        return False
    
    api_key = os.getenv('OPENAI_API_KEY')
    return api_key and api_key != 'your_openai_api_key_here'


def create_openai_client() -> Optional[OpenAIClient]:
    """
    Create an OpenAI client if properly configured.
    
    Returns:
        Optional[OpenAIClient]: OpenAI client or None if not available
    """
    try:
        if is_openai_configured():
            return OpenAIClient()
    except Exception as e:
        print(f"Failed to create OpenAI client: {e}")
    
    return None