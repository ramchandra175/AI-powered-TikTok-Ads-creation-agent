"""
TikTok Ads API Client

Handles all API interactions:
- Music validation
- Music upload
- Ad submission
- Error handling and interpretation
"""

from typing import Dict, Optional
import requests

from config import Config
from oauth_manager import TikTokOAuthManager
from mock_api import get_mock_api


class APIError(Exception):
    """Custom exception for API errors"""
    
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        context: str = ""
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.context = context
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            "status_code": self.status_code,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context
        }


class TikTokAPIClient:
    """Client for TikTok Ads API"""
    
    def __init__(self, oauth_manager: TikTokOAuthManager, use_mock: bool = False):
        self.oauth_manager = oauth_manager
        self.use_mock = use_mock
        self.base_url = Config.TIKTOK_API_BASE_URL
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with access token"""
        access_token = self.oauth_manager.get_access_token()
        return {
            "Access-Token": access_token,
            "Content-Type": "application/json"
        }
    
    def validate_music(self, music_id: str) -> Dict:
        """
        Validate a music ID
        
        Returns:
            {
                "valid": bool,
                "error": Optional[str],
                "data": Optional[Dict]
            }
        """
        if self.use_mock:
            return self._mock_validate_music(music_id)
        
        try:
            url = f"{self.base_url}/music/info/"
            params = {"music_id": music_id}
            headers = self._get_headers()
            
            response = requests.get(url, params=params, headers=headers)
            data = response.json()
            
            if data.get("code") == 0:
                return {
                    "valid": True,
                    "error": None,
                    "data": data.get("data")
                }
            else:
                return {
                    "valid": False,
                    "error": self._interpret_music_error(data),
                    "data": None
                }
        
        except requests.RequestException as e:
            return {
                "valid": False,
                "error": f"Network error: {str(e)}",
                "data": None
            }
    
    def _mock_validate_music(self, music_id: str) -> Dict:
        """Mock music validation"""
        mock_api = get_mock_api()
        access_token = self.oauth_manager.get_access_token()
        
        response = mock_api.validate_music(music_id, access_token)
        
        if response["code"] == 0:
            return {
                "valid": True,
                "error": None,
                "data": response.get("data")
            }
        else:
            return {
                "valid": False,
                "error": self._interpret_music_error(response),
                "data": None
            }
    
    def upload_music(self, file_path: str) -> Dict:
        """
        Upload custom music file
        
        Returns:
            {
                "success": bool,
                "music_id": Optional[str],
                "error": Optional[str]
            }
        """
        if self.use_mock:
            return self._mock_upload_music(file_path)
        
        try:
            url = f"{self.base_url}/file/music/upload/"
            headers = self._get_headers()
            
            # In production, this would upload the actual file
            # For now, simulate with file metadata
            files = {"music_file": ("music.mp3", open(file_path, "rb"), "audio/mpeg")}
            
            response = requests.post(url, headers=headers, files=files)
            data = response.json()
            
            if data.get("code") == 0:
                return {
                    "success": True,
                    "music_id": data.get("data", {}).get("music_id"),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "music_id": None,
                    "error": data.get("message", "Upload failed")
                }
        
        except Exception as e:
            return {
                "success": False,
                "music_id": None,
                "error": str(e)
            }
    
    def _mock_upload_music(self, file_path: str) -> Dict:
        """Mock music upload"""
        mock_api = get_mock_api()
        access_token = self.oauth_manager.get_access_token()
        
        response = mock_api.upload_music(file_path, access_token)
        
        if response["code"] == 0:
            return {
                "success": True,
                "music_id": response.get("data", {}).get("music_id"),
                "error": None
            }
        else:
            return {
                "success": False,
                "music_id": None,
                "error": response.get("message", "Upload failed")
            }
    
    def create_ad(self, campaign_data: Dict) -> Dict:
        """
        Submit ad campaign
        
        Args:
            campaign_data: Validated campaign data
        
        Returns:
            {
                "success": bool,
                "ad_id": Optional[str],
                "error": Optional[str],
                "error_details": Optional[Dict]
            }
        """
        if self.use_mock:
            return self._mock_create_ad(campaign_data)
        
        try:
            url = f"{self.base_url}/ad/create/"
            headers = self._get_headers()
            
            # Build TikTok API payload
            payload = self._build_ad_payload(campaign_data)
            
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            
            if data.get("code") == 0:
                return {
                    "success": True,
                    "ad_id": data.get("data", {}).get("ad_id"),
                    "error": None,
                    "error_details": None
                }
            else:
                return {
                    "success": False,
                    "ad_id": None,
                    "error": self._interpret_submission_error(data),
                    "error_details": data
                }
        
        except requests.RequestException as e:
            return {
                "success": False,
                "ad_id": None,
                "error": f"Network error: {str(e)}",
                "error_details": None
            }
    
    def _mock_create_ad(self, campaign_data: Dict) -> Dict:
        """Mock ad creation"""
        mock_api = get_mock_api()
        access_token = self.oauth_manager.get_access_token()
        
        payload = self._build_ad_payload(campaign_data)
        response = mock_api.create_ad(payload, access_token)
        
        if response["code"] == 0:
            return {
                "success": True,
                "ad_id": response.get("data", {}).get("ad_id"),
                "error": None,
                "error_details": None
            }
        else:
            return {
                "success": False,
                "ad_id": None,
                "error": self._interpret_submission_error(response),
                "error_details": response
            }
    
    def _build_ad_payload(self, campaign_data: Dict) -> Dict:
        """Build TikTok API payload from campaign data"""
        # This is a simplified payload structure
        # Real TikTok API requires more fields
        payload = {
            "advertiser_id": self.oauth_manager.credentials.get("advertiser_ids", [None])[0],
            "campaign_name": campaign_data["campaign_name"],
            "objective": campaign_data["objective"],
            "creative": {
                "ad_text": campaign_data["ad_text"],
                "call_to_action": campaign_data["cta"]
            }
        }
        
        if campaign_data.get("music_id"):
            payload["creative"]["music_id"] = campaign_data["music_id"]
        
        return payload
    
    def _interpret_music_error(self, error_response: Dict) -> str:
        """Interpret music validation error"""
        code = error_response.get("code", "")
        message = error_response.get("message", "")
        
        interpretations = {
            "40300": "This Music ID doesn't exist in TikTok's music library.",
            "40301": "This music is not available in your target region due to licensing restrictions.",
            "40302": "This music has copyright restrictions and cannot be used.",
            "40303": "This music has been removed or is no longer available.",
            "MUSIC_NOT_FOUND": "This Music ID doesn't exist in TikTok's music library.",
            "MUSIC_GEO_RESTRICTED": "This music is not available in your region.",
            "MUSIC_COPYRIGHT": "This music has copyright restrictions."
        }
        
        base_error = interpretations.get(str(code), message or "Unknown music validation error")
        
        suggestion = (
            "\n\nWhat would you like to do?\n"
            "1. Try a different Music ID\n"
            "2. Upload your own custom music\n"
            "3. Continue without music (only for Traffic campaigns)"
        )
        
        return base_error + suggestion
    
    def _interpret_submission_error(self, error_response: Dict) -> str:
        """Interpret ad submission error"""
        code = error_response.get("code", "")
        message = error_response.get("message", "")
        
        # Token errors
        if code == 40100:
            return "Your access token is invalid or expired. Let me help you re-authenticate."
        
        # Permission errors
        elif code == 40104:
            if "permission" in message.lower():
                return "Your app doesn't have permission for ad creation. Please add required scopes in TikTok Developer dashboard."
            elif "region" in message.lower() or "geo" in message.lower():
                return "Ad creation is not available in your region. You may need to use a VPN or regional account."
        
        # Music errors
        elif code == 40300:
            return f"Invalid music: {message}"
        
        # Rate limiting
        elif code == 429:
            return "TikTok is rate limiting requests. Let's wait a moment and try again."
        
        # Server errors
        elif int(code) >= 500:
            return "TikTok's API is experiencing issues. Would you like to retry or save as draft?"
        
        else:
            return f"Submission failed: {message}"