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

    # Fetch recently played tracks (raw JSON)
    recently_played = GetRecentlyPlayed(access_token)
    recently_played_tracks = recently_played.get_recently_played(limit=10)

    # Save the raw recently played tracks to a file
    with open("recently_played.json", "w") as f:
        json.dump(recently_played_tracks, f, indent=2)
    
    print(f"Successfully saved {len(recently_played_tracks.get('items', []))} recently played tracks to recently_played.json")
    
    # Example: Get parsed track history for database insertion
    selfopticon_user_id = "user_123"  # Replace with actual selfopticon user ID
    spotify_user_id = "spotify_user_456"  # Replace with actual Spotify user ID
    
    parsed_tracks = recently_played.parse_track_history(
        recently_played_tracks, 
        selfopticon_user_id, 
        spotify_user_id
    )
    
    pprint_parsed_tracks(parsed_tracks)

def pprint_parsed_tracks(parsed_tracks):
    print(f"Retrieved and parsed {len(parsed_tracks)} track records")
    
    # Here you would typically insert parsed_tracks into your database
    # For demonstration, we'll just print the first few records
    for i, track in enumerate(parsed_tracks[:3]):
        print(f"\nTrack {i+1}:")
        print(f"  Played: {track['played_at']}")
        print(f"  Song: {track['track_name']} by {track['first_artist_name']}")
        print(f"  Album: {track['album_name']}")


def main_with_parsed_data():
    """Alternative main function demonstrating parsed data usage"""
    load_dotenv()

    # Get access token using refresh token
    token_refresher = RefreshToken()
    access_token = token_refresher.refresh()

    # Get parsed track history directly
    recently_played = GetRecentlyPlayed(access_token)
    
    selfopticon_user_id = "user_123"  # Replace with actual selfopticon user ID
    spotify_user_id = "spotify_user_456"  # Replace with actual Spotify user ID
    
    parsed_tracks = recently_played.get_parsed_track_history(
        selfopticon_user_id=selfopticon_user_id,
        spotify_user_id=spotify_user_id,
        limit=10
    )

    pprint_parsed_tracks(parsed_tracks)


if __name__ == "__main__":
    main()
    # Uncomment the line below to test the parsed data functionality
    # main_with_parsed_data()