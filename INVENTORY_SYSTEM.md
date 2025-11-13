# Inventory System Documentation

## Overview

The inventory system allows players to find, store, and use various items throughout their dungeon exploration. Items can provide healing, combat buffs, direct damage, or other utility benefits.

## Key Features

- **High Find Rate**: 65% chance to find items when entering new rooms (when no encounter occurs)
- **No Duplicates in Visited Rooms**: Items only appear in rooms the player hasn't visited before
- **Unlimited Storage**: Players can carry as many items as they find
- **Single-Use Consumables**: All items are consumed upon use
- **Combat & Exploration Items**: Some items can be used any time, others only during combat

## Item Types

### Healing Items
| Item | Rarity | Effect | Usable in Combat |
|------|--------|--------|------------------|
| Health Potion | Common | Restores 30 HP | Yes |
| Greater Health Potion | Uncommon | Restores 60 HP | Yes |

### Combat Buffs
| Item | Rarity | Effect | Usable in Combat |
|------|--------|--------|------------------|
| Attack Elixir | Uncommon | +15 Attack Power (one battle) | Yes |
| Iron Skin Tonic | Uncommon | +10 Defense (one battle) | Yes |

### Offensive Items
| Item | Rarity | Effect | Usable in Combat |
|------|--------|--------|------------------|
| Explosive Bomb | Rare | Deals 40 damage to enemy | Yes |
| Poison Vial | Uncommon | Deals 25 damage to enemy | Yes |

### Utility Items
| Item | Rarity | Effect | Usable in Combat |
|------|--------|--------|------------------|
| Scroll of Escape | Rare | Guarantees successful flee | Yes |
| Bag of Gold Coins | Common | Grants 50 gold | No |

## Rarity System

Items have three rarity tiers:
- **Common**: More frequent at lower floors
- **Uncommon**: Moderate frequency, scales with floor level
- **Rare**: Increases significantly with floor level

The rarity distribution adjusts dynamically based on the current floor, making rare items more common in deeper dungeon levels.

## API Endpoints

### View Inventory
```http
POST /api/inventory/view
Content-Type: application/json

{
  "session_id": "player-session-id"
}
```

Returns:
- List of all items in inventory
- Grouped inventory (items organized by type)
- Total item count

### Use Item
```http
POST /api/inventory/use
Content-Type: application/json

{
  "session_id": "player-session-id",
  "item_id": "item-uuid"
}
```

Uses the specified item and applies its effect. The item is removed from inventory after use.

### Discard Item
```http
POST /api/inventory/discard
Content-Type: application/json

{
  "session_id": "player-session-id",
  "item_id": "item-uuid"
}
```

Removes the item from inventory without using it.

## Game Flow Integration

### Item Finding
1. Player moves to a new room
2. System checks for enemy encounter first
3. If no encounter occurs, system rolls for item find (65% chance)
4. If successful, a random item is generated based on floor level
5. Item is automatically added to player's inventory
6. Player is notified of the find in the move response

### Item Usage
1. Player can view inventory at any time
2. Player selects an item to use by its ID
3. System validates:
   - Item exists in inventory
   - Item can be used in current context (combat vs. exploration)
   - Required targets are available (e.g., enemy for damage items)
4. Item effect is applied immediately
5. Item is removed from inventory
6. Player and enemy stats are updated and saved

## Code Structure

### Models
- **`app/models/item.py`**: Item class with all item types and effects
- **`app/models/player.py`**: Player model extended with inventory field

### Controllers
- **`app/controllers/inventory.py`**: InventoryController handles all inventory operations

### Routes
- **`app/routes.py`**: Three inventory endpoints (view, use, discard)

### Tests
- **`tests/test_inventory.py`**: Comprehensive unit tests covering:
  - Item creation and properties
  - Player inventory management
  - Inventory controller operations
  - Full integration scenarios

## Testing

Run the inventory system tests:
```bash
python -m unittest tests.test_inventory -v
```

This runs 32 test cases covering:
- Item model functionality (16 tests)
- Player inventory operations (6 tests)
- Inventory controller logic (9 tests)
- Integration scenarios (3 tests)

## Future Enhancements

Potential additions to the inventory system:
- Item crafting/combining
- Stackable items (multiple of the same type)
- Equipment slots (weapons, armor)
- Item durability
- Trading system
- Item shops
- Quest items
- Multi-use items with charges
