"""
REST API routes for the dungeon crawler game.
"""

from flask import Blueprint, request, jsonify, current_app, session, send_from_directory
from typing import Dict, Any, Optional
import uuid
from pathlib import Path

from .models import Player, Enemy, Ally, Room, Item
from .controllers import MovementController, CombatController, GenerationController, ScoringController, InventoryController, BlackjackController
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
        'scoring': ScoringController(),
        'inventory': InventoryController(),
        'blackjack': BlackjackController()
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
        from pydantic import ValidationError
        from app.models.request_models import PlayerCreateRequest
        try:
            req = PlayerCreateRequest.parse_obj(request.get_json() or {})
        except ValidationError as ve:
            return create_error_response(f"Invalid input: {ve.errors()}", ve.json()), 400
        player_name = sanitize_input(req.name)

        # Create new player
        player = Player(name=player_name)
        
        # Initialize starting room
        controllers = get_controllers()
        
        # Set the session for session-specific room management
        controllers['movement'].set_session(player.session_id)
        
        start_room = controllers['movement'].initialize_player_room(player)
        
        # Save player to database
        user_db = get_user_db()
        success = user_db.save_user(player.session_id, player.to_dict())
        
        if not success:
            return create_error_response("Failed to create player session"), 500
        
        # Hardcoded story intro - same for all players
        story_intro = (
            "The day started like any other at Rocket Software's headquarters. Developers typed away at their keyboards, "
            "coffee machines hummed in break rooms, and the fluorescent lights buzzed overhead. But then, without warning, "
            "a black SUV screeched to a halt outside the building.\n\n"
            
            "An evil wizard emerged, staff crackling with dark energy. With a wave of his gnarled hand and a muttered incantation, "
            "reality itself bent and twisted. The building groaned and shifted—hallways stretched into impossible corridors, "
            "conference rooms became monster-infested chambers, and the elevator shafts descended into endless darkness.\n\n"
            
            "Rocket Software had become an infinite labyrinth of horrors.\n\n"
            
            "But the employees were not defenseless. As the curse took hold, something awakened within them—ancient powers "
            "of fantasy and legend. Programmers found themselves wielding swords of pure code. Project managers commanded "
            "arcane shields. Even the interns discovered they could cast healing spells.\n\n"
            
            "Now, you and your fellow employees must fight through the cursed floors, battling office-dwelling monsters "
            "and twisted creatures of corporate nightmare. Your mission: reclaim Rocket Software, defeat the wizard's minions, "
            "and restore the building to normal.\n\n"
            
            "The labyrinth awaits. Steel yourself, brave employee. Your adventure begins now!"
        )
        
        response_data = {
            'session_id': player.session_id,
            'story': story_intro,
            'player': {
                'name': player.name,
                'health': f"{player.health}/{player.max_health}",
                'gold': player.gold,
                'floor': player.floor,
                'room_id': player.room_id,
                'level': player.level,
                'attack_power': player.attack_power,
                'defense': player.defense,
                'visited_rooms': list(player.visited_rooms),
                'allies': [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies],
                'allies_count': len(player.allies),
                'inventory': [item.get_item_info() for item in player.inventory]
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
        from app.models.request_models import PlayerSessionRequest
        req = PlayerSessionRequest.parse_obj(request.get_json() or {})
        session_id = req.session_id
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
                'allies_count': len(player.allies),
                'inventory_count': len(player.inventory)
            },
            'current_room': current_room.get_room_info(),
            'movement_options': movement_info['data'] if not movement_info.get('error') else {},
            'inventory': [item.get_item_info() for item in player.inventory],
            'allies': [ally.get_ally_info() if hasattr(ally, 'get_ally_info') else ally for ally in player.allies]
        }
        
        return create_success_response(response_data, "Player status retrieved")
        
    except Exception as e:
        return create_error_response(f"Error retrieving player status: {str(e)}"), 500


