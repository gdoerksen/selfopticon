"""
Main script for Spotify watcher application
"""
import json
import logging
from dotenv import load_dotenv

from spotify_watcher.auth import RefreshToken
from spotify_watcher.spotify_api import GetRecentlyPlayed
from spotify_watcher.database import SpotifyTrackHistoryDB

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def pprint_parsed_tracks(parsed_tracks):
    """Helper function to pretty print parsed tracks"""
    logger.info(f"Retrieved and parsed {len(parsed_tracks)} track records")
    
    # For demonstration, print the first few records
    for i, track in enumerate(parsed_tracks[:3]):
        logger.info(f"Track {i+1}: {track['track_name']} by {track['first_artist_name']} at {track['played_at']}")


def main():
    """Main function to run the Spotify watcher with sqlite database storage"""
    load_dotenv()
    logger.info("Starting Spotify watcher application")

    # Initialize database
    db = SpotifyTrackHistoryDB()
    
    # Get access token using refresh token
    token_refresher = RefreshToken()
    access_token = token_refresher.refresh()

    # Fetch recently played tracks (raw JSON)
    recently_played = GetRecentlyPlayed(access_token)
    recently_played_tracks = recently_played.get_recently_played(limit=50)

    # Save the raw recently played tracks to a file for debugging
    with open("recently_played.json", "w") as f:
        json.dump(recently_played_tracks, f, indent=2)
    
    logger.info(f"Fetched {len(recently_played_tracks.get('items', []))} recently played tracks from Spotify API")
    
    # Parse tracks for database insertion
    selfopticon_user_id = "1"  # Replace with actual selfopticon user ID
    spotify_user_id = "1"  # Replace with actual Spotify user ID
    
    parsed_tracks = recently_played.parse_track_history(
        recently_played_tracks, 
        selfopticon_user_id, 
        spotify_user_id
    )
    
    logger.info(f"Parsed {len(parsed_tracks)} track records")
    
    # Insert tracks into database with automatic deduplication
    if parsed_tracks:
        inserted_count = db.insert_tracks_bulk(parsed_tracks)
        logger.info(f"Inserted {inserted_count} new tracks into database")
        
        # Show some stats
        total_tracks = db.get_track_count(selfopticon_user_id)
        logger.info(f"Total tracks in database for user {selfopticon_user_id}: {total_tracks}")
        
        # Show recent tracks from database
        recent_tracks = db.get_recent_tracks(selfopticon_user_id, limit=5)
        logger.info("Recent tracks from database:")
        for i, track in enumerate(recent_tracks[:3], 1):
            logger.info(f"  {i}. {track['track_name']} by {track['first_artist_name']} at {track['played_at']}")
    else:
        logger.warning("No tracks were parsed from Spotify response")

def main_with_pagination():
    """Demonstrate pagination with database storage"""
    load_dotenv()
    logger.info("Starting Spotify watcher with pagination")

    # Initialize database
    db = SpotifyTrackHistoryDB()
    
    # Get access token using refresh token
    token_refresher = RefreshToken()
    access_token = token_refresher.refresh()

    # Get parsed track history directly
    recently_played = GetRecentlyPlayed(access_token)
    
    selfopticon_user_id = "1"
    spotify_user_id = "1"
    
    # Check when we last updated
    latest_played_at = db.get_latest_played_at(selfopticon_user_id)
    if latest_played_at:
        logger.info(f"Last update was at: {latest_played_at}")
        start_time_ms = int(latest_played_at.timestamp() * 1000)
    else:
        # First run - get tracks from last 7 days
        from datetime import datetime, timedelta
        start_time = datetime.now() - timedelta(days=7)
        start_time_ms = int(start_time.timestamp() * 1000)
        logger.info("First run - fetching tracks from last 7 days")
    
    # Get all tracks since last update
    try:
        all_tracks = recently_played.get_all_tracks_since(
            start_time=start_time_ms,
            selfopticon_user_id=selfopticon_user_id,
            spotify_user_id=spotify_user_id,
            limit=50
        )
        
        if all_tracks:
            inserted_count = db.insert_tracks_bulk(all_tracks)
            logger.info(f"Pagination complete: inserted {inserted_count} new tracks (out of {len(all_tracks)} fetched)")
            
            # Show stats
            total_tracks = db.get_track_count(selfopticon_user_id)
            logger.info(f"Total tracks in database: {total_tracks}")
            
            # Show top tracks
            top_tracks = db.get_top_tracks(selfopticon_user_id, days=7, limit=5)
            logger.info("Top tracks this week:")
            for i, track in enumerate(top_tracks, 1):
                logger.info(f"  {i}. {track['track_name']} by {track['first_artist_name']} ({track['play_count']} plays)")
        else:
            logger.info("No new tracks found since last update")
            
    except Exception as e:
        logger.error(f"Error during pagination: {e}")
        raise

if __name__ == "__main__":
    # Run basic main function
    main()
    
    # Uncomment to test pagination functionality
    # main_with_pagination()