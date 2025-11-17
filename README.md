# Abyssal Invaders - Dungeon Crawler Game

A Python Flask-based dungeon crawler game with a web-based frontend and REST API. Players explore procedurally generated dungeons, fight enemies with elemental combat and status effects, recruit allies, manage inventory, shop for items, gamble at casinos, and compete for high scores in a Rocket Software office building transformed into a monster-filled labyrinth.

## Features

### Core Gameplay
- **Web-based frontend** - Fully interactive browser-based UI with real-time updates
- **Session-based gameplay** - Each player has a unique session ID for persistent progress
- **Procedural dungeon generation** - Rooms are generated dynamically with random connections
- **Bi-directional navigation** - Explore freely and backtrack through visited rooms
- **Progressive difficulty** - Enemies scale with floor depth

### Combat System
- **Turn-based tactical combat** - Strategic attack/flee decisions with turn order
- **Elemental system** - Fire, Water, Earth, Air, Light, and Dark elements with strengths/weaknesses
- **Status effects** - Burn, Poison, Stun, Freeze, Bleed, Regen with turn-based durations
- **Ally support** - Recruit powerful allies for one-time devastating attacks
- **Enemy variety** - 70+ unique enemy types with custom sprites and abilities

### Inventory & Items
- **Dynamic inventory system** - Collect, use, and discard items
- **Multiple item types** - Healing potions, combat buffs, offensive items, utility scrolls
- **Rarity tiers** - Common, Uncommon, Rare, Epic, and Legendary items
- **Cursed items** - Risk/reward items with permanent negative effects

### Shops & Economy
- **Shop rooms** - Purchase healing potions, combat elixirs, and rare items
- **Gold currency** - Earn gold through combat, exploration, and item use
- **Dynamic pricing** - Item costs scale with rarity and floor level

### Casino System
- **Casino rooms** - Gamble your gold in the Lucky Dice Casino
- **Blackjack** - Full-featured blackjack with split and double down mechanics
- **Split hands** - Split matching cards and play two hands simultaneously
- **Double down** - Risk it all for double the reward

### Character Customization
- **Player sprites** - Choose from multiple character appearances
- **Level progression** - Gain experience and level up for stat increases
- **Stat system** - Health, Attack, Defense, Speed with dynamic scaling

### Persistence & Leaderboard
- **Save/Load system** - Continue your adventure across sessions
- **High score leaderboard** - Compete based on gold, floors cleared, and enemies defeated
- **File-based database** - JSON storage for easy backup and portability

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Virtual environment support

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/RocketCamEvans/Abyssal-Invaders.git
   cd Abyssal-Invaders
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**
   ```bash
   python run.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000` to start playing!

The game frontend will be served at `http://localhost:5000` with the API available at `http://localhost:5000/api`

## API Endpoints

### Player Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/player/new` | Create new player session with story intro |
| `POST` | `/api/player/status` | Get current player status |
| `POST` | `/api/player/look` | Get detailed room information |
| `POST` | `/api/player/move` | Move player in a direction |
| `POST` | `/api/player/stats` | Get detailed player statistics |
| `POST` | `/api/player/load` | Load existing player session |
| `POST` | `/api/player/heal` | Heal player (costs gold) |
| `POST` | `/api/player/delete` | Delete player session |

### Combat System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/player/attack` | Initiate or continue combat |
| `POST` | `/api/combat/attack` | Attack current enemy |
| `POST` | `/api/combat/flee` | Attempt to flee from combat |
| `POST` | `/api/player/fire-ally` | Use ally's special attack |

### Inventory System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/inventory/view` | View player's inventory |
| `POST` | `/api/inventory/use` | Use an item from inventory |
| `POST` | `/api/inventory/discard` | Discard an item from inventory |

### Shop System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/shop/view` | View shop inventory and prices |
| `POST` | `/api/shop/purchase` | Purchase an item from shop |

