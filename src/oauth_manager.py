"""
OAuth 2.0 Authorization Code Flow implementation for TikTok Ads API

Handles:
- Authorization URL generation
- Token exchange
- Token refresh
- Credential storage
- Error detection and interpretation
"""

import json
import webbrowser
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path
from flask import Flask, request
import threading
import time

from config import Config
from mock_api import get_mock_api, get_mock_oauth_server


class OAuthError(Exception):
    """Custom exception for OAuth-related errors"""
    
    def __init__(self, error_type: str, message: str, suggestion: str = ""):
        self.error_type = error_type
        self.message = message
        self.suggestion = suggestion
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            "error_type": self.error_type,
            "message": self.message,
            "suggestion": self.suggestion
        }


class TikTokOAuthManager:
    """Manages OAuth 2.0 flow for TikTok Ads API"""
    
    AUTHORIZATION_BASE_URL = "https://business-api.tiktok.com/portal/auth"
    TOKEN_URL = "https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/"
    REFRESH_URL = "https://business-api.tiktok.com/open_api/v1.3/oauth2/refresh_token/"
    
    # Required scopes for ad creation
    REQUIRED_SCOPES = ["ad_management", "ad_creation"]
    
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        self.credentials_file = Config.CREDENTIALS_FILE
        self.credentials: Optional[Dict] = None
        self.authorization_code: Optional[str] = None
        
        # Load existing credentials if available
        self._load_credentials()
    
    def _load_credentials(self) -> bool:
        """Load credentials from file"""
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'r') as f:
                    self.credentials = json.load(f)
                return True
            except Exception as e:
                print(f"Warning: Could not load credentials: {e}")
        return False
    
    def _save_credentials(self):
        """Save credentials to file"""
        if self.credentials:
            with open(self.credentials_file, 'w') as f:
                json.dump(self.credentials, f, indent=2)
    
    def has_valid_token(self) -> bool:
        """Check if we have a valid access token"""
        if not self.credentials:
            return False
        
        access_token = self.credentials.get('access_token')
        expires_at = self.credentials.get('expires_at')
        
        if not access_token or not expires_at:
            return False
        
        # Check if token is expired
        expiry = datetime.fromisoformat(expires_at)
        if datetime.now() >= expiry:
            # Try to refresh
            return self._refresh_token()
        
        return True
    
    def get_access_token(self) -> str:
        """Get current access token (refreshing if needed)"""
        if not self.has_valid_token():
            raise OAuthError(
                "NO_TOKEN",
                "No valid access token available",
                "Please run OAuth flow first"
            )
        
        return self.credentials['access_token']
    
    def start_oauth_flow(self) -> str:
        """
        Start OAuth authorization flow
        
        Returns authorization URL for user to visit
        """
        if self.use_mock:
            return self._start_mock_oauth_flow()
        
        # Build authorization URL
        params = {
            "app_id": Config.TIKTOK_APP_ID,
            "state": "random_state_string",  # In production, use secure random
            "redirect_uri": Config.TIKTOK_REDIRECT_URI,
            "scope": ",".join(self.REQUIRED_SCOPES)
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{self.AUTHORIZATION_BASE_URL}?{query_string}"
        
        return auth_url
    
    def _start_mock_oauth_flow(self) -> str:
        """Mock OAuth flow for testing"""
        mock_oauth = get_mock_oauth_server()
        
        # Simulate user authorization
        self.authorization_code = mock_oauth.simulate_user_authorization(
            Config.TIKTOK_APP_ID or "mock_app_id"
        )
        
        # Immediately exchange code for token in mock mode
        self.exchange_code_for_token(self.authorization_code)
        
        return "Mock OAuth completed successfully"
    
    def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Raises OAuthError on failure
        """
        if self.use_mock:
            return self._mock_token_exchange(code)
        
        import requests
        
        payload = {
            "app_id": Config.TIKTOK_APP_ID,
            "secret": Config.TIKTOK_APP_SECRET,
            "auth_code": code
        }
        
        try:
            response = requests.post(self.TOKEN_URL, json=payload)
            data = response.json()
            
            # Check for errors
            if data.get("code") != 0:
                self._handle_token_error(data)
            
            # Extract token data
            token_data = data.get("data", {})
            expires_in = token_data.get("expires_in", 86400)
            
            self.credentials = {
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "advertiser_ids": token_data.get("advertiser_ids", []),
                "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            self._save_credentials()
            return self.credentials
            
        except requests.RequestException as e:
            raise OAuthError(
                "NETWORK_ERROR",
                f"Failed to connect to TikTok API: {str(e)}",
                "Check your internet connection and try again"
            )
    
    def _mock_token_exchange(self, code: str) -> Dict:
        """Mock token exchange for testing"""
        mock_api = get_mock_api()
        
        response = mock_api.exchange_code_for_token(
            code,
            Config.TIKTOK_APP_ID or "mock_app_id",
            Config.TIKTOK_APP_SECRET or "mock_secret"
        )
        
        if response["code"] != 0:
            self._handle_token_error(response)
        
        token_data = response["data"]
        expires_in = token_data.get("expires_in", 86400)
        
        self.credentials = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "advertiser_ids": token_data.get("advertiser_ids", []),
            "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        self._save_credentials()
        return self.credentials
    
    def _refresh_token(self) -> bool:
        """Refresh access token using refresh token"""
        if not self.credentials or not self.credentials.get('refresh_token'):
            return False
        
        if self.use_mock:
            return self._mock_token_refresh()
        
        import requests
        
        payload = {
            "app_id": Config.TIKTOK_APP_ID,
            "secret": Config.TIKTOK_APP_SECRET,
            "refresh_token": self.credentials['refresh_token']
        }
        
        try:
            response = requests.post(self.REFRESH_URL, json=payload)
            data = response.json()
            
            if data.get("code") != 0:
                return False
            
            token_data = data.get("data", {})
            expires_in = token_data.get("expires_in", 86400)
            
            self.credentials.update({
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token", self.credentials['refresh_token']),
                "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            })
            
            self._save_credentials()
            return True
            
        except Exception:
            return False
    
    def _mock_token_refresh(self) -> bool:
        """Mock token refresh for testing"""
        mock_api = get_mock_api()
        
        response = mock_api.refresh_access_token(
            self.credentials.get('refresh_token', '')
        )
        
        if response["code"] != 0:
            return False
        
        token_data = response["data"]
        expires_in = token_data.get("expires_in", 86400)
        
        self.credentials.update({
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", self.credentials['refresh_token']),
            "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat()
        })
        
        self._save_credentials()
        return True
    
    def _handle_token_error(self, error_response: Dict):
        """Interpret and raise appropriate OAuthError"""
        code = error_response.get("code")
        message = error_response.get("message", "Unknown error")
        
        if code == 40100:
            if "client_id" in message.lower() or "app_id" in message.lower():
                raise OAuthError(
                    "INVALID_CLIENT_ID",
                    "Your TikTok App ID is invalid",
                    "Please check your TIKTOK_APP_ID in .env matches your app in TikTok Developer dashboard"
                )
            elif "secret" in message.lower():
                raise OAuthError(
                    "INVALID_CLIENT_SECRET",
                    "Your TikTok App Secret is invalid",
                    "Please check your TIKTOK_APP_SECRET in .env matches your app secret"
                )
            else:
                raise OAuthError(
                    "INVALID_CREDENTIALS",
                    message,
                    "Verify your app credentials in TikTok Developer dashboard"
                )
        
        elif code == 40101:
            raise OAuthError(
                "INVALID_CODE",
                "Authorization code is invalid or expired",
                "Please restart the OAuth flow"
            )
        
        elif code == 40104:
            raise OAuthError(
                "INSUFFICIENT_PERMISSIONS",
                "Your app doesn't have required permissions",
                f"Add these scopes in TikTok Developer dashboard: {', '.join(self.REQUIRED_SCOPES)}"
            )
        
        else:
            raise OAuthError(
                "OAUTH_ERROR",
                message,
                "Check TikTok Ads API documentation for error code: " + str(code)
            )
    
    def interpret_api_error(self, status_code: int, error_response: Dict) -> str:
        """
        Interpret API errors and provide user-friendly explanations
        
        Returns human-readable error message with suggestion
        """
        code = error_response.get("code", status_code)
        message = error_response.get("message", "Unknown error")
        
        if status_code == 401 or code == 40100:
            return (
                "Your TikTok access token is invalid or expired. "
                "I'll help you re-authenticate."
            )
        
        elif status_code == 403 or code == 40104:
            if "permission" in message.lower() or "scope" in message.lower():
                return (
                    "Your app doesn't have permission for ad creation. "
                    "Please go to your TikTok Developer dashboard and add these scopes: "
                    f"{', '.join(self.REQUIRED_SCOPES)}"
                )
            elif "region" in message.lower() or "geo" in message.lower():
                return (
                    "TikTok Ads API is not available in your region. "
                    "You might need to use a VPN or create an account in a supported region."
                )
            else:
                return f"Access denied: {message}"
        
        elif status_code == 429:
            return (
                "TikTok is rate limiting our requests. "
                "Let's wait a moment and try again."
            )
        
        elif status_code >= 500:
            return (
                "TikTok's API is experiencing issues. "
                "This is temporary - would you like to retry or save as draft?"
            )
        
        else:
            return f"API Error: {message}"


def start_oauth_callback_server() -> str:
    """
    Start a local server to handle OAuth callback
    
    Returns the authorization code once received
    """
    app = Flask(__name__)
    received_code = {"code": None}
    
    @app.route('/callback')
    def callback():
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            return f"<h1>OAuth Error</h1><p>{error}</p>", 400
        
        if code:
            received_code["code"] = code
            return "<h1>Success!</h1><p>You can close this window and return to the terminal.</p>"
        
        return "<h1>Error</h1><p>No authorization code received</p>", 400
    
    # Run server in background thread
    def run_server():
        app.run(
            host=Config.OAUTH_SERVER_HOST,
            port=Config.OAUTH_SERVER_PORT,
            debug=False,
            use_reloader=False
        )
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait for code (timeout after 5 minutes)
    timeout = 300
    elapsed = 0
    while received_code["code"] is None and elapsed < timeout:
        time.sleep(1)
        elapsed += 1
    
    if received_code["code"] is None:
        raise OAuthError(
            "TIMEOUT",
            "OAuth flow timed out",
            "Please try again and complete authorization within 5 minutes"
        )
    
    return received_code["code"]