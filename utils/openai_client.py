"""
OpenAI API utilities for generating game content using the official OpenAI Python library.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

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
                           max_tokens: int = 150, temperature: float = 0.7) -> Optional[str]:
        """
        Generate a completion using OpenAI's chat completions API.
        
        Args:
            prompt (str): The input prompt
            model (str): The model to use (default: gpt-3.5-turbo)
            max_tokens (int): Maximum tokens in response
            temperature (float): Creativity level (0.0 to 1.0)
            
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
            
            return response.choices[0].message.content.strip()
            
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
        
        prompt = f"""You are creating enemies for a whimsical fantasy dungeon crawler set in a cursed office building.

An evil wizard cursed Rocket Software's building into an infinite labyrinth. Employees now fight back with fantasy powers!

Create an enemy for floor {floor}{room_context}.

IMPORTANT: Mix business-themed enemies (like "Suited Vampire" or "Sentient Water Fountain") with generic fantasy monsters (like "Mossy Lurker"). Keep a fantastical but whimsical, slightly funny tone.

Respond ONLY with a JSON object (no other text):
{{"name": "Enemy Name (2-4 words)", "description": "Brief, whimsical description (MAX 200 characters)"}}

The description MUST be under 200 characters. Be creative but concise! Higher floors = more dangerous enemies."""

        response = self.generate_completion(prompt, max_tokens=120, temperature=0.85)
        
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
        
        # Fallback if API fails or returns invalid JSON
        return {
            "name": f"Floor {floor} Creature",
            "description": "A mysterious creature lurks in the shadows, adapted to the dangers of this level."
        }
    
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
        
        prompt = f"""Create a helpful ally for floor {floor} of a dungeon crawler game{room_context}.

Please respond with a JSON object containing:
- "name": A short, friendly ally name (2-3 words max)
- "description": A brief description of why they want to help (1-2 sentences)

The ally should feel appropriate for floor {floor} and be someone who would aid the player in combat.

Example format:
{{"name": "Brave Scout", "description": "A seasoned explorer who recognizes a kindred spirit and offers to lend their bow to your cause."}}"""

        response = self.generate_completion(prompt, max_tokens=100, temperature=0.8)
        
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

        response = self.generate_completion(prompt, max_tokens=100, temperature=0.8)
        
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

        response = self.generate_completion(prompt, max_tokens=80, temperature=0.9)
        
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