### Casino System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/casino/enter` | Enter the casino |
| `POST` | `/api/casino/blackjack/start` | Start a blackjack game |
| `POST` | `/api/casino/blackjack/hit` | Draw a card |
| `POST` | `/api/casino/blackjack/stand` | End turn and let dealer play |
| `POST` | `/api/casino/blackjack/split` | Split matching cards into two hands |
| `POST` | `/api/casino/blackjack/double` | Double bet, draw one card, and stand |

### Scoring & Leaderboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/scores/highscores` | Get leaderboard with top players |
| `POST` | `/api/scores/submit` | Submit final score on death |

### Sprites & Assets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/sprites/enemy/<name>` | Get enemy sprite image |
| `GET` | `/api/sprites/player/<name>` | Get player sprite image |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Basic health check |
| `POST` | `/api/debug/staircases` | Debug endpoint for staircase info |

## Example Usage

### 1. Create a New Player

```bash
curl -X POST http://localhost:5000/api/player/new \
  -H "Content-Type: application/json" \
  -d '{"name": "Hero McHeroface"}'
```

Response:
```json
{
  "error": false,
  "message": "Welcome, Hero McHeroface! Your adventure begins.",
  "data": {
    "session_id": "12345678-1234-1234-1234-123456789012",
    "player": {
      "name": "Hero McHeroface",
      "health": "100/100",
      "gold": 0,
      "floor": 1,
      "room_id": "start"
    },
    "current_room": {
      "room_id": "start",
      "name": "Floor 1 Entrance",
      "description": "You find yourself at the entrance to floor 1...",
      "floor": 1,
      "available_directions": ["north", "east"],
      "has_staircase": false
    }
  }
}
```

### 2. Move the Player

```bash
curl -X POST http://localhost:5000/api/player/move \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "12345678-1234-1234-1234-123456789012",
    "direction": "north"
  }'
```

### 3. View Inventory

```bash
curl -X POST http://localhost:5000/api/inventory/view \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "12345678-1234-1234-1234-123456789012"
  }'
```

Response:
```json
{
  "error": false,
  "message": "Inventory retrieved",
  "data": {
    "inventory": [
      {
        "item_id": "abc123-...",
        "name": "Health Potion",
        "description": "Restores health when used",
        "effect_type": "heal",
        "effect_value": 30,
        "usable_in_combat": true,
        "rarity": "common"
      }
    ],
    "inventory_size": 1,
    "total_items": 1
  }
}
```

### 4. Use an Item

```bash
curl -X POST http://localhost:5000/api/inventory/use \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "12345678-1234-1234-1234-123456789012",
    "item_id": "abc123-..."
  }'
```

### 5. Get High Scores

```bash
curl http://localhost:5000/api/scores/highscores
```

## Game Mechanics

### Movement & Exploration
- Players can move **north**, **south**, **east**, **west** between connected rooms
- Use **up** to climb staircases to the next floor
- Each room has 1-3 random connections to other rooms
- **Bidirectional movement** - freely backtrack through visited rooms
- **Room features**: Shops (60% spawn), Casinos (40% spawn), Staircases, Allies
- Moving to new rooms awards exploration gold
- Audio cues hint at nearby features (shop music, casino sounds, ally voices)

### Combat System
- **Turn-based combat** with speed-based turn order
- **Elemental strengths/weaknesses**:
  - Fire beats Earth, Earth beats Air, Air beats Fire
  - Water beats Fire, Fire beats Water (mutual)
  - Light beats Dark, Dark beats Light (mutual)
- **Status effects**: Burn, Poison, Freeze, Stun, Bleed, Regen
- **Encounter chance** scales with floor level (30% base)
- **Flee mechanic** - 50-80% success rate based on current health percentage
- **Victory rewards** - Gold, experience, and occasional item drops
- **Death penalty** - Game over with score submission to leaderboard

### Inventory System
- **Dynamic item discovery** - Find items when entering new rooms (no encounters)
- Items are **not found in previously visited rooms**
- Items automatically added to inventory upon finding
- **Unlimited carrying capacity**
- Items can be used during or outside of combat (type-dependent)
- **Single-use consumables** - Items consumed upon use
- Discard unwanted items at any time

