"""
Spotify API interaction classes
"""
import requests


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

        response_json = response.json()
        return response_json
