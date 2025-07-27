"""
SQLite database handler for Spotify track history with automatic deduplication
"""
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SpotifyTrackHistoryDB:
    """SQLite database handler for Spotify track history with automatic deduplication"""
    
    def __init__(self, db_path: str = "spotify_track_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create the track history table with composite unique constraint
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tbl_user_spotify_track_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        played_at DATETIME NOT NULL,
                        selfopticon_user_id TEXT NOT NULL,
                        spotify_user_id TEXT NOT NULL,
                        track_id TEXT NOT NULL,
                        track_name TEXT NOT NULL,
                        track_duration_ms INTEGER NOT NULL,
                        track_popularity INTEGER,
                        album_id TEXT,
                        album_name TEXT,
                        first_artist_id TEXT,
                        first_artist_name TEXT,
                        isrc TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Composite unique constraint for deduplication
                        UNIQUE(played_at, selfopticon_user_id, track_id)
                    )
                """)
                
                # Create indexes for better query performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_played_at 
                    ON tbl_user_spotify_track_history(selfopticon_user_id, played_at DESC)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_track_id 
                    ON tbl_user_spotify_track_history(track_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_artist_id 
                    ON tbl_user_spotify_track_history(first_artist_id)
                """)
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def insert_tracks_bulk(self, tracks: List[Dict]) -> int:
        """
        Bulk insert track history records with automatic deduplication
        
        Args:
            tracks (List[Dict]): List of track history records from parse_track_history()
            
        Returns:
            int: Number of new records inserted (duplicates are ignored)
        """
        if not tracks:
            return 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare the INSERT OR IGNORE statement for deduplication
                insert_sql = """
                    INSERT OR IGNORE INTO tbl_user_spotify_track_history 
                    (played_at, selfopticon_user_id, spotify_user_id, track_id, track_name, 
                     track_duration_ms, track_popularity, album_id, album_name, 
                     first_artist_id, first_artist_name, isrc)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                # Convert track records to tuples for bulk insert
                track_tuples = []
                for track in tracks:
                    
                    track_tuple = (
                        track['played_at'],
                        track['selfopticon_user_id'],
                        track['spotify_user_id'],
                        track['track_id'],
                        track['track_name'],
                        track['track_duration_ms'],
                        track.get('track_popularity'),
                        track.get('album_id'),
                        track.get('album_name'),
                        track.get('first_artist_id'),
                        track.get('first_artist_name'),
                        track.get('isrc')
                    )
                    track_tuples.append(track_tuple)
                
                # Execute bulk insert
                cursor.executemany(insert_sql, track_tuples)
                inserted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Inserted {inserted_count} new track records (out of {len(tracks)} total)")
                return inserted_count
                
        except sqlite3.Error as e:
            logger.error(f"Error inserting tracks: {e}")
            raise
    
    def get_latest_played_at(self, selfopticon_user_id: str) -> Optional[datetime]:
        """
        Get the latest played_at timestamp for a user to determine where to resume fetching
        
        Args:
            selfopticon_user_id (str): User ID to check
            
        Returns:
            datetime | None: Latest played_at timestamp or None if no records exist
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT MAX(played_at) 
                    FROM tbl_user_spotify_track_history 
                    WHERE selfopticon_user_id = ?
                """, (selfopticon_user_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    return datetime.fromisoformat(result[0])
                return None
                
        except sqlite3.Error as e:
            logger.error(f"Error getting latest played_at: {e}")
            raise
    
    def get_track_count(self, selfopticon_user_id: str = None) -> int:
        """
        Get total number of tracks for a user (or all users if None)
        
        Args:
            selfopticon_user_id (str, optional): User ID to filter by
            
        Returns:
            int: Number of track records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if selfopticon_user_id:
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM tbl_user_spotify_track_history 
                        WHERE selfopticon_user_id = ?
                    """, (selfopticon_user_id,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM tbl_user_spotify_track_history")
                
                return cursor.fetchone()[0]
                
        except sqlite3.Error as e:
            logger.error(f"Error getting track count: {e}")
            raise
    
    def get_recent_tracks(self, selfopticon_user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get recent tracks for a user
        
        Args:
            selfopticon_user_id (str): User ID
            limit (int): Number of recent tracks to return
            
        Returns:
            List[Dict]: List of recent track records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM tbl_user_spotify_track_history 
                    WHERE selfopticon_user_id = ?
                    ORDER BY played_at DESC 
                    LIMIT ?
                """, (selfopticon_user_id, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Error getting recent tracks: {e}")
            raise
    
    def get_top_tracks(self, selfopticon_user_id: str, days: int = 7, limit: int = 10) -> List[Dict]:
        """
        Get most played tracks for a user in the last N days
        
        Args:
            selfopticon_user_id (str): User ID
            days (int): Number of days to look back
            limit (int): Number of top tracks to return
            
        Returns:
            List[Dict]: List of top tracks with play counts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT track_name, first_artist_name, COUNT(*) as play_count
                    FROM tbl_user_spotify_track_history 
                    WHERE selfopticon_user_id = ? 
                    AND played_at >= datetime('now', '-' || ? || ' days')
                    GROUP BY track_id, track_name, first_artist_name
                    ORDER BY play_count DESC 
                    LIMIT ?
                """, (selfopticon_user_id, days, limit))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Error getting top tracks: {e}")
            raise
    
    def close(self):
        """Close database connection (SQLite handles this automatically, but included for completeness)"""
        pass
