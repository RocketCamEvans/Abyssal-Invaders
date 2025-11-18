"""
Developer routes for testing and debugging.
Only accessible with valid DEV_MODE_KEY.
"""

from flask import Blueprint, request, jsonify, render_template, current_app
from .models import Player, Enemy, Room, Ally
from .models.ailment import Ailment, calculate_ailment_severity, calculate_ailment_duration
from .controllers import CombatController, GenerationController
from .utils import UserDB, create_error_response, create_success_response
import os
import random

dev_bp = Blueprint('dev', __name__)

# Load dev key from environment
DEV_MODE_KEY = os.getenv('DEV_MODE_KEY', '')

def verify_dev_key():
    """Verify that the request has a valid dev key."""
    key = request.args.get('key') or (request.json.get('key') if request.is_json else None)
    print(f"DEBUG verify_dev_key: received key='{key}', expected='{DEV_MODE_KEY}'")
    is_valid = key and key == DEV_MODE_KEY and DEV_MODE_KEY != ''
    print(f"DEBUG verify_dev_key: valid={is_valid}")
    return is_valid

def get_user_db():
    """Get user database instance."""
    return UserDB(current_app.config['DATA_DIR'])


@dev_bp.route('/dev')
def dev_screen():
    """Render the developer screen."""
    if not verify_dev_key():
        return "Access Denied: Invalid or missing dev key", 403
    
    return render_template('dev.html')


@dev_bp.route('/dev/health')
def dev_health():
    """Simple health check for dev mode availability."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    return jsonify(create_success_response({'status': 'available'}, "Dev mode active"))


@dev_bp.route('/dev/spawn-battle', methods=['POST'])
def spawn_battle():
    """Spawn a battle with custom parameters."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        floor = data.get('floor', 1)
        enemy_name = data.get('enemy_name', '')
        enemy_description = data.get('enemy_description', '')
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        # Create enemy
        if not enemy_name:
            # Generate random enemy
            generation_controller = GenerationController()
            enemy_content = generation_controller.generate_enemy_content(floor, None)
            enemy_name = enemy_content['name']
            enemy_description = enemy_content['description']
        
        enemy = Enemy.create_random_enemy(floor, enemy_name, enemy_description)
        
        # Apply ailment parameters if specified
        # Support both single and multiple ailment types
        ailment_types = data.get('ailment_types', [])  # New: list of types
        ailment_type = data.get('ailment_type')  # Old: single type (for backward compatibility)
        ailment_chance = data.get('ailment_chance')
        ailment_severity = data.get('ailment_severity')
        
        # Convert single type to list for consistency
        if ailment_type and ailment_type != 'none':
            if not ailment_types:
                ailment_types = [ailment_type]
            elif ailment_type not in ailment_types:
                ailment_types.append(ailment_type)
        
        print(f"DEBUG spawn_battle: ailment_types={ailment_types}, ailment_chance={ailment_chance}, ailment_severity={ailment_severity}")
        
        if ailment_types and ailment_chance:
            enemy.ailment_inflict_types = ailment_types
            enemy.ailment_inflict_chance = float(ailment_chance)
            # Set severity if provided (0-5), otherwise it will be calculated based on floor
            if ailment_severity is not None:
                enemy.ailment_inflict_severity = int(ailment_severity)
            print(f"DEBUG spawn_battle: Applied ailments to enemy - types={enemy.ailment_inflict_types}, chance={enemy.ailment_inflict_chance}, severity={enemy.ailment_inflict_severity}")
        
        # Get the current room from movement controller
        from .controllers import MovementController
        movement_controller = MovementController()
        movement_controller.set_session(session_id)
        
        # Try to get player's current room
        room = None
        if hasattr(player, 'room_id') and player.room_id:
            room = movement_controller.get_room_for_session(player.room_id, player.floor, session_id)
        
        # Fallback: create a dev battle room
        if not room:
            room = Room(
                room_id="dev_battle_room",
                name="Developer Battle Arena",
                description="A testing ground for brave developers.",
                floor=floor
            )
            player.room_id = room.room_id
            if not player.visited_rooms:
                player.visited_rooms = set()
            player.visited_rooms.add(room.room_id)
        
        # Start battle
        combat_controller = CombatController()
        result = combat_controller.start_battle(player, enemy, room, None)
        
        # Save player state
        user_db.save_user(session_id, player.to_dict())
        
        # Make sure we return player and room data for UI updates
        if not result.get('error'):
            if 'data' not in result:
                result['data'] = {}
            result['data']['player'] = player.to_dict()
            result['data']['room_info'] = room.to_dict()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify(create_error_response(f"Error spawning battle: {str(e)}")), 500


