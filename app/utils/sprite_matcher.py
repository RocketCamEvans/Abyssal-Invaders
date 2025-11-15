"""
Sprite matching utility for finding the best monster sprite based on enemy description.
"""

import os
from typing import List, Dict, Optional
from pathlib import Path


class SpriteMatcher:
    """
    Matches enemy descriptions to sprite filenames using tag-based scoring.
    """
    
    def __init__(self, sprites_dir: str = None):
        """
        Initialize the sprite matcher.
        
        Args:
            sprites_dir: Path to sprites directory
        """
        if sprites_dir is None:
            # Default to app/sprites directory
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sprites_dir = os.path.join(app_dir, 'sprites')
        
        self.sprites_dir = sprites_dir
        self.sprite_cache: Dict[str, List[Dict[str, str]]] = {}
        self._load_sprites()
    
    def _load_sprites(self):
        """Load all available monster sprites and parse their tags."""
        if not os.path.exists(self.sprites_dir):
            print(f"WARNING: Sprites directory not found: {self.sprites_dir}")
            return
        
        sprites = []
        for filename in os.listdir(self.sprites_dir):
            if filename.startswith('monster_') and filename.endswith('.png'):
                # Extract tags from filename
                # Format: monster_tag1_tag2_tag3.png
                name_without_ext = filename[:-4]  # Remove .png
                name_without_prefix = name_without_ext[8:]  # Remove "monster_"
                tags = name_without_prefix.split('_')
                
                sprites.append({
                    'filename': filename,
                    'path': f'/static/sprites/{filename}',
                    'tags': tags,
                    'tags_lower': [tag.lower() for tag in tags]
                })
        
        self.sprite_cache['all'] = sprites
        print(f"Loaded {len(sprites)} monster sprites")
    
    def find_best_match(self, enemy_name: str, enemy_description: str = '') -> Optional[Dict[str, str]]:
        """
        Find the best matching sprite for an enemy based on name and description.
        
        Args:
            enemy_name: Name of the enemy
            enemy_description: Description of the enemy
            
        Returns:
            Dict with 'filename', 'path', and 'tags', or None if no sprites available
        """
        sprites = self.sprite_cache.get('all', [])
        if not sprites:
            print(f"WARNING: No sprites loaded!")
            return None
        
        print(f"=== SPRITE MATCHING for '{enemy_name}' ===")
        print(f"Description: {enemy_description[:100]}..." if len(enemy_description) > 100 else f"Description: {enemy_description}")
        print(f"Total sprites available: {len(sprites)}")
        
        # Combine name and description for matching
        search_text = f"{enemy_name} {enemy_description}".lower()
        search_words = set(search_text.split())
        print(f"Search words: {search_words}")
        
        # Score each sprite based on tag matches
        scored_sprites = []
        for sprite in sprites:
            score = 0
            matched_tags = []
            
            for tag in sprite['tags_lower']:
                # Exact word match
                if tag in search_words:
                    score += 10
                    matched_tags.append(tag)
                # Partial match (tag contained in search text)
                elif tag in search_text:
                    score += 5
                    matched_tags.append(tag)
                # Search word contained in tag
                else:
                    for word in search_words:
                        if len(word) > 3 and word in tag:
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
        
        print(f"Found {len(scored_sprites)} sprites with matches")
        if scored_sprites:
            # Show top 3 matches
            for i, match in enumerate(scored_sprites[:3]):
                print(f"  {i+1}. {match['sprite']['filename']} - score: {match['score']}, tags: {match['matched_tags']}")
        
        if scored_sprites:
            best_match = scored_sprites[0]['sprite']
            print(f"✓ Selected: '{best_match['filename']}' (score: {scored_sprites[0]['score']})")
            return best_match
        
        # If no matches, return a random sprite as fallback
        import random
        fallback = random.choice(sprites)
        print(f"✗ No match found for '{enemy_name}', using random sprite: {fallback['filename']}")
        return fallback
    
    def get_all_sprites(self) -> List[Dict[str, str]]:
        """
        Get list of all available sprites.
        
        Returns:
            List of sprite dictionaries
        """
        return self.sprite_cache.get('all', [])


# Global sprite matcher instance
_sprite_matcher = None


def get_sprite_matcher() -> SpriteMatcher:
    """Get or create the global sprite matcher instance."""
    global _sprite_matcher
    if _sprite_matcher is None:
        _sprite_matcher = SpriteMatcher()
    return _sprite_matcher
