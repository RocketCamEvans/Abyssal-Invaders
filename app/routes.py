"""
REST API routes for the dungeon crawler game.
"""

from flask import Blueprint, request, jsonify, current_app, session
from typing import Dict, Any, Optional
import uuid

from .models import Player, Enemy, Ally, Room
from .controllers import MovementController, CombatController, GenerationController, ScoringController
from .utils import UserDB, create_error_response, create_success_response, sanitize_input

# Create blueprint
bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize controllers (will be created per request to avoid state issues)
def get_controllers():
    """Get fresh controller instances."""
    return {
        'movement': MovementController(),
        'combat': CombatController(),
        'generation': GenerationController(),
        'scoring': ScoringController()
    }

def get_user_db():
    """Get user database instance."""
    return UserDB(current_app.config['DATA_DIR'])


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return create_success_response({'status': 'healthy', 'service': 'dungeon_crawler_api'})


@bp.route('/player/new', methods=['POST'])
def create_player():
    """
    Create a new player session.
    
    Expected JSON:
    {
        "name": "Player Name" (optional)
    }
    """
    try:
        data = request.get_json() or {}
        player_name = sanitize_input(data.get('name', 'Unknown Adventurer'))
        
        # Create new player
        player = Player(name=player_name)
        
        # Initialize starting room
        controllers = get_controllers()
        start_room = controllers['movement'].initialize_player_room(player)
        
        # Save player to database
        user_db = get_user_db()
        success = user_db.save_user(player.session_id, player.to_dict())
        
        if not success:
            return create_error_response("Failed to create player session"), 500
        
        response_data = {
            'session_id': player.session_id,
            'player': {
                'name': player.name,
                'health': f"{player.health}/{player.max_health}",
                'gold': player.gold,
                'floor': player.floor,
                'room_id': player.room_id
            },
            'current_room': start_room.get_room_info()
        }
        
        return create_success_response(response_data, f"Welcome, {player.name}! Your adventure begins.")
        
    except Exception as e:
        return create_error_response(f"Error creating player: {str(e)}"), 500


