# Abyssal Invaders - Dungeon Crawler API

A Python Flask-based dungeon crawler game with REST API endpoints. Players explore procedurally generated dungeons, fight enemies, recruit allies, and compete for high scores.

## Features

- **Session-based gameplay** - Each player has a unique session ID tracked via cookies
- **Procedural dungeon generation** - Rooms are generated dynamically with random connections
- **Turn-based combat system** - Fight enemies with attack/flee options
- **Ally recruitment** - Find and recruit allies for one-time powerful attacks
- **Progressive difficulty** - Enemies get stronger as you go deeper
- **High score leaderboard** - Compete based on gold earned
- **LLM-ready content generation** - Structured for AI-generated names and descriptions
- **File-based persistence** - JSON database for user data and game state

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Virtual environment support

### Installation

1. **Clone or extract the project**
   ```bash
   cd dungeon_crawler_api
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

The API will be available at `http://localhost:5000`

## API Endpoints

### Player Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/player/new` | Create new player session |
| `POST` | `/api/player/status` | Get current player status |
| `POST` | `/api/player/move` | Move player in a direction |
| `POST` | `/api/player/stats` | Get detailed player statistics |
| `POST` | `/api/player/delete` | Delete player session |

### Combat System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/combat/attack` | Attack an enemy |
| `POST` | `/api/combat/use_ally` | Use ally's attack |
| `POST` | `/api/combat/flee` | Attempt to flee from combat |

### Encounters & Scoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/encounter/ally` | Encounter a helpful ally |
| `GET` | `/api/scores/highscores` | Get leaderboard |
| `POST` | `/api/scores/submit` | Submit final score |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Basic health check |
| `GET` | `/api/health/detailed` | Detailed system status |

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

### 3. Get High Scores

```bash
curl http://localhost:5000/api/scores/highscores
```

## Game Mechanics

### Movement
- Players can move **north**, **south**, **east**, **west** between connected rooms
- Use **up** to climb staircases to the next floor
- Each room has 1-3 random connections to other rooms
- Moving to new rooms awards small amounts of exploration gold

### Combat
- **30% base encounter chance** when entering a room (increases with floor level)
- Combat is automatic once initiated - player and enemy exchange attacks
- Players can **flee** with 50-80% success rate (based on current health)
- **Allies** can be used for powerful one-time attacks
- Defeating enemies awards gold based on their difficulty

### Progression
- **Gold** is the main scoring metric
- **Floors** increase in difficulty with stronger enemies
- **Staircases** appear randomly (5% chance per room) to access new floors
- **Health** regenerates slightly after some victories

### Allies
- Found randomly during exploration
- Each ally can perform one powerful attack
- Ally strength scales with the current floor level
- Strategic use of allies can turn difficult battles

## Project Structure

```
dungeon_crawler_api/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes.py            # REST API endpoints
│   ├── controllers/         # Game logic controllers
│   ├── models/              # Data model classes
│   ├── utils/               # Database and helper utilities
│   └── templates/           # (Optional) HTML templates
├── data/                    # JSON data files
├── tests/                   # Unit tests
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── README.md               # This file
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m unittest tests.test_routes
```

### Configuration

Environment variables:
- `FLASK_ENV` - Set to 'production' for production mode
- `FLASK_HOST` - Server host (default: 127.0.0.1)
- `FLASK_PORT` - Server port (default: 5000)
- `FLASK_DEBUG` - Enable debug mode (default: True)
- `DATA_DIR` - Directory for JSON data files (default: ./data)
- `SECRET_KEY` - Flask secret key for sessions

### Adding LLM Integration

The `GenerationController` is designed to integrate with LLM services. To add real AI-generated content:

1. Install an LLM client library (openai, anthropic, etc.)
2. Update `generation.py` methods to call your LLM API
3. Add your API key to environment variables
4. Replace the template-based generation with LLM calls

Example:
```python
def generate_enemy_content(self, floor: int, room: Optional[Room] = None) -> Dict[str, str]:
    prompt = f"Create a fantasy enemy for floor {floor} of a dungeon..."
    response = openai.Completion.create(...)
    return {"name": response.name, "description": response.description}
```

## Architecture Notes

### Session Management
- Each player gets a unique UUID session ID
- Sessions are stored in `data/users.json`
- No automatic cleanup - implement as needed for production

### Data Persistence
- **File-based JSON storage** for simplicity
- Easy to migrate to proper database (PostgreSQL, MongoDB, etc.)
- All data classes have `to_dict()` and `from_dict()` methods for serialization

### Scalability Considerations
- **Stateless design** - all game state stored in database
- **Controller pattern** - business logic separated from routes
- **Modular structure** - easy to add new features or swap components

## Contributing

1. Follow the existing code structure and patterns
2. Add unit tests for new features
3. Update this README for significant changes
4. Use type hints and docstrings for new functions

## License

This project is provided as-is for educational and development purposes.

---

**Ready to explore the abyss?** Start the server and begin your adventure!