@bp.route('/player/look', methods=['POST'])
def look_around():
    """
    Inspect current room for available directions and details.
    
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
        
        # Get current room
        current_room = controllers['movement'].get_room(player.room_id, player.floor)
        if not current_room:
            return create_error_response("Current room not found"), 404
        
        # Get detailed room information
        response_data = {
            'room': {
                'room_id': current_room.room_id,
                'name': current_room.name,
                'description': current_room.description,
                'floor': current_room.floor,
                'has_been_visited': current_room.has_been_visited,
                'has_staircase': current_room.has_staircase,
                'has_ally': current_room.has_ally(),
                'ally_name': current_room.ally_data.get('name') if current_room.ally_data else None
            },
            'available_directions': current_room.get_available_directions(),
            'connections': {direction: room_id for direction, room_id in current_room.connections.items()},
            'player_status': {
                'in_battle': player.in_battle,
                'health': f"{player.health}/{player.max_health}",
                'level': player.level,
                'experience': player.get_current_level_progress()
            }
        }
        
        return create_success_response(response_data, "Room inspection completed")
        
    except Exception as e:
        return create_error_response(f"Error inspecting room: {str(e)}"), 500


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
        from app.models.request_models import PlayerMoveRequest
        req = PlayerMoveRequest.parse_obj(request.get_json() or {})
        session_id = req.session_id
        direction = req.direction
        direction = sanitize_input(direction)

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
        
        # Set the session for session-specific room management
        controllers['movement'].set_session(session_id)
        
        success, movement_result = controllers['movement'].move_player(player, direction)
        
        if not success:
            return movement_result, 400
        
        # Check for encounter in new room
        new_room = controllers['movement'].get_room(player.room_id, player.floor)
        encounter_occurred = False
        encounter_result = None
        ally_encountered = False
        ally_result = None
        item_found = False
        item_result = None
        
        # Store if room was visited BEFORE we mark it (to prevent exploits)
        room_was_visited = new_room.has_been_visited if new_room else True
        
        # Check for ally first (if room has one AND room not yet visited)
        ally_data = None
        if new_room and not room_was_visited and new_room.has_ally():
            from app.models.ally import Ally
            ally_data = new_room.take_ally()  # Remove ally from room after taking
            ally_encountered = True
            
            print(f"DEBUG ALLY RECRUIT: Player had {len(player.allies)} allies before recruitment")
            
            # Create Ally object and add to player's allies list
            ally = Ally.from_dict(ally_data)
            player.add_ally(ally)
            
            print(f"DEBUG ALLY RECRUIT: Player now has {len(player.allies)} allies after recruitment")
            print(f"DEBUG ALLY RECRUIT: Allies list: {[a.name if hasattr(a, 'name') else str(a) for a in player.allies]}")
            
            ally_result = {
                'ally_found': True,
                'ally': ally.to_dict(),
                'message': f"🤝 {ally.name} joins your party! Use them anytime in battle. ({ally.description})"
            }
        
        # Check for enemy encounter (roll_for_encounter already checks has_been_visited)
        encounter_roll_happened = False
        encounter_roll_result_debug = "no_roll"
        
        if new_room and controllers['combat'].check_encounter_chance(new_room):
            encounter_roll_happened = True
            encounter_roll_result_debug = "encounter_triggered"
            
            # Generate enemy for encounter
            enemy_content = controllers['generation'].generate_enemy_content(player.floor, new_room)
            enemy = Enemy.create_random_enemy(player.floor, enemy_content['name'], enemy_content['description'])
            
            # Start turn-based battle (no ally passed - player chooses when to use)
            combat_result = controllers['combat'].start_battle(player, enemy, new_room, None)
            encounter_occurred = True
            encounter_result = combat_result
        elif new_room:
            encounter_roll_happened = True
            encounter_roll_result_debug = "no_encounter"
            
            # If no encounter, check for item find (only if NOT visited)
            if not room_was_visited:
                found_item, item = controllers['inventory'].roll_for_item_find(player, room_was_visited)
                if found_item and item:
                    item_found = True
                    controllers['inventory'].add_item_to_inventory(player, item)
                    item_result = {
                        'item_found': True,
                        'item': item.get_item_info(),
                        'message': f"You found {item.name}!"
                    }
        
        # NOW mark room as visited after encounter check
        if new_room:
            new_room.visit()
            # Save the room with updated visited status
            controllers['movement']._save_room(new_room)
        
        # Award exploration gold only on first visit
        exploration_gold = 0
        if not room_was_visited:
            exploration_gold = controllers['scoring'].award_exploration_gold(player, True)
            player.add_gold(exploration_gold)
        
        print(f"DEBUG MOVE END: Player has {len(player.allies)} allies before saving")
        print(f"DEBUG MOVE END: Allies: {[a.name if hasattr(a, 'name') else str(a) for a in player.allies]}")
        
        # Save updated player state
        user_db.save_user(session_id, player.to_dict())
        
        # Prepare response
        response_data = movement_result['data']
        response_data['exploration_gold'] = exploration_gold
        response_data['encounter_occurred'] = encounter_occurred
        response_data['ally_encountered'] = ally_encountered
        response_data['item_found'] = item_found
        
        # Add more detailed debug info with correct encounter roll result
        if new_room:
            response_data['debug']['encounter_roll_result'] = encounter_roll_result_debug
            response_data['debug']['room_visited_after_move'] = new_room.has_been_visited
        
        if encounter_occurred:
            response_data['encounter_result'] = encounter_result
            
        if ally_encountered:
            response_data['ally_result'] = ally_result
        
        if item_found:
            response_data['item_result'] = item_result
        
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
        "ally_index": 0 (optional, index of ally to use in attack)
    }
    """
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        action = data.get('action')
        ally_index = data.get('ally_index')  # Optional: which ally to use

        if not session_id or not action:
            return create_error_response("Missing session_id or action"), 400

        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        
        print(f"DEBUG: Before combat action - Player has {len(player.allies)} allies: {[a.name if hasattr(a, 'name') else str(a) for a in player.allies]}")
        
        if not player.is_alive():
            return create_error_response("Cannot act - player is not alive"), 400
        
        if not player.in_battle:
            return create_error_response("Player is not in battle"), 400
        
        controllers = get_controllers()
        
        if action == "attack":
            # Execute attack (with optional ally)
            use_ally = ally_index is not None
            attack_result = controllers['combat'].execute_attack(player, use_ally, ally_index)
        elif action == "flee":
            # Execute flee
            attack_result = controllers['combat'].execute_flee(player)
        else:
            return create_error_response("Invalid action. Use 'attack' or 'flee'"), 400
        
        print(f"DEBUG: After combat action - Player has {len(player.allies)} allies: {[a.name if hasattr(a, 'name') else str(a) for a in player.allies]}")
        
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
        from app.models.request_models import CombatUseAllyRequest
        req = CombatUseAllyRequest.parse_obj(request.get_json() or {})
        if not req.session_id or not req.ally_index or not req.enemy_data:
            return create_error_response("Missing required fields"), 400

        session_id = req.session_id
        ally_index = req.ally_index
        enemy_data = req.enemy_data

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
        from app.models.request_models import CombatFleeRequest
        req = CombatFleeRequest.parse_obj(request.get_json() or {})
        if not req.session_id or not req.enemy_data:
            return create_error_response("Missing session_id or enemy_data"), 400

        session_id = req.session_id
        enemy_data = req.enemy_data

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
        from app.models.request_models import PlayerSessionRequest
        req = PlayerSessionRequest.parse_obj(request.get_json() or {})
        if not req.session_id:
            return create_error_response("Missing session_id"), 400

        session_id = req.session_id
        
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
        from app.models.request_models import PlayerSessionRequest
        req = PlayerSessionRequest.parse_obj(request.get_json() or {})
        if not req.session_id:
            return create_error_response("Missing session_id"), 400

        session_id = req.session_id
        
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
        from app.models.request_models import PlayerSessionRequest
        req = PlayerSessionRequest.parse_obj(request.get_json() or {})
        if not req.session_id:
            return create_error_response("Missing session_id"), 400

        session_id = req.session_id
        
        # Delete player
        user_db = get_user_db()
        success = user_db.delete_user(session_id)
        
        if success:
            return create_success_response({'deleted': True}, "Player session deleted")
        else:
            return create_error_response("Failed to delete player session"), 500
        
    except Exception as e:
        return create_error_response(f"Error deleting player: {str(e)}"), 500


