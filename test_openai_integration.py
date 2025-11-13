#!/usr/bin/env python3
"""
Test script to verify OpenAI integration with the dungeon crawler game.
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai_request import OpenAIClient, test_openai_connection


def main():
    """
    Test the OpenAI integration.
    """
    print("🎮 Testing OpenAI Integration for Abyssal Invaders")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'sk-your_actual_openai_api_key_here':
        print("❌ OpenAI API key not set!")
        print("Please set your OPENAI_API_KEY in the .env file")
        print("Get your API key from: https://platform.openai.com/api-keys")
        return
    
    # Test connection
    if not test_openai_connection():
        print("❌ Could not connect to OpenAI API")
        return
    
    print("\n🎲 Testing game content generation...")
    
    try:
        client = OpenAIClient()
        
        # Test enemy generation
        print("\n🐉 Generating enemy for Floor 2...")
        enemy = client.generate_enemy_content(2, "Ancient Stone Chamber")
        print(f"  Name: {enemy['name']}")
        print(f"  Description: {enemy['description']}")
        
        # Test ally generation  
        print("\n🤝 Generating ally for Floor 2...")
        ally = client.generate_ally_content(2, "Ancient Stone Chamber")
        print(f"  Name: {ally['name']}")
        print(f"  Description: {ally['description']}")
        
        # Test room generation
        print("\n🏰 Generating room for Floor 3...")
        room = client.generate_room_content(3)
        print(f"  Name: {room['name']}")
        print(f"  Description: {room['description']}")
        
        # Test combat description
        print("\n⚔️  Generating combat description...")
        combat_desc = client.generate_combat_description(
            "Hero", "Shadow Beast", "Moonlit Sanctum", "encounter"
        )
        print(f"  Description: {combat_desc}")
        
        print("\n✅ All tests passed! OpenAI integration is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        return


if __name__ == "__main__":
    main()