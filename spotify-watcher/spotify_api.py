"""
Spotify API interaction classes
"""
import requests
from datetime import datetime
from typing import List, Dict, Optional


class GetRecentlyPlayed:
    """Handles retrieving recently played tracks from Spotify API"""

    def __init__(self, access_token):
        self.access_token = access_token
        self.api_endpoint = "https://api.spotify.com/v1/me/player/recently-played"
        self.MAX_LIMIT = 50  # Spotify API limit for recently played tracks

    def get_recently_played(self, limit=10, after: str|int=None, before: str|int=None) -> dict | None:
        """
        Get recently played tracks from Spotify API
        
        Args:
            limit (int): Number of tracks to retrieve (1-50)
            after (str|int): Unix timestamp - return tracks played after this time
            before (str|int): Unix timestamp - return tracks played before this time
            
        Returns:
            dict: JSON response from Spotify API containing recently played tracks
            
        Raises:
            ValueError: If parameters are invalid
            Exception: If API request fails
        """
        # Check that limit is between 1 and MAX_LIMIT
        if not (1 <= limit <= self.MAX_LIMIT):
            raise ValueError(f"Limit must be between 1 and {self.MAX_LIMIT}")
        
        # Only one of after or before can be set
        if after is not None and before is not None:
            raise ValueError("Only one of 'after' or 'before' can be set")
        
        # Make sure after or before are integers
        if after is not None:
            after = int(after)
        if before is not None:
            before = int(before)

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        params = {"limit": limit}
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
            
        response = requests.get(self.api_endpoint, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Failed to get recently played: {response.status_code} - {response.text}")
            # TODO: Handle rate limiting (HTTP 429) and other potential errors
            # See "Retry-After" header in response for rate limiting



        response_json = response.json()
        return response_json

    def parse_track_history(self, spotify_response: dict, selfopticon_user_id: str, spotify_user_id: str) -> List[Dict]:
        """
        Parse Spotify API response into structured track history records
        
        Args:
            spotify_response (dict): Raw response from Spotify recently played API
            selfopticon_user_id (str): Internal user ID for selfopticon system
            spotify_user_id (str): Spotify user ID
            
        Returns:
            List[Dict]: List of structured track history records matching the database schema
        """
        track_history = []
        
        if not spotify_response or 'items' not in spotify_response:
            return track_history
            
        for item in spotify_response['items']:
            try:
                track = item.get('track', {})
                album = track.get('album', {})
                artists = track.get('artists', [])
                
                # Parse played_at timestamp to datetime
                played_at_str = item.get('played_at')
                played_at = datetime.fromisoformat(played_at_str.replace('Z', '+00:00')) if played_at_str else None
                
                # Get first artist info (if available)
                first_artist_id = artists[0].get('id') if artists else None
                first_artist_name = artists[0].get('name') if artists else None
                
                record = {
                    'played_at': played_at,
                    'selfopticon_user_id': selfopticon_user_id,
                    'spotify_user_id': spotify_user_id,
                    'track_id': track.get('id'),
                    'track_name': track.get('name'),
                    'track_duration_ms': track.get('duration_ms'),
                    'track_popularity': track.get('popularity'),
                    'album_id': album.get('id'),
                    'album_name': album.get('name'),
                    'first_artist_id': first_artist_id,
                    'first_artist_name': first_artist_name
                }
                
                # Only add records with required fields
                if all(record[field] is not None for field in ['played_at', 'selfopticon_user_id', 'spotify_user_id', 'track_id', 'track_name', 'track_duration_ms']):
                    track_history.append(record)
                    
            except Exception as e:
                # Log the error but continue processing other tracks
                print(f"Error parsing track item: {e}")
                continue
                
        return track_history

    def get_parsed_track_history(self, selfopticon_user_id: str, spotify_user_id: str, limit=10, after: str|int=None, before: str|int=None) -> List[Dict]:
        """
        Get recently played tracks and return them as parsed structured data
        
        Args:
            selfopticon_user_id (str): Internal user ID for selfopticon system
            spotify_user_id (str): Spotify user ID
            limit (int): Number of tracks to retrieve (1-50)
            after (str|int): Unix timestamp - return tracks played after this time
            before (str|int): Unix timestamp - return tracks played before this time
            
        Returns:
            List[Dict]: List of structured track history records
        """
        raw_response = self.get_recently_played(limit=limit, after=after, before=before)
        return self.parse_track_history(raw_response, selfopticon_user_id, spotify_user_id)