@dev_bp.route('/dev/spawn-room', methods=['POST'])
def spawn_room():
    """Spawn a specific type of room."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        room_type = data.get('room_type', 'normal')  # normal, shop, stairs, boss
        floor = data.get('floor', 1)
        
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        # Use movement controller to handle room properly
        from .controllers import MovementController
        movement_controller = MovementController()
        movement_controller.set_session(session_id)
        
        # Ensure floor is generated
        movement_controller.ensure_floor_generated(floor)
        
        # Get a random room from the floor
        # This ensures the room is properly connected in the dungeon
        start_room = movement_controller.get_start_room(floor)
        if start_room:
            player.room_id = start_room.room_id
            player.floor = floor
            player.visited_rooms.add(start_room.room_id)
            
            # Initialize room position
            if not hasattr(player, 'room_positions'):
                player.room_positions = {}
            player.room_positions[start_room.room_id] = {'x': 0, 'y': 0}
        
        # If not in battle, clear battle state
        if player.in_battle:
            player.end_battle()
        
        user_db.save_user(session_id, player.to_dict())
        
        return jsonify(create_success_response({
            'player': player.to_dict()
        }, f"Moved to a new {room_type} room"))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(create_error_response(f"Error spawning room: {str(e)}")), 500


@dev_bp.route('/dev/give-ally', methods=['POST'])
def give_ally():
    """Give player a specific ally."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        ally_name = data.get('ally_name', '')
        
        from .models.ally import PREDEFINED_ALLIES
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        # Find ally by name or get random
        ally_data = None
        if ally_name:
            ally_data = next((a for a in PREDEFINED_ALLIES if a['name'].lower() == ally_name.lower()), None)
        
        if not ally_data:
            ally_data = random.choice(PREDEFINED_ALLIES)
        
        ally = Ally(
            name=ally_data['name'],
            ally_type=ally_data['type'],
            value=ally_data['value'],
            description=ally_data['description'],
            floor=player.floor,
            sprite=ally_data.get('sprite', 'ally_warrior_human_male.png'),
            max_uses=ally_data.get('max_uses', 3)
        )
        
        result = player.add_ally(ally)
        
        # Update achievement stats for ally recruitment
        if result.get('success'):
            player.stats["allies_recruited"] = player.stats.get("allies_recruited", 0) + 1
            
            # Check if player has all unique allies (12 total)
            unique_ally_names = set()
            for ally_obj in player.allies:
                ally_name = ally_obj.name if hasattr(ally_obj, 'name') else ally_obj.get('name', '')
                if ally_name:
                    unique_ally_names.add(ally_name)
            
            # If player has all 12 unique allies, set the stat
            if len(unique_ally_names) >= 12:
                player.stats['all_allies_recruited'] = 1.0
            else:
                player.stats['all_allies_recruited'] = 0.0
        
        user_db.save_user(session_id, player.to_dict())
        
        return jsonify(create_success_response({
            'ally': ally.to_dict(),
            'player': player.to_dict(),
            'message': result['message']
        }, "Ally given successfully"))
        
    except Exception as e:
        return jsonify(create_error_response(f"Error giving ally: {str(e)}")), 500


