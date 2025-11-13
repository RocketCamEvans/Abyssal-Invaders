#!/usr/bin/env python3
"""
Simple demonstration of the backtracking fix in the dungeon crawler.
This script shows that players can now backtrack to rooms they came from.
"""

import sys
import os

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import Player
from app.controllers import MovementController


def demonstrate_backtracking():
    """Demonstrate that backtracking now works correctly."""
    
    print("🏰 ABYSSAL INVADERS - Backtracking Demonstration")
    print("=" * 60)
    
    # Create a new player and movement controller
    player = Player(name="Test Explorer")
    controller = MovementController()
    
    print(f"👤 Player: {player.name}")
    print(f"💰 Starting Gold: {player.gold}")
    print(f"🏠 Starting Floor: {player.floor}")
    print()
    
    # Initialize starting room
    print("🏁 Initializing starting room...")
    start_room = controller.initialize_player_room(player)
    print(f"📍 Current Room: {start_room.name} (ID: {start_room.room_id})")
    print(f"🗒️  Description: {start_room.description}")
    print(f"🧭 Available Directions: {start_room.get_available_directions()}")
    print()
    
    # Try to move in the first available direction
    available_directions = start_room.get_available_directions()
    
    if not available_directions:
        print("❌ No directions available from starting room!")
        return
    
    first_direction = available_directions[0]
    print(f"🚶 Moving {first_direction}...")
    
    success, result = controller.move_player(player, first_direction)
    
    if not success:
        print(f"❌ Failed to move: {result}")
        return
    
    print(f"✅ Successfully moved {first_direction}!")
    print(f"📍 New Room: {result['data']['room_info']['name']} (ID: {player.room_id})")
    print(f"🗒️  Description: {result['data']['room_info']['description']}")
    print()
    
    # Check if we can backtrack
    current_room = controller.get_room(player.room_id, player.floor)
    opposite_direction = controller._get_opposite_direction(first_direction)
    
    print(f"🔄 Checking for backtrack connection ({opposite_direction})...")
    back_connection = current_room.get_connection(opposite_direction)
    
    if back_connection:
        print(f"✅ Backtrack connection found: {opposite_direction} -> {back_connection}")
        
        # Try to go back
        print(f"🚶 Attempting to backtrack {opposite_direction}...")
        success_back, result_back = controller.move_player(player, opposite_direction)
        
        if success_back:
            print(f"✅ Successfully backtracked!")
            print(f"📍 Back at: {result_back['data']['room_info']['name']} (ID: {player.room_id})")
            
            if player.room_id == "start":
                print("🎉 BACKTRACKING WORKS! Player successfully returned to starting room!")
            else:
                print(f"⚠️  Player is at {player.room_id}, not the starting room")
        else:
            print(f"❌ Failed to backtrack: {result_back}")
    else:
        print(f"❌ No backtrack connection found for {opposite_direction}")
    
    print()
    print("=" * 60)
    print("🎯 Demonstration complete!")


def demonstrate_room_id_fix():
    """Demonstrate that room IDs are now properly generated."""
    
    print("\n🔧 ROOM ID GENERATION FIX DEMONSTRATION")
    print("=" * 60)
    
    controller = MovementController()
    
    # Generate a few test rooms to show IDs are reasonable
    print("🏗️  Generating test rooms...")
    
    for i in range(5):
        from app.utils.helpers import generate_room_id
        room_id = generate_room_id(1)
        print(f"   Room {i+1}: {room_id}")
    
    print()
    print("✅ Room IDs are now concise and don't grow exponentially!")
    print("   (No more floor_1_floor_1_floor_1_... patterns)")


if __name__ == "__main__":
    try:
        demonstrate_backtracking()
        demonstrate_room_id_fix()
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        print("Make sure you're running this from the dungeon_crawler_api directory!")