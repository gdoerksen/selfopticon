# Spotify Watcher

A Python application to track and save a user's recently played Spotify tracks with structured data parsing for database integration.

## Project Structure

```
spotify_watcher/
├── main.py          # Main entry point
├── auth.py          # Authentication classes
├── spotify_api.py   # Spotify API interaction classes
├── test_parser.py   # Test script for parsing functionality
├── pyproject.toml   # Project configuration
├── .env             # Environment variables (not included)
└── README.md        # This file
```

## Modules

### `auth.py`
Contains authentication-related classes:
- `RequestUserAuthorization`: Handles initial OAuth flow
- `RequestAccessToken`: Exchanges authorization code for access token
- `RefreshToken`: Refreshes access tokens using refresh token

### `spotify_api.py`
Contains Spotify API interaction classes:
- `GetRecentlyPlayed`: Retrieves recently played tracks from Spotify
  - `get_recently_played()`: Returns raw JSON from Spotify API
  - `parse_track_history()`: Parses raw JSON into structured database records
  - `get_parsed_track_history()`: Combined method that fetches and parses in one call

### `main.py`
Main script that orchestrates the application flow.

## Data Structure

The parser converts Spotify API responses into structured records for the `tbl_user_spotify_track_history` table:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `played_at` | datetime | ✓ | When the track was played |
| `selfopticon_user_id` | string | ✓ | Internal user ID |
| `spotify_user_id` | string | ✓ | Spotify user ID |
| `track_id` | string | ✓ | Spotify track ID |
| `track_name` | string | ✓ | Track name |
| `track_duration_ms` | integer | ✓ | Track duration in milliseconds |
| `track_popularity` | integer | | Spotify popularity score (0-100) |
| `album_id` | string | | Spotify album ID |
| `album_name` | string | | Album name |
| `first_artist_id` | string | | First artist's Spotify ID |
| `first_artist_name` | string | | First artist's name |

## Usage

### Basic Usage
Run the main script to fetch and save recently played tracks:

```bash
python main.py
```

This will create a `recently_played.json` file with your recent listening history and demonstrate the parsing functionality.

### Advanced Usage with Parsed Data

```python
from spotify_api import GetRecentlyPlayed
from auth import RefreshToken

# Get access token
token_refresher = RefreshToken()
access_token = token_refresher.refresh()

# Create API client
spotify_api = GetRecentlyPlayed(access_token)

# Get parsed track history ready for database insertion
parsed_tracks = spotify_api.get_parsed_track_history(
    selfopticon_user_id="your_internal_user_id",
    spotify_user_id="spotify_user_id", 
    limit=50
)

# Insert into your database
for track in parsed_tracks:
    # Insert track record into tbl_user_spotify_track_history
    pass
```

### Testing the Parser

```bash
python test_parser.py
```

This will demonstrate the parsing functionality and create a `parsed_track_history.json` file with sample structured data.

## Environment Variables

Make sure to set up your `.env` file with the following variables:
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REFRESH_TOKEN`
- `SPOTIFY_REDIRECT_URI`