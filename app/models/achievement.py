"""Achievement model for tracking player accomplishments."""

class Achievement:
    """Represents an achievement that players can unlock."""
    
    # Achievement definitions
    ACHIEVEMENTS = {
        'first_blood': {
            'id': 'first_blood',
            'name': 'First Blood',
            'description': 'Defeat your first enemy',
            'emoji': '🩸',
            'reward': 50,
            'type': 'combat',
            'requirement': 1
        },
        'seasoned_warrior': {
            'id': 'seasoned_warrior',
            'name': 'Seasoned Warrior',
            'description': 'Defeat 10 enemies',
            'emoji': '🗡️',
            'reward': 100,
            'type': 'combat',
            'requirement': 10
        },
        'veteran_slayer': {
            'id': 'veteran_slayer',
            'name': 'Veteran Slayer',
            'description': 'Defeat 50 enemies',
            'emoji': '⚔️',
            'reward': 300,
            'type': 'combat',
            'requirement': 50
        },
        'legendary_warrior': {
            'id': 'legendary_warrior',
            'name': 'Legendary Warrior',
            'description': 'Defeat 100 enemies',
            'emoji': '👑',
            'reward': 1000,
            'type': 'combat',
            'requirement': 100
        },
        'speed_demon': {
            'id': 'speed_demon',
            'name': 'Speed Demon',
            'description': 'Land 2 critical hits in one battle',
            'emoji': '⚡',
            'reward': 200,
            'type': 'combat',
            'requirement': 2
        },
        'explorer': {
            'id': 'explorer',
            'name': 'Explorer',
            'description': 'Visit 20 different rooms',
            'emoji': '🗺️',
            'reward': 100,
            'type': 'exploration',
            'requirement': 20
        },
        'floor_10': {
            'id': 'floor_10',
            'name': 'Depth Crawler',
            'description': 'Reach floor 10',
            'emoji': '🔟',
            'reward': 300,
            'type': 'progression',
            'requirement': 10
        },
        'floor_25': {
            'id': 'floor_25',
            'name': 'Abyss Walker',
            'description': 'Reach floor 25',
            'emoji': '🕳️',
            'reward': 700,
            'type': 'progression',
            'requirement': 25
        },
        'wealthy': {
            'id': 'wealthy',
            'name': 'Wealthy Adventurer',
            'description': 'Accumulate 1000 gold',
            'emoji': '💰',
            'reward': 200,
            'type': 'wealth',
            'requirement': 1000
        },
        'rich': {
            'id': 'rich',
            'name': 'Rich Tycoon',
            'description': 'Accumulate 5000 gold',
            'emoji': '💎',
            'reward': 500,
            'type': 'wealth',
            'requirement': 5000
        },
        'shopaholic': {
            'id': 'shopaholic',
            'name': 'Shopaholic',
            'description': 'Purchase 10 items from shops',
            'emoji': '🛒',
            'reward': 150,
            'type': 'shopping',
            'requirement': 10
        },
        'lucky_streak': {
            'id': 'lucky_streak',
            'name': 'Lucky Streak',
            'description': 'Win 500 gold in a single casino game',
            'emoji': '🎰',
            'reward': 100,
            'type': 'casino',
            'requirement': 500
        },
        'high_roller': {
            'id': 'high_roller',
            'name': 'High Roller',
            'description': 'Win 1000 gold total from casino games',
            'emoji': '🎲',
            'reward': 200,
            'type': 'casino',
            'requirement': 1000
        },
        'party_leader': {
            'id': 'party_leader',
            'name': 'Party Leader',
            'description': 'Recruit 3 different allies',
            'emoji': '👥',
            'reward': 150,
            'type': 'allies',
            'requirement': 3
        },
        'critical_master': {
            'id': 'critical_master',
            'name': 'Critical Master',
            'description': 'Land 4 critical hits in one battle',
            'emoji': '💥',
            'reward': 400,
            'type': 'combat',
            'requirement': 4
        },
        'untouchable': {
            'id': 'untouchable',
            'name': 'Untouchable',
            'description': 'Win a battle without taking damage',
            'emoji': '🛡️',
            'reward': 400,
            'type': 'combat',
            'requirement': 1
        },
        'fullmetal': {
            'id': 'fullmetal',
            'name': 'Fullmetal',
            'description': 'Equip a weapon, armor, and accessory',
            'emoji': '⚙️',
            'reward': 100,
            'type': 'equipment',
            'requirement': 1
        },
        'bullseye': {
            'id': 'bullseye',
            'name': 'Bullseye',
            'description': 'Land 10 perfectly timed hits in a row',
            'emoji': '🎯',
            'reward': 300,
            'type': 'combat',
            'requirement': 10
        },
        'king_of_hell': {
            'id': 'king_of_hell',
            'name': 'King of Hell',
            'description': 'Reach floor 100',
            'emoji': '👹',
            'reward': 2000,
            'type': 'progression',
            'requirement': 100,
            'hidden': True,
            'hint': 'HINT: Push forward and never stop'
        },
        'one_punch': {
            'id': 'one_punch',
            'name': 'One Punch Person',
            'description': 'Deal 500+ damage in one attack',
            'emoji': '👊',
            'reward': 500,
            'type': 'combat',
            'requirement': 500
        },
        'close_call': {
            'id': 'close_call',
            'name': 'Close Call',
            'description': 'Win a battle with exactly 1 HP remaining',
            'emoji': '💀',
            'reward': 250,
            'type': 'combat',
            'requirement': 1,
            'hidden': True,
            'hint': 'HINT: How far can you push yourself to the brink of destruction?'
        },
        'hephaestus': {
            'id': 'hephaestus',
            'name': 'From Hephaestus, to Achilles',
            'description': 'Equip legendary gear in all three slots',
            'emoji': '🔱',
            'reward': 800,
            'type': 'equipment',
            'requirement': 1,
            'hidden': True,
            'hint': 'HINT: Forged by gods'
        },
        'pantheon': {
            'id': 'pantheon',
            'name': 'Pantheon',
            'description': 'Recruit every unique ally',
            'emoji': '🏛️',
            'reward': 128,
            'type': 'allies',
            'requirement': 1,
            'hidden': True,
            'hint': 'HINT: Everyone\'s here!'
        },
        'qa': {
            'id': 'qa',
            'name': 'QA',
            'description': 'Use 50 items',
            'emoji': '🧪',
            'reward': 300,
            'type': 'items',
            'requirement': 50,
            'hidden': True,
            'hint': 'HINT:Consume, consume, consume'
        }
    }
    
    @staticmethod
    def get_all():
        """Get all achievement definitions as a list."""
        return list(Achievement.ACHIEVEMENTS.values())
    
    @staticmethod
    def get_achievement(achievement_id):
        """Get a specific achievement by ID."""
        return Achievement.ACHIEVEMENTS.get(achievement_id)
    
    @staticmethod
    def check_progress(achievement, player_stats):
        """
        Check progress towards an achievement.
        
        Args:
            achievement: Achievement dict
            player_stats: Player stats dict
            
        Returns:
            float: Progress ratio (0.0 to 1.0+)
        """
        if not achievement or not player_stats:
            return 0.0
        
        achievement_type = achievement.get('type')
        requirement = achievement.get('requirement', 1)
        
        # Map achievement types to stat keys
        stat_mapping = {
            'combat': 'enemies_defeated',
            'exploration': 'rooms_visited',
            'shopping': 'items_purchased',
            'casino': 'casino_winnings',
            'allies': 'allies_recruited',
            'wealth': 'gold',
            'equipment': 'fully_equipped',
            'items': 'items_used',
        }
        
        # Special handling for specific achievements
        achievement_id = achievement.get('id')
        
        # Wealth achievements - check 'gold' key directly (player's gold balance is passed in stats as 'gold')
        if achievement_id in ['wealthy', 'rich']:
            current = player_stats.get('gold', 0)
            return min(current / requirement, 1.0)
        elif achievement_id in ['floor_10', 'floor_25', 'king_of_hell']:
            # Floor progression achievements
            current = player_stats.get('highest_floor_reached', 0)
            return min(current / requirement, 1.0)
        elif achievement_id in ['critical_master', 'speed_demon']:
            # Critical hits in one battle
            current = player_stats.get('critical_hits_this_battle', 0)
            return min(current / requirement, 1.0)
        elif achievement_id == 'bullseye':
            # Consecutive perfectly timed hits
            current = player_stats.get('consecutive_perfect_hits', 0)
            return min(current / requirement, 1.0)
        elif achievement_id == 'one_punch':
            # Max damage in one hit
            current = player_stats.get('max_damage_dealt', 0)
            return min(current / requirement, 1.0)
        elif achievement_id in ['untouchable', 'close_call']:
            # Battle victory conditions - special case, can't track progress
            return 0.0
        elif achievement_id == 'lucky_streak':
            # Single game win - special case, can't track progress easily
            return 0.0
        elif achievement_id == 'fullmetal':
            # Equipment check
            current = player_stats.get('fully_equipped', 0)
            return current  # Already 0.0 or 1.0
        elif achievement_id == 'hephaestus':
            # All legendary equipment
            current = player_stats.get('all_legendary_equipped', 0)
            return current  # Already 0.0 or 1.0
        elif achievement_id == 'pantheon':
            # All unique allies recruited
            current = player_stats.get('all_allies_recruited', 0)
            return current  # Already 0.0 or 1.0
        else:
            # Standard stat-based achievements
            stat_key = stat_mapping.get(achievement_type)
            if stat_key:
                current = player_stats.get(stat_key, 0)
                return min(current / requirement, 1.0)
        
        return 0.0

