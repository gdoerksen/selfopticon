"""
Authentication classes for Spotify API
"""
import os
import base64
import secrets
import requests
from urllib.parse import urlparse, parse_qs


class RequestUserAuthorization:
    """Handles the initial user authorization flow for Spotify API"""
    
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.user_id = os.getenv("SPOTIFY_USER_ID")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    def get_authorization(self):
        """Generate authorization URL and handle the callback (not working in headless environments)"""
        # Generate a random state parameter as per RFC-6749 recommendations
        api_endpoint = 'https://accounts.spotify.com/authorize?'        
        
        state = secrets.token_urlsafe(16)
        response_type = "code"
        scope = ' '.join([
            "user-top-read",
            "user-read-recently-played"
        ])
        show_dialog = "false"
        
        query = api_endpoint + \
            f'response_type={response_type}&' + \
            f'client_id={self.client_id}&' + \
            f'scope={scope}&' + \
            f'redirect_uri={self.redirect_uri}&' + \
            f'state={state}&' + \
            f'show_dialog={show_dialog}'
        
        print(f'State: {state}')
        print(query)
        return
        
        response = requests.get(query)

        # Extract the code and state from the response
        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)
        code = query_params.get("code", [None])[0]
        response_state = query_params.get("state", [None])[0]

        # Ensure the state matches the one we generated
        if state != response_state:
            raise ValueError("State mismatch. Possible CSRF attack.")
        return code


class RequestAccessToken:
    """Handles exchanging authorization code for access token"""
    
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    def get_access_token(self, auth_code=None) -> str:
        """Exchange authorization code for access token"""
        self.code = auth_code or os.getenv("SPOTIFY_AUTH_CODE")

        credentials = f"{self.client_id}:{self.client_secret}"
        authorization = "Basic " + base64.urlsafe_b64encode(credentials.encode()).decode()

        api_endpoint = "https://accounts.spotify.com/api/token"
        response = requests.post(
            api_endpoint,
            data={
                "code": self.code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": authorization
            },
        )

        # Check if the response is successful
        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.status_code} - {response.text}")

        response_json = response.json()
        return response_json["access_token"]


class RefreshToken:
    """Handles refreshing access tokens using refresh token"""
    
    def __init__(self):
        self.refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    def refresh(self) -> str:
        """Refresh the access token using the refresh token"""
        api_endpoint = "https://accounts.spotify.com/api/token"
        credentials = f"{self.client_id}:{self.client_secret}"
        authorization = "Basic " + base64.urlsafe_b64encode(credentials.encode()).decode()
        
        response = requests.post(
            api_endpoint,
            data={"grant_type": "refresh_token", "refresh_token": self.refresh_token},
            headers={"Authorization": authorization},
        )

        if response.status_code != 200:
            raise Exception(f"Failed to refresh token: {response.status_code} - {response.text}")

        response_json = response.json()
        return response_json["access_token"]
