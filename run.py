"""
Entry point for the Flask dungeon crawler API.
"""

import os
from app import create_app

# Create the Flask application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Configuration for development
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    ABYSSAL INVADERS                          ║
    ║                  Dungeon Crawler API                         ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Server starting on: http://{host}:{port}                   ║
    ║  Debug mode: {'ON' if debug else 'OFF'}                                         ║
    ║  Data directory: {app.config.get('DATA_DIR', 'data'):>30}  ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Available Endpoints:
    
    Core Game Operations:
    • POST /api/player/new          - Create new player
    • POST /api/player/status       - Get player status  
    • POST /api/player/move         - Move player
    • POST /api/player/stats        - Get detailed stats
    • POST /api/player/delete       - Delete player session
    
    Combat System:
    • POST /api/combat/attack       - Attack enemy
    • POST /api/combat/use_ally     - Use ally attack
    • POST /api/combat/flee         - Flee from combat
    
    Encounters:
    • POST /api/encounter/ally      - Encounter ally
    
    Scoring:
    • GET  /api/scores/highscores   - Get leaderboard
    • POST /api/scores/submit       - Submit final score
    
    System:
    • GET  /api/health              - Basic health check
    • GET  /api/health/detailed     - Detailed health check
    
    Ready to explore the abyss!
    """)
    
    app.run(host=host, port=port, debug=debug)