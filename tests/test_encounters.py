#!/usr/bin/env python3
"""
Test script to verify combat and staircase functionality.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_encounter_system():
    """Test the encounter system by creating a player and moving around."""
    
    print("🎮 Testing Abyssal Invaders Encounter System")
    print("=" * 50)
    
    # Create a new player
    print("\n1. Creating new player...")
    create_response = requests.post(f"{BASE_URL}/player/new", 
                                   json={"name": "Test Hero"})
    
    if create_response.status_code != 200:
        print(f"❌ Failed to create player: {create_response.text}")
        return
    
    player_data = create_response.json()
    session_id = player_data['data']['session_id']
    print(f"✅ Created player: {player_data['data']['player']['name']}")
    print(f"   Session ID: {session_id}")
    
    # Test room debug info
    print("\n2. Checking initial room debug info...")
    debug_response = requests.post(f"{BASE_URL}/debug/room", 
                                  json={"session_id": session_id})
    
    if debug_response.status_code == 200:
        debug_data = debug_response.json()['data']
        print(f"   Room: {debug_data['room_name']} ({debug_data['room_id']})")
        print(f"   Encounter chance: {debug_data['encounter_chance']:.1%}")
        print(f"   Has staircase: {debug_data['has_staircase']}")
        print(f"   Available directions: {debug_data['available_directions']}")
        print(f"   Encounters in 10 rolls: {debug_data['encounters_triggered_out_of_10']}/10")
    
    # Try moving around and look for encounters
    moves_attempted = 0
    encounters_found = 0
    stairs_found = 0
    
    for attempt in range(20):  # Try up to 20 moves
        print(f"\n3.{attempt + 1} Attempting move #{attempt + 1}...")
        
        # Get current status
        status_response = requests.post(f"{BASE_URL}/player/status", 
                                       json={"session_id": session_id})
        
        if status_response.status_code != 200:
            print(f"❌ Failed to get status: {status_response.text}")
            break
        
        status_data = status_response.json()['data']
        available_directions = status_data['movement_options']['available_directions']
        has_staircase = status_data['current_room']['has_staircase']
        
        if has_staircase:
            stairs_found += 1
            print(f"🆙 Found staircase in {status_data['current_room']['name']}!")
        
        if not available_directions:
            print("⚠️  No available directions from current room")
            break
        
        # Try to move in the first available direction
        direction = available_directions[0]
        move_response = requests.post(f"{BASE_URL}/player/move", 
                                     json={"session_id": session_id, "direction": direction})
        
        if move_response.status_code != 200:
            print(f"❌ Move failed: {move_response.text}")
            break
        
        move_data = move_response.json()['data']
        moves_attempted += 1
        
        print(f"   Moved {direction} to: {move_data['room_info']['name']}")
        
        # Check debug info
        if 'debug' in move_data:
            debug = move_data['debug']
            print(f"   Debug: new_room={debug.get('room_was_new')}, encounter_chance={debug.get('encounter_chance'):.1%}")
            if 'encounter_roll_result' in debug:
                print(f"   Encounter roll: {debug['encounter_roll_result']}")
        
        # Check if encounter occurred
        if move_data.get('encounter_occurred'):
            encounters_found += 1
            encounter_result = move_data.get('encounter_result', {})
            print(f"⚔️  ENCOUNTER! Result: {encounter_result.get('data', {}).get('winner', 'unknown')}")
        else:
            print(f"   No encounter (exploration gold: {move_data.get('exploration_gold', 0)})")
        
        # Small delay to be nice to the server
        time.sleep(0.1)
    
    # Final statistics
    print(f"\n📊 Test Results:")
    print(f"   Moves attempted: {moves_attempted}")
    print(f"   Encounters found: {encounters_found}")
    print(f"   Stairs found: {stairs_found}")
    
    if moves_attempted > 0:
        encounter_rate = encounters_found / moves_attempted
        stair_rate = stairs_found / moves_attempted
        print(f"   Encounter rate: {encounter_rate:.1%}")
        print(f"   Stair rate: {stair_rate:.1%}")
        
        if encounters_found == 0:
            print("❌ NO ENCOUNTERS FOUND - There's definitely a bug!")
        elif encounter_rate < 0.1:
            print("⚠️  Very low encounter rate - might be a problem")
        else:
            print("✅ Encounters seem to be working")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    try:
        test_encounter_system()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the Flask app is running on localhost:5000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")