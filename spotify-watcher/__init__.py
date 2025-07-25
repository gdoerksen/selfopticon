"""
Spotify Watcher - A Python application to track Spotify listening history
"""

__version__ = "1.0.0"
__author__ = "Your Name"

from .auth import RequestUserAuthorization, RequestAccessToken, RefreshToken
from .spotify_api import GetRecentlyPlayed

__all__ = [
    "RequestUserAuthorization",
    "RequestAccessToken", 
    "RefreshToken",
    "GetRecentlyPlayed"
]
