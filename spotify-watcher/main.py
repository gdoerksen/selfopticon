"""
Main script for Spotify watcher application
"""
import json
from dotenv import load_dotenv

from auth import RefreshToken
from spotify_api import GetRecentlyPlayed

def main():
    """Main function to run the Spotify watcher"""
    load_dotenv()

    # Get access token using refresh token
    token_refresher = RefreshToken()
    access_token = token_refresher.refresh()

    # Fetch recently played tracks
    recently_played = GetRecentlyPlayed(access_token)
    recently_played_tracks = recently_played.get_recently_played(limit=10)

    # Save the recently played tracks to a file
    with open("recently_played.json", "w") as f:
        json.dump(recently_played_tracks, f, indent=2)
    
    print(f"Successfully saved {len(recently_played_tracks.get('items', []))} recently played tracks to recently_played.json")


if __name__ == "__main__":
    main()