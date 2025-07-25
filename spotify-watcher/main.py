"""
Generates a new access token on each run
"""
import os

import requests 
from dotenv import load_dotenv
import secrets
from urllib.parse import urlparse, parse_qs
import base64
import json


class RequestUserAuthorization:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.user_id = os.getenv("SPOTIFY_USER_ID")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
    
    def get_authorization(self):
        # Generate a random state parameter as per RFC-6749 recommendations
        # state = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        api_endpoint = 'https://accounts.spotify.com/authorize?'        
        
        state = secrets.token_urlsafe(16)
        response_type = "code"
        scope = ' '.join([
            # "user-read-private",
            # "user-read-email"
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

        # https://my-domain.com/callback?code=NApCCg..BkWtQ&state=34fFs29kd09
        # redirect_uri?code=NApCCg..BkWtQ&state=34fFs29kd09
        # Extract the code and state from the response
        response.url

        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)
        code = query_params.get("code", [None])[0]
        response_state = query_params.get("state", [None])[0]

        # ensure the state matches the one we generated
        if state != response_state:
            raise ValueError("State mismatch. Possible CSRF attack.")
        return code

class RequestAccessToken:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    def get_access_token(self):

        self.code = os.getenv("SPOTIFY_AUTH_CODE") # this should be an input to the function

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

        # check if the response is successful
        if response.status_code != 200:
            raise Exception(f"Failed to get access token: {response.status_code} - {response.text}")

        response_json = response.json()
        return response_json["access_token"]

class RefreshToken:
    def __init__(self):
        self.refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.base_64 = os.getenv("SPOTIFY_BASE_64")

    def refresh(self):
        query = "https://accounts.spotify.com/api/token"
        credentials = f"{self.client_id}:{self.client_secret}"
        authorization = "Basic " + base64.urlsafe_b64encode(credentials.encode()).decode()
        response = requests.post(
            query,
            data={"grant_type": "refresh_token", "refresh_token": self.refresh_token},
            headers={"Authorization": authorization},
        )

        response_json = response.json()
        return response_json["access_token"]

class GetRecentlyPlayed:

    def __init__(self, access_token):
        self.access_token = access_token
        self.api_endpoint = "https://api.spotify.com/v1/me/player/recently-played"
        self.MAX_LIMIT = 50  # Spotify API limit for recently played tracks

    def get_recently_played(self, limit=10, after: str|int=None, before: str|int=None):
        # check that limit is between 1 and MAX_LIMIT
        if not (1 <= limit and limit <= self.MAX_LIMIT):
            raise ValueError(f"Limit must be between 1 and {self.MAX_LIMIT}")
        
        # only one of after or before can be set
        if after is not None and before is not None:
            raise ValueError("Only one of 'after' or 'before' can be set")
        
        # make sure after or before are integers
        if after is not None:
            after = int(after)
        if before is not None:
            before = int(before)

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        response = requests.get(self.api_endpoint, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Failed to get recently played: {response.status_code} - {response.text}")

        response_json = response.json()
        return response_json

if __name__ == "__main__":
    load_dotenv()

    # Uncomment the following lines to run the authorization flow
    # Does not work in a headless environment
    # authorization = RequestUserAuthorization()
    # code = authorization.get_authorization()

    # access_token = RequestAccessToken().get_access_token()

    # token_retriever = RefreshToken()
    # token_retriever.refresh()

    # access_token = os.getenv("SPOTIFY_AUTH_TOKEN")
    access_token = RefreshToken().refresh()

    recently_played = GetRecentlyPlayed(access_token)
    recently_played_tracks = recently_played.get_recently_played(limit=10)

    # save the recently played tracks to a file
    with open("recently_played.json", "w") as f:
        json.dump(recently_played_tracks, f, indent=2)
    

    """
    me/player/recently-played
    
    items
    - a list of tracks

    for each items.track:
    - album.id
    - album.name
    - ? album.release_date
    - artists (list)
        - id, name
    - duration_ms
    - id
    - external_ids (dict)
        - isrc (International Standard Recording Code)
    - name
    - popularity
    - played_at
    
    If we were going full deduplicated then we just need
    - id
    - played_at

    """