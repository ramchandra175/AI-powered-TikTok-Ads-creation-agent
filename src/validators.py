"""
Business rule validators for TikTok Ads campaigns

These validators enforce rules BEFORE API submission to prevent errors.
"""

from typing import Optional, Dict, List
from config import BusinessRules


class ValidationError:
    """Represents a validation error"""
    
    def __init__(self, field: str, message: str, suggestion: str = ""):
        self.field = field
        self.message = message
        self.suggestion = suggestion
    
    def __str__(self):
        return f"{self.field}: {self.message}" + (f" ({self.suggestion})" if self.suggestion else "")
    
    def to_dict(self):
        return {
            "field": self.field,
            "message": self.message,
            "suggestion": self.suggestion
        }


class CampaignValidator:
    """Validates campaign data against business rules"""
    
    @staticmethod
    def validate_campaign_name(name: Optional[str]) -> Optional[ValidationError]:
        """Validate campaign name"""
        if not name:
            return ValidationError(
                "campaign_name",
                "Campaign name is required",
                "Please provide a name for your campaign"
            )
        
        if len(name.strip()) < BusinessRules.CAMPAIGN_NAME_MIN_LENGTH:
            return ValidationError(
                "campaign_name",
                f"Campaign name must be at least {BusinessRules.CAMPAIGN_NAME_MIN_LENGTH} characters",
                f"Current length: {len(name.strip())} characters"
            )
        
        return None
    
    @staticmethod
    def validate_objective(objective: Optional[str]) -> Optional[ValidationError]:
        """Validate campaign objective"""
        if not objective:
            return ValidationError(
                "objective",
                "Campaign objective is required",
                f"Choose either: {', '.join(BusinessRules.VALID_OBJECTIVES)}"
            )
        
        if objective not in BusinessRules.VALID_OBJECTIVES:
            return ValidationError(
                "objective",
                f"Invalid objective: {objective}",
                f"Must be one of: {', '.join(BusinessRules.VALID_OBJECTIVES)}"
            )
        
        return None
    
    @staticmethod
    def validate_ad_text(text: Optional[str]) -> Optional[ValidationError]:
        """Validate ad text"""
        if not text:
            return ValidationError(
                "ad_text",
                "Ad text is required",
                "Please provide text for your ad"
            )
        
        if len(text) > BusinessRules.AD_TEXT_MAX_LENGTH:
            return ValidationError(
                "ad_text",
                f"Ad text exceeds maximum length of {BusinessRules.AD_TEXT_MAX_LENGTH} characters",
                f"Current length: {len(text)} characters. Please shorten by {len(text) - BusinessRules.AD_TEXT_MAX_LENGTH} characters."
            )
        
        return None
    
    @staticmethod
    def validate_cta(cta: Optional[str]) -> Optional[ValidationError]:
        """Validate call to action"""
        if not cta:
            return ValidationError(
                "cta",
                "CTA (Call to Action) is required",
                f"Choose one of: {', '.join(BusinessRules.VALID_CTAS)}"
            )
        
        if cta not in BusinessRules.VALID_CTAS:
            return ValidationError(
                "cta",
                f"Invalid CTA: {cta}",
                f"Must be one of: {', '.join(BusinessRules.VALID_CTAS)}"
            )
        
        return None
    
    @staticmethod
    def validate_music_logic(
        objective: Optional[str], 
        music_id: Optional[str]
    ) -> Optional[ValidationError]:
        """
        Validate music logic - THE CRITICAL RULE
        
        Rules:
        - If objective is "Conversions", music_id is REQUIRED
        - If objective is "Traffic", music_id is OPTIONAL
        """
        if not objective:
            # Can't validate music logic without objective
            return None
        
        # Case: Conversions requires music
        if BusinessRules.requires_music(objective) and not music_id:
            return ValidationError(
                "music_id",
                f"{objective} campaigns require music",
                "Please provide a Music ID or upload custom music. Alternatively, change objective to Traffic."
            )
        
        # Case: Traffic allows no music (no error)
        return None
    
    @staticmethod
    def validate_all(campaign_data: Dict) -> List[ValidationError]:
        """
        Validate all fields in campaign data
        
        Returns list of ValidationErrors (empty if all valid)
        """
        errors = []
        
        # Validate each field
        error = CampaignValidator.validate_campaign_name(campaign_data.get("campaign_name"))
        if error:
            errors.append(error)
        
        error = CampaignValidator.validate_objective(campaign_data.get("objective"))
        if error:
            errors.append(error)
        
        error = CampaignValidator.validate_ad_text(campaign_data.get("ad_text"))
        if error:
            errors.append(error)
        
        error = CampaignValidator.validate_cta(campaign_data.get("cta"))
        if error:
            errors.append(error)
        
        # Validate music logic (critical rule)
        error = CampaignValidator.validate_music_logic(
            campaign_data.get("objective"),
            campaign_data.get("music_id")
        )
        if error:
            errors.append(error)
        
        return errors
    
    @staticmethod
    def is_complete(campaign_data: Dict) -> bool:
        """Check if all required data is collected"""
        required_fields = ["campaign_name", "objective", "ad_text", "cta"]
        
        for field in required_fields:
            if not campaign_data.get(field):
                return False
        
        # Check music requirement based on objective
        objective = campaign_data.get("objective")
        music_id = campaign_data.get("music_id")
        
        if BusinessRules.requires_music(objective) and not music_id:
            return False
        
        return True


class MusicValidator:
    """Validates music-related logic"""
    
    @staticmethod
    def interpret_validation_error(error_response: Dict) -> str:
        """
        Interpret TikTok music validation API error
        
        Returns human-readable explanation
        """
        error_code = error_response.get("code", "")
        error_message = error_response.get("message", "")
        
        # Common error codes from TikTok Ads API
        interpretations = {
            "40300": "This Music ID doesn't exist in TikTok's music library.",
            "40301": "This music is not available in your target region due to licensing restrictions.",
            "40302": "This music has copyright restrictions and cannot be used.",
            "40303": "This music has been removed or is no longer available.",
            "MUSIC_NOT_FOUND": "This Music ID doesn't exist in TikTok's music library.",
            "MUSIC_GEO_RESTRICTED": "This music is not available in your region.",
            "MUSIC_COPYRIGHT": "This music has copyright restrictions."
        }
        
        explanation = interpretations.get(error_code, error_message or "Unknown music validation error")
        
        # Add suggestions
        suggestion = (
            "\\n\\nWhat would you like to do?\\n"
            "1. Try a different Music ID\\n"
            "2. Upload your own custom music\\n"
            "3. Continue without music (only available for Traffic campaigns)"
        )
        
        return explanation + suggestion
    
    @staticmethod
    def can_skip_music(objective: str) -> bool:
        """Check if campaign can skip music"""
        return BusinessRules.allows_no_music(objective)


def format_validation_errors(errors: List[ValidationError]) -> str:
    """Format validation errors for display"""
    if not errors:
        return ""
    
    lines = ["Validation Errors:"]
    for error in errors:
        lines.append(f"  • {error}")
    
    return "\\n".join(lines)