@bp.route('/player/status', methods=['POST'])
def get_player_status():
    """
    Get current player status.
    
    Expected JSON:
    {
        "session_id": "player-session-id"
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data:
            return create_error_response("Missing session_id"), 400
        
        session_id = data['session_id']
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        controllers = get_controllers()
        
        # Get current room information
        current_room = controllers['movement'].get_room(player.room_id, player.floor)
        if not current_room:
            return create_error_response("Current room not found"), 404
        
        # Get available moves
        movement_info = controllers['movement'].get_available_moves(player)
        
        response_data = {
            'player': {
                'name': player.name,
                'health': f"{player.health}/{player.max_health}",
                'gold': player.gold,
                'floor': player.floor,
                'room_id': player.room_id,
                'is_alive': player.is_alive(),
                'allies_count': len(player.allies)
            },
            'current_room': current_room.get_room_info(),
            'movement_options': movement_info['data'] if not movement_info.get('error') else {}
        }
        
        return create_success_response(response_data, "Player status retrieved")
        
    except Exception as e:
        return create_error_response(f"Error retrieving player status: {str(e)}"), 500


@bp.route('/player/move', methods=['POST'])
def move_player():
    """
    Move player in specified direction.
    
    Expected JSON:
    {
        "session_id": "player-session-id",
        "direction": "north|south|east|west|up"
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data or 'direction' not in data:
            return create_error_response("Missing session_id or direction"), 400
        
        session_id = data['session_id']
        direction = sanitize_input(data['direction'])
        turn_based = bool(data.get('turn_based'))  # optional flag
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        if not player.is_alive():
            return create_error_response("Cannot move - player is not alive"), 400
        
        # Attempt movement
        controllers = get_controllers()
        success, movement_result = controllers['movement'].move_player(player, direction)
        
        if not success:
            return movement_result, 400
        
        # Check for encounter in new room
        new_room = controllers['movement'].get_room(player.room_id, player.floor)
        encounter_occurred = False
        encounter_result = None
        ally_encountered = False
        ally_result = None
        
        # Check for ally first (if room has one)
        ally_data = None
        if new_room and new_room.has_ally():
            ally_data = new_room.take_ally()  # Remove ally from room after taking
            ally_encountered = True
            ally_result = {
                'ally_found': True,
                'ally_name': ally_data['name'],
                'ally_description': ally_data['description'],
                'message': f"You encountered {ally_data['name']}! They will assist you in your next battle."
            }
            # Store ally for future battles - it will be used automatically in the next combat
        
        # Check for enemy encounter
        if new_room and controllers['combat'].check_encounter_chance(new_room):
            enemy_content = controllers['generation'].generate_enemy_content(player.floor, new_room)
            enemy = Enemy.create_random_enemy(player.floor, enemy_content['name'], enemy_content['description'])

            if turn_based:
                # Begin turn-based battle (no auto resolution)
                ally_for_battle = ally_data if ally_encountered else None
                start_data = controllers['combat'].start_battle(player, enemy, new_room, ally_for_battle)
                # Enrich with enemy/player snapshot
                if not start_data.get('error'):
                    data_block = start_data.get('data', {})
                    data_block['battle_started'] = True
                    data_block['enemy'] = enemy.to_dict()
                    data_block['player'] = {
                        'health': f"{player.health}/{player.max_health}",
                        'gold': player.gold,
                        'floor': player.floor,
                        'room_id': player.room_id
                    }
                    start_data['data'] = data_block
                encounter_occurred = True
                encounter_result = start_data
            else:
                # Auto-resolve full combat
                player, enemy, combat_result = controllers['combat'].initiate_combat(player, enemy, new_room)
                if not combat_result.get('error'):
                    data_block = combat_result.get('data', {})
                    rounds = data_block.get('combat_log', [])
                    outcome_msg = data_block.get('result', {}).get('message', combat_result.get('message', 'Combat resolved'))
                    first_round_summary = rounds[0]['summary'] if rounds else ''
                    short_summary = f"Encounter! {outcome_msg}" if outcome_msg else "Encounter resolved."
                    data_block['enemy'] = enemy.to_dict()
                    data_block['player_after'] = {
                        'health': f"{player.health}/{player.max_health}",
                        'gold': player.gold,
                        'floor': player.floor,
                        'room_id': player.room_id
                    }
                    data_block['short_summary'] = short_summary
                    data_block['first_round'] = first_round_summary
                    combat_result['data'] = data_block
                encounter_occurred = True
                encounter_result = combat_result
        
        # NOW mark room as visited after encounter check
        if new_room:
            new_room.visit()
            # Save the room with updated visited status
            controllers['movement']._save_room(new_room)
        
        # Award exploration gold
        exploration_gold = controllers['scoring'].award_exploration_gold(player, True)
        player.add_gold(exploration_gold)
        
        # Save updated player state
        user_db.save_user(session_id, player.to_dict())
        
        # Prepare response
        response_data = movement_result['data']
        response_data['exploration_gold'] = exploration_gold
        response_data['encounter_occurred'] = encounter_occurred
        response_data['ally_encountered'] = ally_encountered
        
        # Add more detailed debug info
        if new_room:
            response_data['debug']['encounter_roll_result'] = "turn_based_started" if (encounter_occurred and turn_based) else (controllers['combat'].check_encounter_chance(new_room) if not new_room.has_been_visited else "room_already_visited")
            response_data['debug']['room_visited_after_move'] = new_room.has_been_visited
            response_data['debug']['turn_based'] = turn_based
        
        if encounter_occurred:
            response_data['encounter_result'] = encounter_result
            
        if ally_encountered:
            response_data['ally_result'] = ally_result
        
        return create_success_response(response_data, "Movement completed")
        
    except Exception as e:
        return create_error_response(f"Error during movement: {str(e)}"), 500


@bp.route('/player/attack', methods=['POST'])
def player_attack():
    """
    Execute a turn-based attack in combat.
    
    Expected JSON:
    {
        "session_id": "player-session-id",
        "action": "attack" | "flee",
        "use_ally": false (optional, for ally special attack)
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data or 'action' not in data:
            return create_error_response("Missing required fields"), 400
        
        session_id = data['session_id']
        action = data['action']
        use_ally = data.get('use_ally', False)
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        
        if not player.is_alive():
            return create_error_response("Cannot act - player is not alive"), 400
        
        if not player.in_battle:
            return create_error_response("Player is not in battle"), 400
        
        controllers = get_controllers()
        
        if action == "attack":
            # Execute attack
            attack_result = controllers['combat'].execute_attack(player, use_ally)
        elif action == "flee":
            # Execute flee
            attack_result = controllers['combat'].execute_flee(player)
        else:
            return create_error_response("Invalid action. Use 'attack' or 'flee'"), 400
        
        # Save updated player state
        user_db.save_user(session_id, player.to_dict())
        
        return attack_result
        
    except Exception as e:
        return create_error_response(f"Error during combat action: {str(e)}"), 500


@bp.route('/combat/attack', methods=['POST'])
def attack_enemy():
    """
    Attack an enemy during combat.
    
    Expected JSON:
    {
        "session_id": "player-session-id",
        "enemy_data": {...enemy object...}
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data or 'enemy_data' not in data:
            return create_error_response("Missing session_id or enemy_data"), 400
        
        session_id = data['session_id']
        enemy_data = data['enemy_data']
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        if not player.is_alive():
            return create_error_response("Cannot attack - player is not alive"), 400
        
        # Recreate enemy from data
        enemy = Enemy.from_dict(enemy_data)
        if not enemy.is_alive():
            return create_error_response("Enemy is already defeated"), 400
        
        # Get current room for combat context
        controllers = get_controllers()
        current_room = controllers['movement'].get_room(player.room_id, player.floor)
        
        # Execute single combat round
        player, enemy, combat_result = controllers['combat'].initiate_combat(player, enemy, current_room)
        
        # Save updated player state
        user_db.save_user(session_id, player.to_dict())
        
        return combat_result
        
    except Exception as e:
        return create_error_response(f"Error during combat: {str(e)}"), 500


@bp.route('/combat/flee', methods=['POST'])
def flee_combat():
    """
    Attempt to flee from combat.
    
    Expected JSON:
    {
        "session_id": "player-session-id",
        "enemy_data": {...enemy object...}
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data or 'enemy_data' not in data:
            return create_error_response("Missing session_id or enemy_data"), 400
        
        session_id = data['session_id']
        enemy_data = data['enemy_data']
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        enemy = Enemy.from_dict(enemy_data)
        
        # Attempt to flee
        controllers = get_controllers()
        success, result = controllers['combat'].flee_from_combat(player, enemy)
        
        # Save updated player state (health might have changed)
        user_db.save_user(session_id, player.to_dict())
        
        return result
        
    except Exception as e:
        return create_error_response(f"Error fleeing combat: {str(e)}"), 500


@bp.route('/scores/highscores', methods=['GET'])
def get_high_scores():
    """Get the current high score leaderboard."""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(50, max(1, limit))  # Clamp between 1 and 50
        
        controllers = get_controllers()
        result = controllers['scoring'].get_high_scores(limit)
        
        return result
        
    except Exception as e:
        return create_error_response(f"Error retrieving high scores: {str(e)}"), 500


@bp.route('/scores/submit', methods=['POST'])
def submit_score():
    """
    Submit player's final score.
    
    Expected JSON:
    {
        "session_id": "player-session-id"
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data:
            return create_error_response("Missing session_id"), 400
        
        session_id = data['session_id']
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        
        # Submit score
        controllers = get_controllers()
        success, result = controllers['scoring'].submit_high_score(player)
        
        return result
        
    except Exception as e:
        return create_error_response(f"Error submitting score: {str(e)}"), 500


@bp.route('/player/stats', methods=['POST'])
def get_player_statistics():
    """
    Get detailed player statistics.
    
    Expected JSON:
    {
        "session_id": "player-session-id"
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data:
            return create_error_response("Missing session_id"), 400
        
        session_id = data['session_id']
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        
        # Get statistics
        controllers = get_controllers()
        stats = controllers['scoring'].get_player_statistics(player)
        
        return stats
        
    except Exception as e:
        return create_error_response(f"Error retrieving statistics: {str(e)}"), 500


@bp.route('/player/delete', methods=['POST'])
def delete_player():
    """
    Delete a player session.
    
    Expected JSON:
    {
        "session_id": "player-session-id"
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data:
            return create_error_response("Missing session_id"), 400
        
        session_id = data['session_id']
        
        # Delete player
        user_db = get_user_db()
        success = user_db.delete_user(session_id)
        
        if success:
            return create_success_response({'deleted': True}, "Player session deleted")
        else:
            return create_error_response("Failed to delete player session"), 500
        
    except Exception as e:
        return create_error_response(f"Error deleting player: {str(e)}"), 500


# Health check for individual components
@bp.route('/debug/room', methods=['POST'])
def debug_room_info():
    """Debug endpoint to check room encounter and staircase status."""
    try:
        data = request.get_json()
        if not data or 'session_id' not in data:
            return create_error_response("Missing session_id"), 400
        
        session_id = data['session_id']
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        
        # Get current room
        controllers = get_controllers()
        current_room = controllers['movement'].get_room(player.room_id, player.floor)
        
        if not current_room:
            return create_error_response("Current room not found"), 404
        
        # Test encounter chance multiple times to see probability
        encounter_tests = []
        for i in range(10):
            encounter_tests.append(current_room.roll_for_encounter())
        
        debug_info = {
            'room_id': current_room.room_id,
            'room_name': current_room.name,
            'floor': current_room.floor,
            'has_been_visited': current_room.has_been_visited,
            'encounter_chance': current_room.encounter_chance,
            'has_staircase': current_room.has_staircase,
            'available_directions': current_room.get_available_directions(),
            'encounter_test_results': encounter_tests,
            'encounters_triggered_out_of_10': sum(encounter_tests)
        }
        
        return create_success_response(debug_info, "Room debug info")
        
    except Exception as e:
        return create_error_response(f"Error getting debug info: {str(e)}"), 500


@bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check including database connectivity."""
    try:
        # Test database connectivity
        user_db = get_user_db()
        test_data = {'test': 'connection'}
        db_healthy = user_db.save_data('health_check', test_data)
        if db_healthy:
            user_db.delete_file('health_check')
        
        # Test controllers
        controllers = get_controllers()
        
        health_status = {
            'service': 'dungeon_crawler_api',
            'status': 'healthy' if db_healthy else 'degraded',
            'components': {
                'database': 'healthy' if db_healthy else 'error',
                'movement_controller': 'healthy',
                'combat_controller': 'healthy',
                'generation_controller': 'healthy',
                'scoring_controller': 'healthy'
            },
            'data_directory': current_app.config['DATA_DIR']
        }
        
        return create_success_response(health_status)
        
    except Exception as e:
        return create_error_response(f"Health check failed: {str(e)}"), 500