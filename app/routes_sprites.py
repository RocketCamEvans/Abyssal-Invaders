"""
Sprite-related API routes for the dungeon crawler game.
"""

from flask import request
from .utils import create_error_response, create_success_response


def register_sprite_routes(bp):
    """Register sprite-related routes to the blueprint."""
    
    @bp.route('/enemy/sprite', methods=['POST'])
    def get_enemy_sprite():
        """
        Get the best matching sprite for an enemy.
        
        Expected JSON:
        {
            "enemy_name": "Corrupted Developer",
            "enemy_description": "A twisted programmer..."
        }
        """
        try:
            from .utils.sprite_matcher import get_sprite_matcher
            
            data = request.get_json() or {}
            enemy_name = data.get('enemy_name', '')
            enemy_description = data.get('enemy_description', '')
            
            if not enemy_name:
                return create_error_response("Missing enemy_name"), 400
            
            sprite_matcher = get_sprite_matcher()
            sprite = sprite_matcher.find_best_match(enemy_name, enemy_description)
            
            if sprite:
                return create_success_response({
                    'sprite_path': sprite['path'],
                    'sprite_filename': sprite['filename'],
                    'sprite_tags': sprite['tags']
                }, "Sprite matched successfully")
            else:
                return create_error_response("No sprites available"), 404
                
        except Exception as e:
            return create_error_response(f"Error matching sprite: {str(e)}"), 500

    @bp.route('/player/sprite', methods=['POST'])
    def get_player_sprite():
        """
        Get the best matching player sprite based on player name.
        
        Expected JSON:
        {
            "player_name": "Blayten"
        }
        """
        try:
            import os
            import random
            
            data = request.get_json() or {}
            player_name = data.get('player_name', '')
            
            if not player_name:
                return create_error_response("Missing player_name"), 400
            
            # Get the sprites directory
            app_dir = os.path.dirname(os.path.abspath(__file__))
            sprites_dir = os.path.join(app_dir, 'sprites')
            
            # Find all player sprites (those with player_ prefix)
            player_sprites = []
            if os.path.exists(sprites_dir):
                for filename in os.listdir(sprites_dir):
                    if filename.startswith('player_') and filename.endswith('.png'):
                        # Extract tags from filename
                        name_without_ext = filename[:-4]  # Remove .png
                        name_without_prefix = name_without_ext[7:]  # Remove "player_"
                        tags = ['player'] + name_without_prefix.split('_')
                        
                        player_sprites.append({
                            'filename': filename,
                            'path': f'/static/sprites/{filename}',
                            'tags': tags,
                            'tags_lower': [tag.lower() for tag in tags]
                        })
            
            if not player_sprites:
                # Fallback to a default sprite
                return create_success_response({
                    'sprite_path': '/static/sprites/player_knight_with_dog.png',
                    'sprite_filename': 'player_knight_with_dog.png',
                    'sprite_tags': ['player', 'knight', 'with', 'dog']
                }, "Using default player sprite")
            
            # Try to match player name to sprite tags
            player_name_lower = player_name.lower()
            player_name_words = set(player_name_lower.split())
            
            scored_sprites = []
            for sprite in player_sprites:
                score = 0
                matched_tags = []
                
                for tag in sprite['tags_lower']:
                    # Exact word match in player name
                    if tag in player_name_words:
                        score += 10
                        matched_tags.append(tag)
                    # Partial match (tag contained in player name)
                    elif tag in player_name_lower:
                        score += 5
                        matched_tags.append(tag)
                    # Player name word contained in tag
                    else:
                        for word in player_name_words:
                            if len(word) > 2 and word in tag:
                                score += 3
                                matched_tags.append(tag)
                                break
                
                if score > 0:
                    scored_sprites.append({
                        'sprite': sprite,
                        'score': score,
                        'matched_tags': matched_tags
                    })
            
            # Sort by score (highest first)
            scored_sprites.sort(key=lambda x: x['score'], reverse=True)
            
            # If we have a good match, use it
            if scored_sprites and scored_sprites[0]['score'] >= 5:
                best_match = scored_sprites[0]['sprite']
                return create_success_response({
                    'sprite_path': best_match['path'],
                    'sprite_filename': best_match['filename'],
                    'sprite_tags': best_match['tags']
                }, f"Player sprite matched: {best_match['filename']} (matched: {', '.join(scored_sprites[0]['matched_tags'])})")
            
            # Otherwise, select a random player sprite
            selected_sprite = random.choice(player_sprites)
            
            return create_success_response({
                'sprite_path': selected_sprite['path'],
                'sprite_filename': selected_sprite['filename'],
                'sprite_tags': selected_sprite['tags']
            }, f"Player sprite randomly selected: {selected_sprite['filename']}")
                
        except Exception as e:
            return create_error_response(f"Error selecting player sprite: {str(e)}"), 500

