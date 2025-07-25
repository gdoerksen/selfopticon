# Spotify Watcher

A Python application to track and save a user's recently played Spotify tracks.

## Project Structure

```
spotify-watcher/
├── main.py          # Main entry point
├── auth.py          # Authentication classes
├── spotify_api.py   # Spotify API interaction classes
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

### `main.py`
Main script that orchestrates the application flow.

## Usage

Run the main script to fetch and save recently played tracks:

```bash
python main.py
```

This will create a `recently_played.json` file with your recent listening history.

## Environment Variables

Make sure to set up your `.env` file with the following variables:
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`
- `SPOTIFY_REFRESH_TOKEN`
- `SPOTIFY_REDIRECT_URI`