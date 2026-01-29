"""
Tests for business rule validators
"""

import pytest
from src.validators import CampaignValidator, MusicValidator, ValidationError
from src.config import BusinessRules


class TestCampaignNameValidation:
    """Test campaign name validation"""
    
    def test_valid_campaign_name(self):
        error = CampaignValidator.validate_campaign_name("My Campaign")
        assert error is None
    
    def test_missing_campaign_name(self):
        error = CampaignValidator.validate_campaign_name(None)
        assert error is not None
        assert error.field == "campaign_name"
        assert "required" in error.message.lower()
    
    def test_short_campaign_name(self):
        error = CampaignValidator.validate_campaign_name("Ab")
        assert error is not None
        assert error.field == "campaign_name"
        assert "3 characters" in error.message


class TestObjectiveValidation:
    """Test objective validation"""
    
    def test_valid_traffic_objective(self):
        error = CampaignValidator.validate_objective("Traffic")
        assert error is None
    
    def test_valid_conversions_objective(self):
        error = CampaignValidator.validate_objective("Conversions")
        assert error is None
    
    def test_invalid_objective(self):
        error = CampaignValidator.validate_objective("InvalidObjective")
        assert error is not None
        assert error.field == "objective"
    
    def test_missing_objective(self):
        error = CampaignValidator.validate_objective(None)
        assert error is not None


class TestAdTextValidation:
    """Test ad text validation"""
    
    def test_valid_ad_text(self):
        error = CampaignValidator.validate_ad_text("Buy now and save 50%!")
        assert error is None
    
    def test_missing_ad_text(self):
        error = CampaignValidator.validate_ad_text(None)
        assert error is not None
        assert "required" in error.message.lower()
    
    def test_ad_text_too_long(self):
        long_text = "a" * 101
        error = CampaignValidator.validate_ad_text(long_text)
        assert error is not None
        assert "100 characters" in error.message


class TestCTAValidation:
    """Test CTA validation"""
    
    def test_valid_cta(self):
        for cta in BusinessRules.VALID_CTAS:
            error = CampaignValidator.validate_cta(cta)
            assert error is None, f"Valid CTA {cta} should not error"
    
    def test_invalid_cta(self):
        error = CampaignValidator.validate_cta("INVALID_CTA")
        assert error is not None
        assert error.field == "cta"
    
    def test_missing_cta(self):
        error = CampaignValidator.validate_cta(None)
        assert error is not None


class TestMusicLogic:
    """Test critical music logic rules"""
    
    def test_conversions_requires_music(self):
        """CRITICAL: Conversions objective MUST have music"""
        error = CampaignValidator.validate_music_logic("Conversions", None)
        assert error is not None
        assert "require" in error.message.lower()
        assert "music" in error.message.lower()
    
    def test_conversions_with_music_valid(self):
        """Conversions with music should be valid"""
        error = CampaignValidator.validate_music_logic("Conversions", "music_123")
        assert error is None
    
    def test_traffic_allows_no_music(self):
        """Traffic objective can have no music"""
        error = CampaignValidator.validate_music_logic("Traffic", None)
        assert error is None
    
    def test_traffic_with_music_valid(self):
        """Traffic with music should also be valid"""
        error = CampaignValidator.validate_music_logic("Traffic", "music_123")
        assert error is None


class TestCompleteValidation:
    """Test complete campaign validation"""
    
    def test_valid_campaign_traffic_no_music(self):
        campaign = {
            "campaign_name": "Summer Sale",
            "objective": "Traffic",
            "ad_text": "Check out our summer deals!",
            "cta": "SHOP_NOW",
            "music_id": None
        }
        
        errors = CampaignValidator.validate_all(campaign)
        assert len(errors) == 0
    
    def test_valid_campaign_conversions_with_music(self):
        campaign = {
            "campaign_name": "Summer Sale",
            "objective": "Conversions",
            "ad_text": "Check out our summer deals!",
            "cta": "SHOP_NOW",
            "music_id": "music_123"
        }
        
        errors = CampaignValidator.validate_all(campaign)
        assert len(errors) == 0
    
    def test_invalid_campaign_conversions_no_music(self):
        """CRITICAL TEST: This should fail"""
        campaign = {
            "campaign_name": "Summer Sale",
            "objective": "Conversions",
            "ad_text": "Check out our summer deals!",
            "cta": "SHOP_NOW",
            "music_id": None
        }
        
        errors = CampaignValidator.validate_all(campaign)
        assert len(errors) > 0
        
        # Should have music error
        music_errors = [e for e in errors if e.field == "music_id"]
        assert len(music_errors) > 0
    
    def test_multiple_validation_errors(self):
        campaign = {
            "campaign_name": "Ab",  # Too short
            "objective": "InvalidObjective",  # Invalid
            "ad_text": "a" * 101,  # Too long
            "cta": "INVALID_CTA",  # Invalid
            "music_id": None
        }
        
        errors = CampaignValidator.validate_all(campaign)
        assert len(errors) >= 4  # Should have multiple errors


class TestMusicValidator:
    """Test music validator"""
    
    def test_can_skip_music_traffic(self):
        assert MusicValidator.can_skip_music("Traffic") is True
    
    def test_cannot_skip_music_conversions(self):
        assert MusicValidator.can_skip_music("Conversions") is False
    
    def test_interpret_music_not_found(self):
        error_response = {
            "code": "40300",
            "message": "Music not found"
        }
        
        interpretation = MusicValidator.interpret_validation_error(error_response)
        assert "doesn't exist" in interpretation.lower()
        assert "library" in interpretation.lower()
    
    def test_interpret_geo_restriction(self):
        error_response = {
            "code": "40301",
            "message": "Geo restricted"
        }
        
        interpretation = MusicValidator.interpret_validation_error(error_response)
        assert "region" in interpretation.lower()


class TestIsComplete:
    """Test campaign completion check"""
    
    def test_incomplete_missing_fields(self):
        campaign = {
            "campaign_name": "Test",
            "objective": None,  # Missing
            "ad_text": "Text",
            "cta": "SHOP_NOW",
            "music_id": None
        }
        
        assert CampaignValidator.is_complete(campaign) is False
    
    def test_incomplete_conversions_no_music(self):
        campaign = {
            "campaign_name": "Test",
            "objective": "Conversions",
            "ad_text": "Text",
            "cta": "SHOP_NOW",
            "music_id": None  # Required for Conversions
        }
        
        assert CampaignValidator.is_complete(campaign) is False
    
    def test_complete_traffic_no_music(self):
        campaign = {
            "campaign_name": "Test",
            "objective": "Traffic",
            "ad_text": "Text",
            "cta": "SHOP_NOW",
            "music_id": None  # Optional for Traffic
        }
        
        assert CampaignValidator.is_complete(campaign) is True
    
    def test_complete_conversions_with_music(self):
        campaign = {
            "campaign_name": "Test",
            "objective": "Conversions",
            "ad_text": "Text",
            "cta": "SHOP_NOW",
            "music_id": "music_123"
        }
        
        assert CampaignValidator.is_complete(campaign) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])