@dev_bp.route('/dev/inflict-ailment', methods=['POST'])
def inflict_ailment():
    """Inflict an ailment on player or current enemy."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        target = data.get('target', 'enemy')  # 'player' or 'enemy'
        ailment_type = data.get('ailment_type', 'poison')  # 'poison' or 'paralysis'
        severity = data.get('severity', 3)
        
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        duration = calculate_ailment_duration(severity)
        ailment = Ailment(ailment_type, severity, duration)
        
        # Check if ailment is player-only
        if target == 'enemy' and ailment.is_player_only():
            return jsonify(create_error_response(f"{ailment_type} is a player-only ailment")), 400
        
        if target == 'player':
            player.add_ailment(ailment)
            user_db.save_user(session_id, player.to_dict())
            return jsonify(create_success_response({
                'ailment': ailment.to_dict(),
                'player': player.to_dict()
            }, f"Inflicted {ailment_type} on player"))
        else:
            if not player.in_battle or not player.current_enemy:
                return jsonify(create_error_response("Not in battle")), 400
            
            enemy = Enemy.from_dict(player.current_enemy)
            enemy.add_ailment(ailment)
            player.current_enemy = enemy.to_dict()
            user_db.save_user(session_id, player.to_dict())
            
            return jsonify(create_success_response({
                'ailment': ailment.to_dict(),
                'enemy': enemy.to_dict()
            }, f"Inflicted {ailment_type} on enemy"))
        
    except Exception as e:
        return jsonify(create_error_response(f"Error inflicting ailment: {str(e)}")), 500


@dev_bp.route('/dev/modify-stats', methods=['POST'])
def modify_stats():
    """Modify player stats for testing."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        # Modify stats - update max_health first so health isn't capped to old max
        if 'max_health' in data:
            player.max_health = data['max_health']
        if 'health' in data:
            player.health = min(data['health'], player.max_health)
        if 'gold' in data:
            player.gold = data['gold']
        if 'attack_power' in data:
            player.attack_power = data['attack_power']
        if 'defense' in data:
            player.defense = data['defense']
        if 'speed' in data:
            player.speed = data['speed']
        if 'level' in data:
            player.level = data['level']
        if 'floor' in data:
            player.floor = data['floor']
        
        user_db.save_user(session_id, player.to_dict())
        
        return jsonify(create_success_response({
            'player': player.to_dict()
        }, "Stats modified successfully"))
        
    except Exception as e:
        return jsonify(create_error_response(f"Error modifying stats: {str(e)}")), 500


@dev_bp.route('/dev/end-battle', methods=['POST'])
def end_battle():
    """Force end current battle."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        player.end_battle()
        user_db.save_user(session_id, player.to_dict())
        
        return jsonify(create_success_response({
            'player': player.to_dict()
        }, "Battle ended"))
        
    except Exception as e:
        return jsonify(create_error_response(f"Error ending battle: {str(e)}")), 500


@dev_bp.route('/dev/list-allies', methods=['POST'])
def list_allies():
    """List all available predefined allies."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        
        # Get player's current allies
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        from .models.ally import PREDEFINED_ALLIES
        return jsonify(create_success_response({
            'available_allies': PREDEFINED_ALLIES,
            'player_allies': [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies],
            'ally_count': len(player.allies)
        }, f"Player has {len(player.allies)} allies"))
    except Exception as e:
        return jsonify(create_error_response(f"Error listing allies: {str(e)}")), 500


@dev_bp.route('/dev/change-floor', methods=['POST'])
def change_floor():
    """Change player's floor and reset room state."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        new_floor = data.get('floor', 1)
        
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        # Change floor
        old_floor = player.floor
        player.floor = new_floor
        
        # Use movement controller to generate a proper floor
        from .controllers import MovementController
        movement_controller = MovementController()
        movement_controller.set_session(session_id)
        
        # Ensure the floor is generated
        movement_controller.ensure_floor_generated(new_floor)
        
        # Set player to the start room of the new floor
        # The start room is always "start" and movement controller will find it
        player.room_id = "start"
        
        # Clear visited rooms for new floor
        player.visited_rooms = set()
        player.visited_rooms.add(player.room_id)
        
        # Reset minimap data
        player.room_positions = {player.room_id: {'x': 0, 'y': 0}}
        player.room_info = {}
        
        # Clear battle state if any
        if player.in_battle:
            player.end_battle()
        
        user_db.save_user(session_id, player.to_dict())
        
        # Get the start room info for the UI
        start_room = movement_controller.get_room_for_session("start", new_floor, session_id)
        room_info = start_room.to_dict() if start_room else None
        
        return jsonify(create_success_response({
            'player': player.to_dict(),
            'room_info': room_info,
            'old_floor': old_floor,
            'new_floor': new_floor
        }, f"Changed floor from {old_floor} to {new_floor}"))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(create_error_response(f"Error changing floor: {str(e)}")), 500


@dev_bp.route('/dev/get-player-info', methods=['POST'])
def get_player_info():
    """Get detailed player information."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        return jsonify(create_success_response({
            'player': player.to_dict(),
            'stats': {
                'health': f"{player.health}/{player.max_health}",
                'gold': player.gold,
                'attack': player.attack_power,
                'defense': player.defense,
                'speed': player.speed,
                'level': player.level,
                'floor': player.floor,
                'in_battle': player.in_battle,
                'allies': len(player.allies),
                'ailments': len(player.ailments)
            }
        }, "Player info retrieved"))
        
    except Exception as e:
        return jsonify(create_error_response(f"Error getting player info: {str(e)}")), 500


