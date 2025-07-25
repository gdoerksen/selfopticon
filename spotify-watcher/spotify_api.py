"""
Spotify API interaction classes
"""
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional, Generator


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
                
                # Get ISRC (International Standard Recording Code)
                external_ids = track.get('external_ids', {})
                isrc = external_ids.get('isrc')
                
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
                    'first_artist_name': first_artist_name,
                    'isrc': isrc
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

    def get_all_tracks_since(self, start_time: int, selfopticon_user_id: str, spotify_user_id: str, 
                           end_time: Optional[int] = None, limit: int = 50, 
                           sleep_between_requests: float = 0.1) -> List[Dict]:
        """
        Get all recently played tracks from start_time forward, handling pagination automatically.
        
        Args:
            start_time (int): Unix timestamp in milliseconds - fetch tracks played after this time
            selfopticon_user_id (str): Internal user ID for selfopticon system
            spotify_user_id (str): Spotify user ID
            end_time (int, optional): Unix timestamp in milliseconds - stop fetching tracks after this time.
                                    If None, fetches until current time.
            limit (int): Number of tracks per API call (1-50, default 50 for efficiency)
            sleep_between_requests (float): Seconds to sleep between API calls to respect rate limits
            
        Returns:
            List[Dict]: List of all structured track history records from start_time to end_time
            
        Raises:
            ValueError: If parameters are invalid
            Exception: If API requests fail
        """
        if end_time is None:
            end_time = int(time.time() * 1000)  # Current time in milliseconds
            
        if start_time >= end_time:
            raise ValueError("start_time must be before end_time")
            
        all_tracks = []
        current_after = start_time
        
        print(f"Fetching tracks from {datetime.fromtimestamp(start_time/1000)} to {datetime.fromtimestamp(end_time/1000)}")
        
        while True:
            try:
                # Get next batch of tracks
                response = self.get_recently_played(limit=limit, after=current_after)
                
                if not response or 'items' not in response or not response['items']:
                    # print("No more tracks found")
                    break
                
                # Parse the tracks
                parsed_tracks = self.parse_track_history(response, selfopticon_user_id, spotify_user_id)
                
                # Filter tracks that are within our time range
                filtered_tracks = []
                for track in parsed_tracks:
                    track_time_ms = int(track['played_at'].timestamp() * 1000)
                    if track_time_ms <= end_time:
                        filtered_tracks.append(track)
                    else:
                        print(f"Reached end_time, stopping at track played at {track['played_at']}")
                        all_tracks.extend(filtered_tracks)
                        return all_tracks
                
                all_tracks.extend(filtered_tracks)
                print(f"Fetched {len(filtered_tracks)} tracks, total: {len(all_tracks)}")
                
                # Check if we have more data to fetch
                if 'next' not in response or not response['next']:
                    print("No next page available")
                    break
                    
                # Update cursor for next request
                if 'cursors' in response and 'after' in response['cursors']:
                    current_after = int(response['cursors']['after'])
                else:
                    print("No after cursor found, stopping pagination")
                    break
                
                # Respect rate limits
                if sleep_between_requests > 0:
                    time.sleep(sleep_between_requests)
                    
            except Exception as e:
                print(f"Error during pagination: {e}")
                raise
                
        return all_tracks

    def paginate_tracks_generator(self, start_time: int, selfopticon_user_id: str, spotify_user_id: str,
                                end_time: Optional[int] = None, limit: int = 50,
                                sleep_between_requests: float = 0.1) -> Generator[List[Dict], None, None]:
        """
        Generator that yields batches of tracks from start_time forward, handling pagination.
        Useful for processing large datasets without loading everything into memory.
        
        Args:
            start_time (int): Unix timestamp in milliseconds - fetch tracks played after this time
            selfopticon_user_id (str): Internal user ID for selfopticon system  
            spotify_user_id (str): Spotify user ID
            end_time (int, optional): Unix timestamp in milliseconds - stop fetching tracks after this time.
                                    If None, fetches until current time.
            limit (int): Number of tracks per API call (1-50, default 50 for efficiency)
            sleep_between_requests (float): Seconds to sleep between API calls to respect rate limits
            
        Yields:
            List[Dict]: Batch of structured track history records
            
        Raises:
            ValueError: If parameters are invalid
            Exception: If API requests fail
        """
        if end_time is None:
            end_time = int(time.time() * 1000)  # Current time in milliseconds
            
        if start_time >= end_time:
            raise ValueError("start_time must be before end_time")
            
        current_after = start_time
        
        print(f"Starting pagination from {datetime.fromtimestamp(start_time/1000)} to {datetime.fromtimestamp(end_time/1000)}")
        
        while True:
            try:
                # Get next batch of tracks
                response = self.get_recently_played(limit=limit, after=current_after)
                
                if not response or 'items' not in response or not response['items']:
                    print("No more tracks found")
                    break
                
                # Parse the tracks
                parsed_tracks = self.parse_track_history(response, selfopticon_user_id, spotify_user_id)
                
                # Filter tracks that are within our time range
                filtered_tracks = []
                should_stop = False
                
                for track in parsed_tracks:
                    track_time_ms = int(track['played_at'].timestamp() * 1000)
                    if track_time_ms <= end_time:
                        filtered_tracks.append(track)
                    else:
                        print(f"Reached end_time, stopping at track played at {track['played_at']}")
                        should_stop = True
                        break
                
                if filtered_tracks:
                    yield filtered_tracks
                
                if should_stop:
                    break
                
                # Check if we have more data to fetch
                if 'next' not in response or not response['next']:
                    print("No next page available")
                    break
                    
                # Update cursor for next request
                if 'cursors' in response and 'after' in response['cursors']:
                    current_after = int(response['cursors']['after'])
                else:
                    print("No after cursor found, stopping pagination")
                    break
                
                # Respect rate limits
                if sleep_between_requests > 0:
                    time.sleep(sleep_between_requests)
                    
            except Exception as e:
                print(f"Error during pagination: {e}")
                raise