@bp.route('/player/heal', methods=['POST'])
def heal_player():
    """
    Restore player to full health (debug/cheat endpoint).
    
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
        
        # Heal to full
        old_health = player.health
        player.health = player.max_health
        
        # Save updated player state
        user_db.save_user(session_id, player.to_dict())
        
        return create_success_response({
            'old_health': old_health,
            'new_health': player.health,
            'max_health': player.max_health,
            'message': f'Health restored from {old_health} to {player.health}!'
        }, "Player healed to full health")
        
    except Exception as e:
        return create_error_response(f"Error healing player: {str(e)}"), 500


@bp.route('/debug/staircases', methods=['POST'])
def debug_staircases():
    """
    Debug endpoint to check all staircases on current floor.
    
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
        controllers = get_controllers()
        
        # Get all rooms on current floor
        room_db = controllers['movement'].room_db
        floor_rooms = room_db.get_floor_rooms(player.floor)
        
        staircase_info = {}
        for room_id, room_data in floor_rooms.items():
            has_staircase = room_data.get('has_staircase', False)
            staircase_info[room_id] = {
                'name': room_data.get('name', 'Unknown'),
                'has_staircase': has_staircase,
                'has_been_visited': room_data.get('has_been_visited', False)
            }
        
        return create_success_response({
            'floor': player.floor,
            'current_room': player.room_id,
            'total_rooms': len(floor_rooms),
            'rooms_with_staircases': sum(1 for info in staircase_info.values() if info['has_staircase']),
            'room_details': staircase_info
        }, "Staircase debug information")
        
    except Exception as e:
        return create_error_response(f"Error getting staircase debug info: {str(e)}"), 500