#### Item Types & Rarity

**Healing Items:**
- **Health Potion** (Common) - Restores 30 HP
- **Greater Health Potion** (Uncommon) - Restores 60 HP
- **Superior Health Potion** (Rare) - Restores 100 HP
- **Ultimate Elixir** (Epic) - Restores full HP

**Combat Buffs:**
- **Attack Elixir** (Uncommon) - +15 attack for one battle
- **Iron Skin Tonic** (Uncommon) - +10 defense for one battle
- **Berserker's Brew** (Rare) - +30 attack, -5 defense
- **Titan's Fortitude** (Epic) - +20 defense, +50 max HP

**Offensive Items:**
- **Explosive Bomb** (Rare) - Deals 40 direct damage
- **Poison Vial** (Uncommon) - Deals 25 damage + poison
- **Elemental Scroll** (Rare) - Deals 50 elemental damage
- **Divine Strike** (Legendary) - Deals 100 holy damage

**Utility Items:**
- **Scroll of Escape** (Rare) - Guarantees successful flee
- **Bag of Gold Coins** (Common) - Grants 50 gold
- **Lucky Charm** (Uncommon) - Increases item find chance
- **Treasure Map** (Rare) - Reveals nearby rooms

**Cursed Items:**
- **Cursed Ring** - +20 attack, -10 max HP permanently
- **Vampire's Chalice** - Heal on hit, but take burn damage
- **Dark Pact** - Double gold, but increased encounter rate

**Rarity Distribution:** Higher floors dramatically increase chances of rare, epic, and legendary items.

### Shop System
- **Shop rooms** spawn on 60% of floors
- Purchase items with gold:
  - **Minor Health Potion** - 20 gold
  - **Health Potion** - 50 gold
  - **Greater Health Potion** - 100 gold
  - **Attack Elixir** - 75 gold
  - **Iron Skin Tonic** - 75 gold
  - **Scroll of Escape** - 150 gold
- Items can only be purchased once per shop
- Shops persist across visits to the same floor

### Casino System
- **Casino rooms** spawn on 40% of floors
- **Blackjack gameplay**:
  - Bet any amount of gold (up to your total)
  - Standard blackjack rules: Hit, Stand, Split, Double Down
  - **Split** - Split matching cards into two hands (requires additional bet)
  - **Double Down** - Double your bet, draw one card, auto-stand
  - Dealer hits until 17+
  - Blackjack pays 2.5x, regular win pays 2x
  - Push returns your bet
- Strategic gambling can multiply your wealth or bankrupt you

### Progression & Leveling
- **Experience points** earned from defeating enemies
- **Level up** system with stat increases per level
- **Gold** is the primary scoring metric
- **Floors** increase in difficulty exponentially
- **Staircases** appear randomly to access deeper floors
- **Enemy scaling** - Stats, elements, and status effects scale with floor

### Allies
- Found randomly during exploration
- Each ally provides **one powerful attack** per battle
- Ally types: Healer, Tank, DPS, Support
- **Ally strength scales** with current floor level
- Multiple allies can be recruited and used strategically
- Allies reset their "used" status at the start of each new battle

## Project Structure

