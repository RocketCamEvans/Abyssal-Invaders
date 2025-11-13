#!/usr/bin/env python3
"""
Test script to verify OpenAI integration with the dungeon crawler game.
"""

import sys
import os

# Add the parent directory to the Python path to access utils
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from utils.openai_client import OpenAIClient, create_openai_client, is_openai_configured
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def main():
    """
    Test the OpenAI integration.
    """
    print("🎮 Testing OpenAI Integration for Abyssal Invaders")
    print("=" * 50)
    
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI client not available!")
        print("Please install the openai library: pip install openai")
        return
    
    # Check if API key is set
    if not is_openai_configured():
        print("❌ OpenAI API key not set!")
        print("Please set your OPENAI_API_KEY in the .env file")
        print("Get your API key from: https://platform.openai.com/api-keys")
        return
    
    # Test connection
    client = create_openai_client()
    if not client:
        print("❌ Could not create OpenAI client")
        return
    
    print("✅ OpenAI client initialized successfully")
    print("\n🎲 Testing game content generation...")
    
    try:
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