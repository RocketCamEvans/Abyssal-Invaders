#!/usr/bin/env python3
"""
Test script for the new turn-based combat system.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_turn_based_combat():
    """Test the new turn-based combat system."""
    
    print("🎮 Testing Turn-Based Combat System")
    print("=" * 50)
    
    # Create a new player
    print("\n1. Creating new player...")
    create_response = requests.post(f"{BASE_URL}/player/new", 
                                  json={"name": "Combat Tester"})
    
    if create_response.status_code != 200:
        print(f"❌ Failed to create player: {create_response.text}")
        return False
    
    player_data = create_response.json()
    session_id = player_data['data']['session_id']
    print(f"✅ Player created with session: {session_id}")
    
    # Move around to find a battle
    print("\n2. Moving around to find encounters...")
    directions = ['north', 'south', 'east', 'west']
    battle_found = False
    
    for i in range(10):  # Try up to 10 moves
        direction = directions[i % len(directions)]
        
        move_response = requests.post(f"{BASE_URL}/player/move",
                                    json={"session_id": session_id, "direction": direction})
        
        if move_response.status_code != 200:
            print(f"❌ Move failed: {move_response.text}")
            continue
        
        move_data = move_response.json()['data']
        print(f"📍 Moved {direction} to: {move_data['room_name']}")
        
        # Check for ally encounter
        if move_data.get('ally_encountered'):
            ally_info = move_data['ally_result']
            print(f"🤝 Found ally: {ally_info['ally_name']} - {ally_info['message']}")
        
        # Check for battle
        if move_data.get('encounter_occurred'):
            print(f"⚔️  Battle started!")
            battle_found = True
            break
        
        time.sleep(0.5)  # Small delay between moves
    
    if not battle_found:
        print("❌ No battle encountered after 10 moves")
        return False
    
    # Test turn-based combat
    print("\n3. Testing turn-based combat...")
    
    # Get player status to check battle state
    status_response = requests.post(f"{BASE_URL}/player/status",
                                  json={"session_id": session_id})
    
    if status_response.status_code != 200:
        print(f"❌ Failed to get status: {status_response.text}")
        return False
    
    status_data = status_response.json()['data']
    
    if not status_data.get('in_battle'):
        print("❌ Player should be in battle but isn't")
        return False
    
    print(f"✅ Player is in battle!")
    print(f"   Enemy: {status_data.get('current_enemy', {}).get('name', 'Unknown')}")
    print(f"   Player Health: {status_data['health']}")
    print(f"   Ally Available: {status_data.get('current_ally') is not None}")
    
    # Test attack action
    print("\n4. Testing attack action...")
    
    # First attack - use ally if available
    use_ally = status_data.get('current_ally') is not None
    
    attack_response = requests.post(f"{BASE_URL}/player/attack",
                                  json={
                                      "session_id": session_id,
                                      "action": "attack",
                                      "use_ally": use_ally
                                  })
    
    if attack_response.status_code != 200:
        print(f"❌ Attack failed: {attack_response.text}")
        return False
    
    attack_data = attack_response.json()['data']
    print(f"✅ Attack executed!")
    
    if 'battle_log' in attack_data:
        for log_entry in attack_data['battle_log']:
            print(f"   📜 {log_entry.get('description', 'Action occurred')}")
    
    print(f"   Player Health: {attack_data['player_health']}")
    print(f"   Enemy Health: {attack_data['enemy_health']}")
    print(f"   Battle Ended: {attack_data.get('battle_ended', False)}")
    
    # Continue battle until it ends or we reach max turns
    turn_count = 1
    max_turns = 20
    
    while not attack_data.get('battle_ended') and turn_count < max_turns:
        print(f"\n   Turn {turn_count + 1}...")
        
        # Continue attacking
        attack_response = requests.post(f"{BASE_URL}/player/attack",
                                      json={
                                          "session_id": session_id,
                                          "action": "attack",
                                          "use_ally": False  # Ally should be used up after first attack
                                      })
        
        if attack_response.status_code != 200:
            print(f"❌ Attack failed: {attack_response.text}")
            break
        
        attack_data = attack_response.json()['data']
        
        if 'battle_log' in attack_data:
            for log_entry in attack_data['battle_log']:
                print(f"      📜 {log_entry.get('description', 'Action occurred')}")
        
        print(f"      Player Health: {attack_data['player_health']}")
        print(f"      Enemy Health: {attack_data['enemy_health']}")
        
        turn_count += 1
        time.sleep(0.5)
    
    if attack_data.get('battle_ended'):
        if attack_data.get('victory'):
            print(f"🎉 Victory! Player won the battle!")
            if 'reward' in attack_data:
                print(f"   💰 Reward: {attack_data['reward']}")
        else:
            print(f"💀 Defeat! Player lost the battle!")
    else:
        print(f"⏰ Battle didn't end within {max_turns} turns")
    
    print("\n5. Testing flee action...")
    
    # Move to find another battle to test flee
    for i in range(5):
        direction = directions[i % len(directions)]
        
        move_response = requests.post(f"{BASE_URL}/player/move",
                                    json={"session_id": session_id, "direction": direction})
        
        if move_response.status_code != 200:
            continue
        
        move_data = move_response.json()['data']
        
        if move_data.get('encounter_occurred'):
            print(f"⚔️  New battle started for flee test!")
            
            # Test flee
            flee_response = requests.post(f"{BASE_URL}/player/attack",
                                        json={
                                            "session_id": session_id,
                                            "action": "flee"
                                        })
            
            if flee_response.status_code == 200:
                flee_data = flee_response.json()['data']
                print(f"🏃 Fled from battle!")
                print(f"   💰 Gold lost: {flee_data.get('gold_lost', 0)}")
                print(f"   💰 Current gold: {flee_data.get('current_gold', 0)}")
            else:
                print(f"❌ Flee failed: {flee_response.text}")
            
            break
        
        time.sleep(0.5)
    
    print("\n✅ Turn-based combat system test completed!")
    return True


if __name__ == "__main__":
    try:
        success = test_turn_based_combat()
        if success:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")