```
Abyssal-Invaders/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── routes.py                # Main API endpoints
│   ├── dev_routes.py            # Development/debug endpoints
│   ├── routes_sprites.py        # Sprite serving endpoints
│   ├── controllers/             # Game logic controllers
│   │   ├── blackjack.py         # Casino blackjack logic
│   │   ├── combat.py            # Combat system with elements/ailments
│   │   ├── generation.py        # Content generation
│   │   ├── inventory.py         # Inventory management
│   │   ├── movement.py          # Room generation & navigation
│   │   └── scoring.py           # Leaderboard system
│   ├── models/                  # Data model classes
│   │   ├── player.py            # Player character
│   │   ├── enemy.py             # Enemy entities
│   │   ├── ally.py              # Ally NPCs
│   │   ├── item.py              # Item system
│   │   ├── room.py              # Room/dungeon structure
│   │   ├── element.py           # Elemental types
│   │   ├── ailment.py           # Status effects
│   │   └── request_models.py    # API request validation
│   ├── utils/                   # Helper utilities
│   │   ├── file_db.py           # JSON database
│   │   ├── helpers.py           # Utility functions
│   │   └── sprite_matcher.py    # Sprite assignment logic
│   ├── frontend/                # Web UI
│   │   ├── index.html           # Main game interface
│   │   ├── game.js              # Game client logic
│   │   ├── dev-panel.js         # Developer panel
│   │   └── styles.css           # Game styling
│   ├── sprites/                 # Character & enemy images
│   └── templates/               # HTML templates
├── data/                        # JSON data storage
│   ├── users.json               # Player save data
│   └── rooms.json               # Room state data
├── tests/                       # Unit tests
├── utils/                       # External utilities
│   ├── openai_client.py         # LLM integration
│   └── llm_logger.py            # LLM logging
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
├── README.md                    # This file
└── DEV_MODE.md                  # Developer documentation
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test modules
python -m unittest tests.test_routes
python -m unittest tests.test_combat
python -m unittest tests.test_inventory
python -m unittest tests.test_movement
python -m unittest tests.test_turn_based_combat

# Run demonstration scripts
python demo_inventory.py
python test_backtracking.py
```

### Development Mode

Enable developer mode for debugging and testing features:

1. Access dev panel at `http://localhost:5000/dev`
2. Features include:
   - God mode (invincibility)
   - Instant floor skip
   - Gold/XP manipulation
   - Force enemy encounters
   - Clear save data
   - View game state

See `DEV_MODE.md` for full documentation.

### Configuration

Environment variables (`.env` file):
- `FLASK_ENV` - Set to 'production' for production mode
- `FLASK_HOST` - Server host (default: 127.0.0.1)
- `FLASK_PORT` - Server port (default: 5000)
- `FLASK_DEBUG` - Enable debug mode (default: True)
- `DATA_DIR` - Directory for JSON data files (default: ./data)
- `SECRET_KEY` - Flask secret key for sessions
- `OPENAI_API_KEY` - OpenAI API key for LLM generation

### LLM Integration

The game includes OpenAI integration for dynamic content generation:

- **Enemy generation** - Names, descriptions, and flavor text
- **Room descriptions** - Dynamic environment descriptions
- **Ally generation** - Unique ally characters
- **Combat narration** - Engaging battle text

Configure in `utils/openai_client.py` with your API key.

## Architecture & Design

### Frontend Architecture
- **Single-page application** - Dynamic DOM updates without page reloads
- **Event-driven UI** - Responsive button states and animations
- **API client** - Async request handling with error management
- **State management** - Client-side game state synchronization
- **CSS animations** - Smooth transitions for combat, damage, healing

### Backend Architecture
- **Flask REST API** - Clean separation of frontend and backend
- **Controller pattern** - Business logic isolated from routes
- **Model classes** - Structured data with serialization methods
- **Stateless design** - All game state persisted in database

### Session Management
- **UUID-based sessions** - Unique identifier per player
- **Cookie-based tracking** - Automatic session management
- **Persistent storage** - Save/load across server restarts

### Data Persistence
- **File-based JSON storage** - Simple and portable
- **Separate files** - `users.json` for players, `rooms.json` for dungeon state
- **Serialization** - All models have `to_dict()` and `from_dict()` methods
- **Migration ready** - Easy to swap for PostgreSQL, MongoDB, etc.

### Combat System Design
- **Turn-based mechanics** - Speed stat determines turn order
- **Elemental matrix** - Rock-paper-scissors style strengths
- **Status effect stack** - Multiple ailments can apply simultaneously
- **Damage calculation** - Attack, defense, element modifiers, and status effects

### Scalability Considerations
- **Modular controllers** - Easy to extend with new features
- **Sprite system** - Dynamic image serving and matching
- **Session isolation** - Each player's rooms stored separately
- **Extensible models** - Clean class hierarchy for new content types

## Recent Updates

