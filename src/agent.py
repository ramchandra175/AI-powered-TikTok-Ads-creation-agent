"""
TikTok Ads AI Agent

Core agent that:
1. Conducts conversational ad creation
2. Enforces business rules
3. Validates with APIs
4. Handles errors intelligently
"""

import json
from typing import Dict, Optional, List
from datetime import datetime

from config import Config, BusinessRules
from prompts import (
    get_system_prompt,
    get_music_validation_prompt,
    get_error_interpretation_prompt,
    get_submission_prompt
)
from validators import CampaignValidator, MusicValidator, format_validation_errors
from api_client import TikTokAPIClient
from oauth_manager import TikTokOAuthManager


class AgentResponse:
    """Structured agent response"""
    
    def __init__(self, raw_response: str):
        self.raw = raw_response
        self.parsed: Optional[Dict] = None
        self.error: Optional[str] = None
        
        try:
            # Extract JSON from response (might be wrapped in markdown)
            json_str = self._extract_json(raw_response)
            self.parsed = json.loads(json_str)
        except Exception as e:
            self.error = f"Failed to parse agent response: {str(e)}"
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from potentially markdown-wrapped text"""
        # Remove markdown code blocks if present
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()
        else:
            # Try to find JSON object
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                return text[start:end]
        return text
    
    def is_valid(self) -> bool:
        return self.parsed is not None and self.error is None
    
    def get_conversation_response(self) -> str:
        if not self.is_valid():
            return "I apologize, but I'm having trouble processing that. Could you please rephrase?"
        return self.parsed.get("conversation_response", "")
    
    def get_collected_data(self) -> Dict:
        if not self.is_valid():
            return {}
        return self.parsed.get("collected_data", {})
    
    def get_validation_status(self) -> str:
        if not self.is_valid():
            return "error"
        return self.parsed.get("validation_status", "incomplete")
    
    def get_next_action(self) -> str:
        if not self.is_valid():
            return "continue"
        return self.parsed.get("next_action", "continue")


class TikTokAdsAgent:
    """AI Agent for TikTok Ad campaign creation"""
    
    def __init__(
        self,
        oauth_manager: TikTokOAuthManager,
        api_client: TikTokAPIClient,
        use_mock: bool = False
    ):
        self.oauth_manager = oauth_manager
        self.api_client = api_client
        self.use_mock = use_mock
        
        # LLM client
        self.llm_provider = Config.get_llm_provider()
        self._init_llm_client()
        
        # Conversation state
        self.conversation_history: List[Dict] = []
        self.campaign_data: Dict = {
            "campaign_name": None,
            "objective": None,
            "ad_text": None,
            "cta": None,
            "music_id": None,
            "music_status": "not_requested"
        }
        
        # System prompt
        self.system_prompt = get_system_prompt()
    
    def _init_llm_client(self):
        """Initialize LLM client based on provider"""
        if self.llm_provider == "openai":
            from openai import OpenAI
            self.llm_client = OpenAI(api_key=Config.OPENAI_API_KEY)
            self.model = Config.OPENAI_MODEL
        elif self.llm_provider == "anthropic":
            from anthropic import Anthropic
            self.llm_client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            self.model = Config.ANTHROPIC_MODEL
    
    def start_conversation(self) -> str:
        """Start the ad creation conversation"""
        initial_message = "I want to create a TikTok ad campaign"
        return self.process_user_input(initial_message)
    
    def process_user_input(self, user_input: str) -> str:
        """
        Process user input and return agent response
        
        This is the main conversation loop
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Get LLM response
        llm_response = self._call_llm(user_input)
        
        # Parse structured response
        agent_response = AgentResponse(llm_response)
        
        if Config.DEBUG:
            print(f"\n[DEBUG] Agent response: {agent_response.parsed}\n")
        
        # Update campaign data
        collected = agent_response.get_collected_data()
        if collected:
            self.campaign_data.update(collected)
        
        # Handle next action
        next_action = agent_response.get_next_action()
        
        if next_action == "validate_music":
            return self._handle_music_validation(agent_response)
        elif next_action == "submit":
            return self._handle_submission(agent_response)
        elif next_action == "enforce_rule":
            return self._handle_rule_enforcement(agent_response)
        else:
            # Continue conversation
            response_text = agent_response.get_conversation_response()
            self.conversation_history.append({
                "role": "assistant",
                "content": response_text
            })
            return response_text
    
    def _call_llm(self, user_message: str, additional_context: str = "") -> str:
        """Call LLM with conversation history"""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history (keep last 10 turns)
        messages.extend(self.conversation_history[-10:])
        
        # Add additional context if provided
        if additional_context:
            messages.append({
                "role": "user",
                "content": additional_context
            })
        
        # Call appropriate LLM
        if self.llm_provider == "openai":
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        
        elif self.llm_provider == "anthropic":
            # Extract system prompt
            system = messages[0]["content"]
            conversation = messages[1:]
            
            response = self.llm_client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system,
                messages=conversation
            )
            return response.content[0].text
    
    def _handle_music_validation(self, agent_response: AgentResponse) -> str:
        """Handle music validation request"""
        music_id = self.campaign_data.get("music_id")
        
        if not music_id:
            return "Please provide a Music ID to validate."
        
        # Call API to validate
        result = self.api_client.validate_music(music_id)
        
        # Update music status
        if result["valid"]:
            self.campaign_data["music_status"] = "validated"
            response = f"Great! Music ID '{music_id}' is valid and ready to use. "
            
            # Check if we have everything
            if self._is_campaign_complete():
                response += "I have all the information needed. Ready to submit?"
            
        else:
            self.campaign_data["music_status"] = "error"
            self.campaign_data["music_id"] = None
            
            # Get LLM to interpret error
            error_context = get_music_validation_prompt(result)
            interpretation = self._call_llm("", error_context)
            
            parsed = AgentResponse(interpretation)
            response = parsed.get_conversation_response()
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _handle_submission(self, agent_response: AgentResponse) -> str:
        """Handle ad submission"""
        # Final validation
        errors = CampaignValidator.validate_all(self.campaign_data)
        
        if errors:
            error_msg = "Cannot submit - please fix these issues:\n"
            error_msg += format_validation_errors(errors)
            
            self.conversation_history.append({
                "role": "assistant",
                "content": error_msg
            })
            return error_msg
        
        # Submit to API
        result = self.api_client.create_ad(self.campaign_data)
        
        if result["success"]:
            response = (
                f"🎉 Success! Your ad campaign has been created.\n\n"
                f"Ad ID: {result['ad_id']}\n"
                f"Campaign: {self.campaign_data['campaign_name']}\n"
                f"Objective: {self.campaign_data['objective']}\n"
                f"Status: Pending Review\n\n"
                f"Your ad will be reviewed by TikTok and should go live within 24 hours."
            )
        else:
            # Interpret error
            error_prompt = get_error_interpretation_prompt(
                error_type="SUBMISSION_ERROR",
                status_code=result.get("error_details", {}).get("code", 500),
                error_message=result["error"],
                context="Ad submission failed"
            )
            
            interpretation = self._call_llm("", error_prompt)
            parsed = AgentResponse(interpretation)
            response = parsed.get_conversation_response()
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _handle_rule_enforcement(self, agent_response: AgentResponse) -> str:
        """Handle business rule enforcement"""
        # This is triggered when LLM detects a rule violation
        response = agent_response.get_conversation_response()
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _is_campaign_complete(self) -> bool:
        """Check if all required data is collected"""
        return CampaignValidator.is_complete(self.campaign_data)
    
    def get_campaign_summary(self) -> str:
        """Get a summary of collected campaign data"""
        summary = "Current Campaign Data:\n"
        summary += "=" * 40 + "\n"
        
        for key, value in self.campaign_data.items():
            if value is not None and key != "music_status":
                summary += f"{key}: {value}\n"
        
        summary += "=" * 40
        return summary
    
    def reset(self):
        """Reset agent state for new campaign"""
        self.conversation_history = []
        self.campaign_data = {
            "campaign_name": None,
            "objective": None,
            "ad_text": None,
            "cta": None,
            "music_id": None,
            "music_status": "not_requested"
        }