### Inventory Endpoints ###

@bp.route('/inventory/view', methods=['POST'])
def view_inventory():
    """
    View player's inventory.
    
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
        
        # Get inventory
        controllers = get_controllers()
        result = controllers['inventory'].get_inventory(player)
        
        return result
        
    except Exception as e:
        return create_error_response(f"Error viewing inventory: {str(e)}"), 500


@bp.route('/inventory/use', methods=['POST'])
def use_item():
    """
    Use an item from inventory.
    
    Expected JSON:
    {
        "session_id": "player-session-id",
        "item_id": "item-uuid"
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data or 'item_id' not in data:
            return create_error_response("Missing session_id or item_id"), 400
        
        session_id = data['session_id']
        item_id = data['item_id']
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        
        # Get enemy if in battle
        enemy = None
        if player.in_battle and player.current_enemy:
            enemy = Enemy.from_dict(player.current_enemy)
        
        # Use item
        controllers = get_controllers()
        success, result = controllers['inventory'].use_item(player, item_id, enemy)
        
        # If enemy was affected, update it in player's battle state
        if enemy and player.in_battle:
            player.current_enemy = enemy.to_dict()
        
        # Save updated player state
        user_db.save_user(session_id, player.to_dict())
        
        if success:
            return result
        else:
            return result, 400
        
    except Exception as e:
        return create_error_response(f"Error using item: {str(e)}"), 500


@bp.route('/inventory/discard', methods=['POST'])
def discard_item():
    """
    Discard an item from inventory.
    
    Expected JSON:
    {
        "session_id": "player-session-id",
        "item_id": "item-uuid"
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data or 'item_id' not in data:
            return create_error_response("Missing session_id or item_id"), 400
        
        session_id = data['session_id']
        item_id = data['item_id']
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        
        # Discard item
        controllers = get_controllers()
        success, result = controllers['inventory'].discard_item(player, item_id)
        
        # Save updated player state
        user_db.save_user(session_id, player.to_dict())
        
        if success:
            return result
        else:
            return result, 400
        
    except Exception as e:
        return create_error_response(f"Error discarding item: {str(e)}"), 500


@bp.route('/shop/view', methods=['POST'])
def view_shop():
    """
    View shop items in current room.
    
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
        
        print(f"DEBUG: Shop view - Player at room_id: {player.room_id}, floor: {player.floor}, session: {session_id[:8]}")
        
        # Get current room - use regular get_room since rooms are saved without explicit session suffix in ID
        controllers = get_controllers()
        controllers['movement'].set_session(session_id)  # Set session for any room operations
        current_room = controllers['movement'].get_room(player.room_id, player.floor)
        
        print(f"DEBUG: Shop view - Room found: {current_room is not None}")
        if current_room:
            print(f"DEBUG: Shop view - Room is_shop: {current_room.is_shop}")
            print(f"DEBUG: Shop view - Shop items count: {len(current_room.shop_items)}")
        
        if not current_room:
            return create_error_response("Current room not found"), 404
        
        if not current_room.is_shop:
            return create_error_response("Current room is not a shop"), 400
        
        # Get available items (excluding already purchased)
        available_items = current_room.get_available_shop_items()
        
        return create_success_response({
            "shop_items": available_items,
            "player_gold": player.gold
        }, "Shop inventory retrieved")
        
    except Exception as e:
        return create_error_response(f"Error viewing shop: {str(e)}"), 500


@bp.route('/shop/purchase', methods=['POST'])
def purchase_item():
    """
    Purchase an item from the shop.
    
    Expected JSON:
    {
        "session_id": "player-session-id",
        "item_name": "Item Name"
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data or 'item_name' not in data:
            return create_error_response("Missing session_id or item_name"), 400
        
        session_id = data['session_id']
        item_name = data['item_name']
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        
        # Get current room - use regular get_room since rooms are saved without explicit session suffix in ID
        controllers = get_controllers()
        controllers['movement'].set_session(session_id)  # Set session for any room operations
        current_room = controllers['movement'].get_room(player.room_id, player.floor)
        
        if not current_room:
            return create_error_response("Current room not found"), 404
        
        if not current_room.is_shop:
            return create_error_response("Current room is not a shop"), 400
        
        # Check if item already purchased
        if current_room.is_item_purchased(item_name):
            return create_error_response("Item already purchased"), 400
        
        # Find the item in shop
        shop_item = None
        for item in current_room.shop_items:
            if item['name'] == item_name:
                shop_item = item
                break
        
        if not shop_item:
            return create_error_response("Item not found in shop"), 404
        
        # Check if player has enough gold
        if player.gold < shop_item['price']:
            return create_error_response(f"Not enough gold. Need {shop_item['price']}, have {player.gold}"), 400
        
        # Deduct gold
        player.gold -= shop_item['price']
        
        # Add item to inventory
        new_item = Item(shop_item['item_type'])
        player.add_item(new_item)
        
        # Mark item as purchased
        current_room.purchase_item(item_name)
        
        # Save updated player state
        user_db.save_user(session_id, player.to_dict())
        
        # Save updated room state - use regular _save_room since session is set
        controllers['movement']._save_room(current_room)
        
        return create_success_response({
            "purchased_item": shop_item,
            "gold_remaining": player.gold,
            "inventory": [item.to_dict() for item in player.inventory]
        }, f"Purchased {item_name} for {shop_item['price']} gold!")
        
    except Exception as e:
        return create_error_response(f"Error purchasing item: {str(e)}"), 500


@bp.route('/casino/enter', methods=['POST'])
def enter_casino():
    """
    Enter the casino in the current room.
    
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
        
        # Get current room
        controllers = get_controllers()
        controllers['movement'].set_session(session_id)
        current_room = controllers['movement'].get_room(player.room_id, player.floor)
        
        if not current_room:
            return create_error_response("Current room not found"), 404
        
        if not current_room.is_casino:
            return create_error_response("Current room is not a casino"), 400
        
        return create_success_response({
            "player_gold": player.gold,
            "casino_name": current_room.name,
            "casino_description": current_room.description
        }, "Welcome to the casino!")
        
    except Exception as e:
        return create_error_response(f"Error entering casino: {str(e)}"), 500


@bp.route('/casino/blackjack/start', methods=['POST'])
def start_blackjack():
    """
    Start a new blackjack game.
    
    Expected JSON:
    {
        "session_id": "player-session-id",
        "bet": 50
    }
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data or 'bet' not in data:
            return create_error_response("Missing session_id or bet"), 400
        
        session_id = data['session_id']
        bet = int(data['bet'])
        
        if bet <= 0:
            return create_error_response("Bet must be positive"), 400
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        player = Player.from_dict(player_data)
        
        # Check if player has enough gold
        if player.gold < bet:
            return create_error_response(f"Not enough gold. Need {bet}, have {player.gold}"), 400
        
        # Deduct bet from player
        player.gold -= bet
        
        # Start blackjack game
        controllers = get_controllers()
        game_state = controllers['blackjack'].start_game(bet)
        
        # Save game state in session (we'll store it in player data temporarily)
        player_data['blackjack_game'] = game_state
        player_data['gold'] = player.gold
        user_db.save_user(session_id, player_data)
        
        # Get display-friendly version
        display = controllers['blackjack'].get_game_display(game_state)
        
        return create_success_response({
            "game": display,
            "player_gold": player.gold
        }, "Blackjack game started!")
        
    except Exception as e:
        return create_error_response(f"Error starting blackjack: {str(e)}"), 500


@bp.route('/casino/blackjack/hit', methods=['POST'])
def blackjack_hit():
    """
    Hit in blackjack (draw another card).
    
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
        
        # Get player and game state
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        if 'blackjack_game' not in player_data:
            return create_error_response("No active blackjack game"), 400
        
        game_state = player_data['blackjack_game']
        
        # Execute hit
        controllers = get_controllers()
        game_state = controllers['blackjack'].hit(game_state)
        
        # Handle payout if game ended
        if game_state['game_over']:
            payout = game_state.get('payout', 0)
            player_data['gold'] += payout
            player_data.pop('blackjack_game', None)  # Remove game state
        else:
            player_data['blackjack_game'] = game_state
        
        user_db.save_user(session_id, player_data)
        
        # Get display version
        display = controllers['blackjack'].get_game_display(game_state)
        
        return create_success_response({
            "game": display,
            "player_gold": player_data['gold']
        }, game_state.get('message', 'Card drawn'))
        
    except Exception as e:
        return create_error_response(f"Error hitting in blackjack: {str(e)}"), 500


@bp.route('/casino/blackjack/stand', methods=['POST'])
def blackjack_stand():
    """
    Stand in blackjack (end player turn, dealer plays).
    
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
        
        # Get player and game state
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        if not player_data:
            return create_error_response("Player session not found"), 404
        
        if 'blackjack_game' not in player_data:
            return create_error_response("No active blackjack game"), 400
        
        game_state = player_data['blackjack_game']
        
        # Execute stand
        controllers = get_controllers()
        game_state = controllers['blackjack'].stand(game_state)
        
        # Handle payout
        payout = game_state.get('payout', 0)
        player_data['gold'] += payout
        player_data.pop('blackjack_game', None)  # Remove game state
        
        user_db.save_user(session_id, player_data)
        
        # Get display version
        display = controllers['blackjack'].get_game_display(game_state, hide_dealer=False)
        
        return create_success_response({
            "game": display,
            "player_gold": player_data['gold']
        }, game_state.get('message', 'Round complete'))
        
    except Exception as e:
        return create_error_response(f"Error standing in blackjack: {str(e)}"), 500


# Health check for individual components
@bp.route('/debug/room', methods=['POST'])
def debug_room_info():
    """Debug endpoint to check room encounter and staircase status."""
    try:
        from app.models.request_models import PlayerSessionRequest
        req = PlayerSessionRequest.parse_obj(request.get_json() or {})
        if not req.session_id:
            return create_error_response("Missing session_id"), 400

        session_id = req.session_id
        
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