### Latest: Casino & Blackjack System (v2.0)
- **Casino Rooms**: 40% spawn rate on floors with full blackjack gambling
- **Blackjack Features**:
  - Standard Hit/Stand mechanics
  - **Split**: Split matching cards into two hands
  - **Double Down**: Risk double the bet for one final card
  - Proper dealer AI (hits until 17)
  - Blackjack pays 2.5x, regular win pays 2x
- **Split Hand Mechanics**: Play two hands sequentially with independent outcomes
- **Gold Management**: Bet any amount, win big or lose it all

### Elemental Combat & Status Effects (v1.8)
- **Element System**: Fire, Water, Earth, Air, Light, Dark with strengths/weaknesses
- **Ailments**: Burn, Poison, Freeze, Stun, Bleed, Regen with turn durations
- **Enemy Diversity**: 70+ unique enemies with sprites and elemental affinities
- **Combat Balance**: Speed-based turn order and damage calculations

### Shop System & Economy (v1.5)
- **Shop Rooms**: 60% spawn rate with purchasable items
- **Dynamic Pricing**: Gold costs scale with item rarity
- **One-time Purchases**: Items can only be bought once per shop
- **Strategic Economy**: Balance gold spending between shops, casinos, and healing

### Inventory & Item System (v1.2)
- **Comprehensive Item Types**: Healing, buffs, offensive, utility, cursed
- **Rarity Tiers**: Common to Legendary with floor-based drop rates
- **Cursed Items**: High-risk, high-reward permanent effects
- **Item Management**: View, use, discard with full API support

### Core Fixes & Improvements
- **Bidirectional Navigation**: Full backtracking through visited rooms
- **Room ID System**: Clean, simple room identifiers
- **Ally Persistence**: Allies properly reset between battles
- **Turn-Based Combat**: Proper speed-based turn order
- **Sprite System**: Dynamic enemy and player sprite matching

## Game Story

The day started like any other at **Rocket Software's headquarters**. Developers typed away at their keyboards, coffee machines hummed in break rooms, and the fluorescent lights buzzed overhead. But then, without warning, a black SUV screeched to a halt outside the building.

An **evil wizard** emerged, staff crackling with dark energy. With a wave of his gnarled hand and a muttered incantation, reality itself bent and twisted. The building groaned and shifted—hallways stretched into impossible corridors, conference rooms became monster-infested chambers, and the elevator shafts descended into endless darkness.

**Rocket Software had become an infinite labyrinth of horrors.**

But the employees were not defenseless. As the curse took hold, something awakened within them—ancient powers of fantasy and legend. Programmers found themselves wielding swords of pure code. Project managers commanded arcane shields. Even the interns discovered they could cast healing spells.

Now, you and your fellow employees must fight through the cursed floors, battling office-dwelling monsters and twisted creatures of corporate nightmare. Your mission: **reclaim Rocket Software, defeat the wizard's minions, and restore the building to normal.**

**The labyrinth awaits. Steel yourself, brave employee. Your adventure begins now!**

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow existing code structure and patterns
4. Add unit tests for new features
5. Update documentation for significant changes
6. Use type hints and docstrings for new functions
7. Submit a pull request

## Credits

**Development Team:**
- Game design and core systems
- Combat mechanics and balancing
- Frontend UI and animations
- Sprite integration and asset management

**Special Thanks:**
- Rocket Software for the game's setting and inspiration
- OpenAI for LLM content generation support
- The Python Flask community

## License

This project is provided as-is for educational and development purposes.

---

## Quick Links

- 📖 [Full API Documentation](./API_DOCUMENTATION.md) *(if exists)*
- 🎮 [Developer Mode Guide](./DEV_MODE.md)
- 🧪 [Testing Guide](./TESTING.md)
- ⚔️ [Combat System Details](./TURN_BASED_COMBAT_SUMMARY.md)
- 🎒 [Inventory System Details](./INVENTORY_SYSTEM.md)

---

**Ready to explore the abyss?** Start the server and reclaim Rocket Software from the forces of darkness!