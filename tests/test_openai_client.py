"""
Test functions for OpenAI client functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.openai_client import OpenAIClient, create_openai_client, is_openai_configured


def test_openai_connection():
    """Test basic OpenAI API connection."""
    print("Testing OpenAI connection...")
    
    if not is_openai_configured():
        print("❌ OpenAI not configured. Please set OPENAI_API_KEY in .env file")
        return False
    
    try:
        client = create_openai_client()
        if not client:
            print("❌ Failed to create OpenAI client")
            return False
        
        print("✅ OpenAI client created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating OpenAI client: {e}")
        return False


def test_generate_enemy_content():
    """Test enemy content generation."""
    print("\nTesting enemy content generation...")
    
    client = create_openai_client()
    if not client:
        print("❌ No OpenAI client available")
        return False
    
    try:
        enemy_data = client.generate_enemy_content(
            floor=2, 
            room_description="Dark Crystal Cavern"
        )
        
        print(f"Generated Enemy:")
        print(f"  Name: {enemy_data.get('name', 'N/A')}")
        print(f"  Description: {enemy_data.get('description', 'N/A')}")
        
        # Validate structure
        if 'name' in enemy_data and 'description' in enemy_data:
            print("✅ Enemy content generation successful")
            return True
        else:
            print("❌ Invalid enemy content structure")
            return False
            
    except Exception as e:
        print(f"❌ Error generating enemy content: {e}")
        return False


def test_generate_ally_content():
    """Test ally content generation."""
    print("\nTesting ally content generation...")
    
    client = create_openai_client()
    if not client:
        print("❌ No OpenAI client available")
        return False
    
    try:
        ally_data = client.generate_ally_content(
            floor=3,
            room_description="Ancient Library"
        )
        
        print(f"Generated Ally:")
        print(f"  Name: {ally_data.get('name', 'N/A')}")
        print(f"  Description: {ally_data.get('description', 'N/A')}")
        
        # Validate structure
        if 'name' in ally_data and 'description' in ally_data:
            print("✅ Ally content generation successful")
            return True
        else:
            print("❌ Invalid ally content structure")
            return False
            
    except Exception as e:
        print(f"❌ Error generating ally content: {e}")
        return False


def test_generate_room_content():
    """Test room content generation."""
    print("\nTesting room content generation...")
    
    client = create_openai_client()
    if not client:
        print("❌ No OpenAI client available")
        return False
    
    try:
        room_data = client.generate_room_content(floor=1, room_type="chamber")
        
        print(f"Generated Room:")
        print(f"  Name: {room_data.get('name', 'N/A')}")
        print(f"  Description: {room_data.get('description', 'N/A')}")
        
        # Validate structure
        if 'name' in room_data and 'description' in room_data:
            print("✅ Room content generation successful")
            return True
        else:
            print("❌ Invalid room content structure")
            return False
            
    except Exception as e:
        print(f"❌ Error generating room content: {e}")
        return False


def test_generate_combat_description():
    """Test combat description generation."""
    print("\nTesting combat description generation...")
    
    client = create_openai_client()
    if not client:
        print("❌ No OpenAI client available")
        return False
    
    try:
        description = client.generate_combat_description(
            player_name="Hero",
            enemy_name="Shadow Beast",
            room_name="Dark Sanctum",
            action="encounter"
        )
        
        print(f"Generated Combat Description:")
        print(f"  {description}")
        
        if description and len(description) > 10:
            print("✅ Combat description generation successful")
            return True
        else:
            print("❌ Invalid combat description")
            return False
            
    except Exception as e:
        print(f"❌ Error generating combat description: {e}")
        return False


def test_fallback_behavior():
    """Test fallback behavior when OpenAI is not available."""
    print("\nTesting fallback behavior...")
    
    # Test with invalid client
    try:
        # Create client with invalid API key temporarily
        original_key = os.environ.get('OPENAI_API_KEY')
        os.environ['OPENAI_API_KEY'] = 'invalid_key_for_testing'
        
        client = OpenAIClient()
        enemy_data = client.generate_enemy_content(floor=1)
        
        # Should get fallback data
        if 'name' in enemy_data and 'description' in enemy_data:
            print("✅ Fallback behavior working correctly")
            result = True
        else:
            print("❌ Fallback behavior failed")
            result = False
        
        # Restore original key
        if original_key:
            os.environ['OPENAI_API_KEY'] = original_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
            
        return result
        
    except Exception as e:
        print(f"❌ Error testing fallback behavior: {e}")
        return False


def run_all_tests():
    """Run all OpenAI client tests."""
    print("=" * 50)
    print("Running OpenAI Client Tests")
    print("=" * 50)
    
    tests = [
        test_openai_connection,
        test_generate_enemy_content,
        test_generate_ally_content,
        test_generate_room_content,
        test_generate_combat_description,
        test_fallback_behavior
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_func, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test_func.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    run_all_tests()