"""
Mock TikTok Ads API for testing without real credentials

This simulates the TikTok Ads API responses for:
- OAuth token exchange
- Music validation
- Ad submission
- Various error scenarios
"""

import random
from typing import Dict, Optional
from datetime import datetime, timedelta


class MockTikTokAPI:
    """Mock implementation of TikTok Ads API"""
    
    # Predefined valid music IDs for testing
    VALID_MUSIC_IDS = [
        "music_123",
        "music_456", 
        "music_789",
        "music_abc",
        "music_xyz"
    ]
    
    # Music IDs that trigger specific errors
    ERROR_MUSIC_IDS = {
        "music_not_found": {"code": "40300", "message": "Music not found"},
        "music_geo_001": {"code": "40301", "message": "Music not available in your region"},
        "music_copyright": {"code": "40302", "message": "Copyright restricted music"},
    }
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.uploaded_music: Dict[str, str] = {}  # filepath -> music_id
    
    def exchange_code_for_token(
        self, 
        code: str, 
        app_id: str, 
        app_secret: str
    ) -> Dict:
        """
        Mock OAuth token exchange
        
        Simulates: POST /oauth2/access_token/
        """
        # Simulate various error scenarios
        if app_id == "invalid_app_id":
            return {
                "code": 40100,
                "message": "Invalid client_id",
                "data": None
            }
        
        if app_secret == "invalid_secret":
            return {
                "code": 40100,
                "message": "Invalid client_secret",
                "data": None
            }
        
        if code == "invalid_code":
            return {
                "code": 40101,
                "message": "Invalid authorization code",
                "data": None
            }
        
        # Successful token exchange
        self.access_token = f"mock_access_token_{random.randint(1000, 9999)}"
        self.token_expires_at = datetime.now() + timedelta(hours=24)
        
        return {
            "code": 0,
            "message": "OK",
            "data": {
                "access_token": self.access_token,
                "advertiser_ids": ["123456789"],
                "expires_in": 86400,
                "refresh_token": f"mock_refresh_token_{random.randint(1000, 9999)}",
                "refresh_expires_in": 2592000
            }
        }
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Mock token refresh
        
        Simulates: POST /oauth2/refresh_token/
        """
        if not refresh_token.startswith("mock_refresh_token_"):
            return {
                "code": 40101,
                "message": "Invalid refresh token",
                "data": None
            }
        
        self.access_token = f"mock_access_token_{random.randint(1000, 9999)}"
        self.token_expires_at = datetime.now() + timedelta(hours=24)
        
        return {
            "code": 0,
            "message": "OK",
            "data": {
                "access_token": self.access_token,
                "expires_in": 86400,
                "refresh_token": f"mock_refresh_token_{random.randint(1000, 9999)}",
                "refresh_expires_in": 2592000
            }
        }
    
    def validate_music(self, music_id: str, access_token: str) -> Dict:
        """
        Mock music validation
        
        Simulates: GET /music/info/
        """
        # Check token
        if not self._validate_token(access_token):
            return {
                "code": 40100,
                "message": "Invalid or expired access token",
                "data": None
            }
        
        # Check for error music IDs
        if music_id in self.ERROR_MUSIC_IDS:
            error = self.ERROR_MUSIC_IDS[music_id]
            return {
                "code": error["code"],
                "message": error["message"],
                "data": None
            }
        
        # Check if music ID exists in valid list or uploaded
        if music_id in self.VALID_MUSIC_IDS or music_id in self.uploaded_music.values():
            return {
                "code": 0,
                "message": "OK",
                "data": {
                    "music_id": music_id,
                    "title": f"Sample Music {music_id}",
                    "artist": "Sample Artist",
                    "duration": 180,
                    "is_commercial": True
                }
            }
        
        # Music not found
        return {
            "code": "40300",
            "message": "Music not found",
            "data": None
        }
    
    def upload_music(self, file_path: str, access_token: str) -> Dict:
        """
        Mock music upload
        
        Simulates: POST /file/music/upload/
        """
        # Check token
        if not self._validate_token(access_token):
            return {
                "code": 40100,
                "message": "Invalid or expired access token",
                "data": None
            }
        
        # Simulate upload success
        music_id = f"music_custom_{random.randint(1000, 9999)}"
        self.uploaded_music[file_path] = music_id
        
        return {
            "code": 0,
            "message": "OK",
            "data": {
                "music_id": music_id,
                "upload_status": "completed"
            }
        }
    
    def create_ad(self, ad_payload: Dict, access_token: str) -> Dict:
        """
        Mock ad creation
        
        Simulates: POST /ad/create/
        """
        # Check token
        if not self._validate_token(access_token):
            return {
                "code": 40100,
                "message": "Invalid or expired access token",
                "data": None
            }
        
        # Validate music if provided
        music_id = ad_payload.get("creative", {}).get("music_id")
        if music_id:
            music_validation = self.validate_music(music_id, access_token)
            if music_validation["code"] != 0:
                return {
                    "code": 40300,
                    "message": f"Invalid music_id: {music_validation['message']}",
                    "data": None
                }
        
        # Simulate geo-restriction (random 5% chance)
        if random.random() < 0.05:
            return {
                "code": 40104,
                "message": "Ad creation not available in your region",
                "data": None
            }
        
        # Successful ad creation
        return {
            "code": 0,
            "message": "OK",
            "data": {
                "ad_id": f"ad_{random.randint(100000, 999999)}",
                "status": "PENDING_REVIEW"
            }
        }
    
    def _validate_token(self, access_token: str) -> bool:
        """Check if access token is valid"""
        if not access_token:
            return False
        
        if access_token == "expired_token":
            return False
        
        if access_token == "revoked_token":
            return False
        
        # In mock mode, accept any token that looks like ours
        if access_token.startswith("mock_access_token_"):
            return True
        
        return access_token == self.access_token
    
    def simulate_scope_error(self, access_token: str) -> Dict:
        """Simulate missing scope error"""
        return {
            "code": 40104,
            "message": "Missing required permission scope: ad_management",
            "data": None
        }


class MockOAuthServer:
    """Mock OAuth authorization server"""
    
    def __init__(self):
        self.authorization_codes: Dict[str, str] = {}
    
    def get_authorization_url(self, app_id: str, redirect_uri: str) -> str:
        """Generate mock authorization URL"""
        return f"http://mock-tiktok-oauth.com/authorize?app_id={app_id}&redirect_uri={redirect_uri}"
    
    def generate_authorization_code(self, app_id: str) -> str:
        """Generate a mock authorization code"""
        code = f"mock_auth_code_{random.randint(10000, 99999)}"
        self.authorization_codes[code] = app_id
        return code
    
    def simulate_user_authorization(self, app_id: str) -> str:
        """Simulate user completing OAuth flow"""
        return self.generate_authorization_code(app_id)


# Global mock instances
mock_api = MockTikTokAPI()
mock_oauth_server = MockOAuthServer()


def get_mock_api() -> MockTikTokAPI:
    """Get the global mock API instance"""
    return mock_api


def get_mock_oauth_server() -> MockOAuthServer:
    """Get the global mock OAuth server instance"""
    return mock_oauth_server