@dev_bp.route('/dev/add-item', methods=['POST'])
def add_item():
    """Add items to player inventory."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        from .models.item import Item
        
        data = request.json
        session_id = data.get('session_id')
        item_type = data.get('item_type')
        quantity = data.get('quantity', 1)
        
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        # Add items to inventory
        for _ in range(quantity):
            item = Item(item_type)
            player.inventory.append(item)
        
        # Save player
        user_db.save_user(session_id, player.to_dict())
        
        return jsonify(create_success_response({
            'player': {
                'name': player.name,
                'health': f"{player.health}/{player.max_health}",
                'gold': player.gold,
                'inventory': [item.get_item_info() if hasattr(item, 'get_item_info') else item for item in player.inventory],
                'allies': [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies],
            },
            'inventory_count': len(player.inventory)
        }, f"Added {quantity}x {item_type} to inventory"))
        
    except Exception as e:
        return jsonify(create_error_response(f"Error adding item: {str(e)}")), 500


@dev_bp.route('/dev/add-gear', methods=['POST'])
def add_gear():
    """Add gear to player inventory."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        from .models.gear import Gear
        
        data = request.json
        session_id = data.get('session_id')
        gear_type = data.get('gear_type')
        floor = data.get('floor', 1)
        quantity = data.get('quantity', 1)
        
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        # Add gear to inventory
        for _ in range(quantity):
            if gear_type == 'random':
                gear = Gear.generate_random_gear(floor)
            elif gear_type == 'weapon':
                gear = Gear.generate_weapon(floor)
            elif gear_type == 'armor':
                gear = Gear.generate_armor(floor)
            elif gear_type == 'accessory':
                gear = Gear.generate_accessory(floor)
            else:
                return jsonify(create_error_response(f"Invalid gear type: {gear_type}")), 400
            
            player.inventory.append(gear)
        
        # Save player
        user_db.save_user(session_id, player.to_dict())
        
        return jsonify(create_success_response({
            'player': {
                'name': player.name,
                'health': f"{player.health}/{player.max_health}",
                'gold': player.gold,
                'inventory': [item.get_item_info() if hasattr(item, 'get_item_info') else item for item in player.inventory],
                'allies': [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies],
            },
            'inventory_count': len(player.inventory)
        }, f"Added {quantity}x {gear_type} (floor {floor}) to inventory"))
        
    except Exception as e:
        return jsonify(create_error_response(f"Error adding gear: {str(e)}")), 500


