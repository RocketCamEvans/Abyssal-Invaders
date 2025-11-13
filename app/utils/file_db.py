"""
File-based database utilities for JSON persistence.
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path


class FileDB:
    """
    Simple file-based database using JSON for persistence.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the file database.
        
        Args:
            data_dir (str): Directory to store data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def _get_file_path(self, filename: str) -> Path:
        """
        Get full path for a data file.
        
        Args:
            filename (str): Name of the data file
            
        Returns:
            Path: Full path to the data file
        """
        if not filename.endswith('.json'):
            filename += '.json'
        return self.data_dir / filename
    
    def load_data(self, filename: str, default: Any = None) -> Any:
        """
        Load data from a JSON file.
        
        Args:
            filename (str): Name of the file to load
            default (Any): Default value if file doesn't exist
            
        Returns:
            Any: Loaded data or default value
        """
        file_path = self._get_file_path(filename)
        
        if not file_path.exists():
            return default if default is not None else {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading {filename}: {e}")
            return default if default is not None else {}
    
    def save_data(self, filename: str, data: Any) -> bool:
        """
        Save data to a JSON file.
        
        Args:
            filename (str): Name of the file to save
            data (Any): Data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        file_path = self._get_file_path(filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (TypeError, IOError) as e:
            print(f"Error saving {filename}: {e}")
            return False
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete a data file.
        
        Args:
            filename (str): Name of the file to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        file_path = self._get_file_path(filename)
        
        try:
            if file_path.exists():
                file_path.unlink()
            return True
        except IOError as e:
            print(f"Error deleting {filename}: {e}")
            return False
    
    def file_exists(self, filename: str) -> bool:
        """
        Check if a data file exists.
        
        Args:
            filename (str): Name of the file to check
            
        Returns:
            bool: True if file exists, False otherwise
        """
        file_path = self._get_file_path(filename)
        return file_path.exists()
    
    def list_files(self) -> List[str]:
        """
        List all JSON files in the data directory.
        
        Returns:
            List[str]: List of filenames (without .json extension)
        """
        try:
            return [f.stem for f in self.data_dir.glob('*.json')]
        except Exception as e:
            print(f"Error listing files: {e}")
            return []


class UserDB(FileDB):
    """
    User-specific database operations.
    """
    
    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        self.users_file = "users"
    
    def get_user(self, session_id: str) -> Optional[Dict]:
        """
        Get user data by session ID.
        
        Args:
            session_id (str): User's session ID
            
        Returns:
            Optional[Dict]: User data or None if not found
        """
        users = self.load_data(self.users_file, {})
        return users.get(session_id)
    
    def save_user(self, session_id: str, user_data: Dict) -> bool:
        """
        Save user data.
        
        Args:
            session_id (str): User's session ID
            user_data (Dict): User data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        users = self.load_data(self.users_file, {})
        users[session_id] = user_data
        return self.save_data(self.users_file, users)
    
    def delete_user(self, session_id: str) -> bool:
        """
        Delete user data.
        
        Args:
            session_id (str): User's session ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        users = self.load_data(self.users_file, {})
        if session_id in users:
            del users[session_id]
            return self.save_data(self.users_file, users)
        return True
    
    def get_all_users(self) -> Dict[str, Dict]:
        """
        Get all user data.
        
        Returns:
            Dict[str, Dict]: All user data keyed by session ID
        """
        return self.load_data(self.users_file, {})


class HighScoreDB(FileDB):
    """
    High score database operations.
    """
    
    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        self.highscores_file = "highscores"
    
    def add_score(self, player_name: str, score: int, floor: int) -> bool:
        """
        Add a new high score.
        
        Args:
            player_name (str): Name of the player
            score (int): Gold score achieved
            floor (int): Floor reached
            
        Returns:
            bool: True if successful, False otherwise
        """
        scores = self.load_data(self.highscores_file, [])
        
        score_entry = {
            "name": player_name,
            "gold": score,
            "floor": floor,
            "timestamp": None  # Could add timestamp if needed
        }
        
        scores.append(score_entry)
        
        # Sort by gold (descending), then by floor (descending)
        scores.sort(key=lambda x: (x["gold"], x["floor"]), reverse=True)
        
        # Keep only top 10 scores
        scores = scores[:10]
        
        return self.save_data(self.highscores_file, scores)
    
    def get_high_scores(self, limit: int = 10) -> List[Dict]:
        """
        Get high scores.
        
        Args:
            limit (int): Maximum number of scores to return
            
        Returns:
            List[Dict]: List of high score entries
        """
        scores = self.load_data(self.highscores_file, [])
        return scores[:limit]
    
    def clear_scores(self) -> bool:
        """
        Clear all high scores.
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.save_data(self.highscores_file, [])


class RoomDB(FileDB):
    """
    Room database operations.
    """
    
    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        self.rooms_file = "rooms"
    
    def get_room(self, room_id: str, floor: int) -> Optional[Dict]:
        """
        Get room data by ID and floor.
        
        Args:
            room_id (str): Room ID
            floor (int): Floor number
            
        Returns:
            Optional[Dict]: Room data or None if not found
        """
        rooms = self.load_data(self.rooms_file, {})
        floor_key = str(floor)
        
        if floor_key in rooms and room_id in rooms[floor_key]:
            return rooms[floor_key][room_id]
        return None
    
    def save_room(self, room_id: str, floor: int, room_data: Dict) -> bool:
        """
        Save room data.
        
        Args:
            room_id (str): Room ID
            floor (int): Floor number
            room_data (Dict): Room data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        rooms = self.load_data(self.rooms_file, {})
        floor_key = str(floor)
        
        if floor_key not in rooms:
            rooms[floor_key] = {}
        
        rooms[floor_key][room_id] = room_data
        return self.save_data(self.rooms_file, rooms)
    
    def get_floor_rooms(self, floor: int) -> Dict[str, Dict]:
        """
        Get all rooms for a specific floor.
        
        Args:
            floor (int): Floor number
            
        Returns:
            Dict[str, Dict]: All rooms on the floor
        """
        rooms = self.load_data(self.rooms_file, {})
        floor_key = str(floor)
        return rooms.get(floor_key, {})