"""
Demonstration script for the inventory system.
Shows item finding, storage, and usage in action.
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import Player, Enemy, Item
from app.controllers import InventoryController

def print_separator():
    print("\n" + "=" * 70 + "\n")

def demonstrate_inventory_system():
    """Demonstrate the full inventory system."""
    
    print("🎮 ABYSSAL INVADERS - INVENTORY SYSTEM DEMONSTRATION")
    print_separator()
    
    # Create player and controller
    player = Player(name="Demo Hero")
    controller = InventoryController()
    
    print(f"Player: {player.name}")
    print(f"Starting Health: {player.health}/{player.max_health}")
    print(f"Starting Gold: {player.gold}")
    print(f"Starting Inventory: {len(player.inventory)} items")
    
    print_separator()
    print("📦 SCENARIO 1: Finding Items During Exploration")
    print_separator()
    
    # Simulate finding items in multiple rooms
    items_found = []
    for floor in [1, 1, 3, 5]:
        found, item = controller.roll_for_item_find(player, room_visited=False)
        if found:
            controller.add_item_to_inventory(player, item)
            items_found.append(item)
            print(f"✓ Floor {floor}: Found {item.name} ({item.rarity})")
            print(f"  └─ {item.description}")
    
    print(f"\nTotal items found: {len(items_found)}")
    print(f"Current inventory size: {len(player.inventory)}")
    
    print_separator()
    print("🎒 SCENARIO 2: Viewing Inventory")
    print_separator()
    
    result = controller.get_inventory(player)
    print(f"Inventory contains {result['data']['total_items']} items:")
    for item_info in result['data']['inventory']:
        print(f"  • {item_info['name']} ({item_info['rarity']})")
        print(f"    └─ {item_info['description']}")
        print(f"    └─ Effect: {item_info['effect_type']} ({item_info['effect_value']})")
        print(f"    └─ Combat use: {'Yes' if item_info['usable_in_combat'] else 'No'}")
    
    print_separator()
    print("💊 SCENARIO 3: Using a Healing Potion")
    print_separator()
    
    # Damage the player
    player.health = 40
    print(f"Player takes damage! Health: {player.health}/{player.max_health}")
    
    # Find and use a health potion
    health_potion = Item('health_potion')
    player.add_item(health_potion)
    print(f"\nFound {health_potion.name}!")
    print(f"Current inventory: {len(player.inventory)} items")
    
    # Use the potion
    success, result = controller.use_item(player, health_potion.item_id)
    if success:
        print(f"\n✓ Used {health_potion.name}!")
        print(f"  └─ {result['data']['use_result']['message']}")
        print(f"  └─ New health: {player.health}/{player.max_health}")
        print(f"  └─ Inventory: {len(player.inventory)} items (potion consumed)")
    
    print_separator()
    print("⚔️ SCENARIO 4: Using Items in Combat")
    print_separator()
    
    # Create an enemy
    enemy = Enemy(name="Shadow Fiend", description="A dark creature", floor=3)
    enemy.defense = 0  # For demo purposes
    player.in_battle = True
    
    print(f"Entered battle with {enemy.name}!")
    print(f"Enemy Health: {enemy.health}/{enemy.max_health}")
    print(f"Enemy Attack: {enemy.attack_power}")
    
    # Add and use an attack boost
    attack_boost = Item('attack_boost')
    player.add_item(attack_boost)
    print(f"\nUsing {attack_boost.name}...")
    success, result = controller.use_item(player, attack_boost.item_id)
    if success:
        print(f"✓ {result['data']['use_result']['message']}")
        print(f"  └─ New attack power: {player.attack_power}")
    
    # Add and use a damage bomb
    bomb = Item('damage_bomb')
    player.add_item(bomb)
    print(f"\nUsing {bomb.name} on enemy...")
    success, result = controller.use_item(player, bomb.item_id, enemy)
    if success:
        print(f"✓ {result['data']['use_result']['message']}")
        print(f"  └─ Enemy health: {enemy.health}/{enemy.max_health}")
    
    print_separator()
    print("🗑️ SCENARIO 5: Discarding Items")
    print_separator()
    
    # Add an item to discard
    gold_bag = Item('gold_coin_bag')
    player.add_item(gold_bag)
    print(f"Found {gold_bag.name}")
    print(f"Inventory before discard: {len(player.inventory)} items")
    
    # Discard it
    success, result = controller.discard_item(player, gold_bag.item_id)
    if success:
        print(f"\n✓ Discarded {gold_bag.name}")
        print(f"Inventory after discard: {len(player.inventory)} items")
    
    print_separator()
    print("🏆 SCENARIO 6: Item Rarity Distribution by Floor")
    print_separator()
    
    # Test rarity distribution across floors
    print("Testing item rarity across different floors...")
    print("(Rolling 20 times per floor)")
    
    for floor in [1, 5, 10]:
        rarities = {'common': 0, 'uncommon': 0, 'rare': 0}
        for _ in range(20):
            item_type = Item.get_random_item_type(floor)
            item = Item(item_type)
            rarities[item.rarity] += 1
        
        print(f"\nFloor {floor}:")
        print(f"  Common: {rarities['common']}/20 ({rarities['common']*5}%)")
        print(f"  Uncommon: {rarities['uncommon']}/20 ({rarities['uncommon']*5}%)")
        print(f"  Rare: {rarities['rare']}/20 ({rarities['rare']*5}%)")
    
    print_separator()
    print("📊 FINAL STATISTICS")
    print_separator()
    
    print(f"Player: {player.name}")
    print(f"Final Health: {player.health}/{player.max_health}")
    print(f"Final Attack Power: {player.attack_power}")
    print(f"Final Defense: {player.defense}")
    print(f"Final Gold: {player.gold}")
    print(f"Final Inventory: {len(player.inventory)} items")
    
    if player.inventory:
        print("\nRemaining items:")
        for item in player.inventory:
            print(f"  • {item.name}")
    
    print_separator()
    print("✅ DEMONSTRATION COMPLETE!")
    print("\nThe inventory system is fully functional with:")
    print("  • Item finding during exploration")
    print("  • 8 different item types across 3 rarity tiers")
    print("  • Combat and exploration item usage")
    print("  • Inventory management (view, use, discard)")
    print("  • Floor-based rarity scaling")
    print("  • Full serialization support")
    print_separator()


if __name__ == '__main__':
    demonstrate_inventory_system()