@dev_bp.route('/dev/clear-inventory', methods=['POST'])
def clear_inventory():
    """Clear all items from player inventory."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        # Clear inventory
        old_count = len(player.inventory)
        player.inventory = []
        
        # Save player
        user_db.save_user(session_id, player.to_dict())
        
        return jsonify(create_success_response({
            'player': {
                'name': player.name,
                'health': f"{player.health}/{player.max_health}",
                'gold': player.gold,
                'inventory': [],
                'allies': [ally.to_dict() if hasattr(ally, 'to_dict') else ally for ally in player.allies],
            },
            'items_removed': old_count
        }, f"Cleared {old_count} items from inventory"))
        
    except Exception as e:
        return jsonify(create_error_response(f"Error clearing inventory: {str(e)}")), 500


@dev_bp.route('/dev/spawn-casino', methods=['POST'])
def spawn_casino():
    """Convert current room to a casino."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        session_id = data.get('session_id')
        
        # Get player
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        # Get current room from movement controller
        from .controllers import MovementController
        from .utils import RoomDB
        
        room_db = RoomDB(current_app.config['DATA_DIR'])
        movement_controller = MovementController(room_db)
        movement_controller.set_session(session_id)
        
        current_room = movement_controller.get_room(player.room_id, player.floor)
        
        if not current_room:
            return jsonify(create_error_response("Current room not found")), 404
        
        print(f"DEBUG spawn_casino: Converting room {player.room_id} on floor {player.floor} to casino")
        
        # Convert room to casino
        current_room.set_casino()
        current_room.name = "The Lucky Dice Casino"
        current_room.description = "A glittering casino run by mysterious figures. The sound of shuffling cards and rolling dice fills the air."
        
        print(f"DEBUG spawn_casino: Room is_casino={current_room.is_casino}, saving to DB...")
        
        # Save the room using the movement controller's _save_room method
        # This ensures it's saved in the correct format and location
        success = movement_controller._save_room(current_room)
        
        if success:
            print(f"DEBUG spawn_casino: Room saved successfully via movement controller")
        else:
            print(f"DEBUG spawn_casino: Failed to save room via movement controller")
        
        # Get room dict and use it for room_info
        room_dict = current_room.to_dict()
        
        return jsonify(create_success_response({
            'room': room_dict,
            'room_info': room_dict,
            'player': {
                'name': player.name,
                'health': f"{player.health}/{player.max_health}",
                'gold': player.gold,
                'floor': player.floor,
                'room_id': player.room_id
            }
        }, "Current room converted to casino!"))
        
    except Exception as e:
        return jsonify(create_error_response(f"Error spawning casino: {str(e)}")), 500


@dev_bp.route('/dev/unlock-achievement', methods=['POST'])
def unlock_achievement():
    """Unlock a specific achievement for a player (dev only)."""
    if not verify_dev_key():
        return jsonify(create_error_response("Access Denied")), 403
    
    try:
        data = request.json
        if not data:
            return jsonify(create_error_response("No data provided")), 400
        
        session_id = data.get('session_id')
        achievement_id = data.get('achievement_id')
        
        if not session_id or not achievement_id:
            return jsonify(create_error_response("Missing session_id or achievement_id")), 400
        
        user_db = get_user_db()
        player_data = user_db.get_user(session_id)
        
        if not player_data:
            return jsonify(create_error_response("Player not found")), 404
        
        player = Player.from_dict(player_data)
        
        # Get achievement info
        from app.models.achievement import Achievement
        achievement = Achievement.get_achievement(achievement_id)
        
        if not achievement:
            return jsonify(create_error_response("Achievement not found")), 404
        
        # Set stats to meet requirement (cheat for dev testing)
        stat_name = achievement.requirement.get('stat')
        required_value = achievement.requirement.get('value', 0)
        
        if stat_name:
            player.stats[stat_name] = required_value
        
        # Unlock achievement
        was_unlocked, reward = player.unlock_achievement(achievement_id)
        
        if not was_unlocked:
            return jsonify(create_success_response({
                'already_unlocked': True,
                'achievement': {
                    'id': achievement['id'],
                    'name': achievement['name'],
                    'emoji': achievement['emoji']
                }
            }, "Achievement was already unlocked"))
        
        # Save player
        user_db.save_user(session_id, player.to_dict())
        
        return jsonify(create_success_response({
            'unlocked': True,
            'achievement': {
                'id': achievement['id'],
                'name': achievement['name'],
                'description': achievement['description'],
                'emoji': achievement['emoji'],
                'reward': reward
            },
            'player': {
                'gold': player.gold,
                'total_achievements': len(player.achievements)
            }
        }, f"Unlocked {achievement.emoji} {achievement.name} (+{reward} gold)"))
        
    except Exception as e:
        return jsonify(create_error_response(f"Error unlocking achievement: {str(e)}")), 500



