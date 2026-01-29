# TikTok Ads AI Agent

An AI-powered conversational agent that helps users create TikTok Ad campaigns through natural language interaction with built-in OAuth integration, business rule enforcement, and intelligent error handling.

## 🎯 Overview

This agent demonstrates production-ready AI workflow design with:
- **Structured prompt engineering** for reliable LLM outputs
- **OAuth 2.0 integration** with TikTok Ads API
- **Business rule enforcement** before API submission
- **Intelligent error interpretation** and recovery suggestions
- **Clear separation of concerns** between conversation, reasoning, and API layers

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  User Interface                      │
│              (CLI Conversation)                      │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              AI Agent Core                           │
│  ┌──────────────────────────────────────────────┐  │
│  │  Conversation Manager                         │  │
│  │  - Collects user inputs step-by-step         │  │
│  │  - Validates responses                        │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Business Rules Engine                        │  │
│  │  - Music logic enforcement                    │  │
│  │  - Field validation                           │  │
│  │  - Pre-submission checks                      │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  Structured Output Generator                  │  │
│  │  - JSON schema enforcement                    │  │
│  │  - Payload construction                       │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              API Layer                               │
│  ┌──────────────────────────────────────────────┐  │
│  │  OAuth Manager                                │  │
│  │  - Authorization code flow                    │  │
│  │  - Token refresh                              │  │
│  │  - Credential storage                         │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  TikTok API Client                            │  │
│  │  - Music validation                           │  │
│  │  - Ad submission                              │  │
│  │  - Error interpretation                       │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 📋 Requirements

- Python 3.9+
- OpenAI API key (or Anthropic Claude API key)
- TikTok Developer account and app credentials

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd tiktok-ads-agent

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# TikTok OAuth Configuration
TIKTOK_APP_ID=your_app_id
TIKTOK_APP_SECRET=your_app_secret
TIKTOK_REDIRECT_URI=http://localhost:8080/callback

# Optional: Use mock mode for testing without real API
USE_MOCK_API=true
```

### 3. TikTok Developer Setup

1. Create a TikTok Developer account at https://ads.tiktok.com/marketing_api/homepage
2. Create a new app in the developer dashboard
3. Configure OAuth redirect URI: `http://localhost:8080/callback`
4. Request the following scopes:
   - `ad_management`
   - `ad_creation`
5. Copy your App ID and Secret to `.env`

### 4. Run the Agent

```bash
# Start the OAuth server (separate terminal)
python src/oauth_server.py

# Run the agent
python src/main.py

# Or run with mock API (no real TikTok account needed)
USE_MOCK_API=true python src/main.py
```

## 🎭 How OAuth is Handled

### Authorization Flow

The agent implements the OAuth 2.0 Authorization Code flow:

1. **Authorization Request**: User is directed to TikTok's authorization URL
2. **User Consent**: User logs in and grants permissions
3. **Callback Handling**: Local server receives the authorization code
4. **Token Exchange**: Code is exchanged for access_token and refresh_token
5. **Token Storage**: Credentials are securely stored in `credentials.json`
6. **Token Refresh**: Automatic refresh when token expires

### Error Detection & Recovery

The OAuth manager detects and handles:

| Error Type | Detection | Agent Response |
|------------|-----------|----------------|
| Invalid client credentials | 401 during token exchange | Explains credential mismatch, suggests verifying App ID/Secret in developer dashboard |
| Missing scopes | 403 on API calls | Lists required scopes, provides link to update app permissions |
| Expired token | 401 on API calls | Automatically attempts refresh, re-prompts OAuth if refresh fails |
| Revoked token | 401 with specific error | Explains token was revoked, initiates new OAuth flow |
| Geo-restriction | 403 with geo error | Explains regional limitations, suggests VPN or regional account |

## 🧠 Prompt Design Explanation

### Three-Layer Prompt Architecture

The agent uses a sophisticated prompt structure with clear separation:

#### 1. System Prompt (Agent Identity)
```
You are a TikTok Ads Campaign Assistant. Your role is to:
- Guide users through ad creation step-by-step
- Enforce business rules before API submission
- Interpret API errors and suggest solutions
- Always output structured JSON with your reasoning
```

#### 2. Business Rules Layer
```
CRITICAL RULES:
- Campaign name: min 3 characters
- Ad text: max 100 characters
- Music logic:
  * If objective = "Conversions" → Music required
  * If objective = "Traffic" → Music optional
  * Invalid music ID → Explain and offer alternatives
```

#### 3. Structured Output Schema
```json
{
  "internal_reasoning": "Step-by-step thought process",
  "conversation_response": "What to say to the user",
  "collected_data": {
    "campaign_name": "...",
    "objective": "...",
    "ad_text": "...",
    "cta": "...",
    "music_id": "..." or null
  },
  "validation_status": "complete|incomplete|error",
  "next_action": "continue|validate_music|submit|retry"
}
```

### Why This Design Works

1. **Separation of Concerns**: Internal reasoning is isolated from user-facing responses
2. **Structured Outputs**: JSON schema ensures consistent, parseable responses
3. **Rule Enforcement**: Business logic is embedded in the prompt, not code
4. **Context Preservation**: Full conversation history maintains state
5. **Error Handling**: LLM interprets API errors and suggests human-readable solutions

### Example Prompt Flow

**User**: "I want to create an ad campaign"

**Agent Internal Reasoning**:
```json
{
  "internal_reasoning": "User initiated ad creation. Need to collect: campaign_name, objective, ad_text, cta, music. Start with campaign name.",
  "conversation_response": "I'll help you create a TikTok ad campaign! Let's start with the basics. What would you like to name your campaign?",
  "collected_data": {},
  "validation_status": "incomplete",
  "next_action": "continue"
}
```

## 🔧 API Assumptions & Mocks

### Mock API Design

For testing without TikTok credentials, the agent includes a comprehensive mock API:

#### Mock Endpoints

1. **Music Validation** (`/music/validate`)
   - Valid IDs: `"music_123"`, `"music_456"`, `"music_789"`
   - Invalid ID response: `{"error": "MUSIC_NOT_FOUND", "message": "Music ID does not exist"}`
   - Geo-restricted: `"music_geo_001"` → 403 error

2. **Ad Submission** (`/ads/create`)
   - Success: Returns mock ad ID
   - Failures simulated:
     - Invalid token: 401
     - Missing permissions: 403
     - Invalid music: 400
     - Rate limiting: 429

#### Real API Assumptions

Based on TikTok Ads API documentation:

- **Base URL**: `https://business-api.tiktok.com/open_api/v1.3/`
- **Authentication**: Bearer token in `Access-Token` header
- **Music Validation**: `GET /music/info/` endpoint
- **Ad Creation**: `POST /ad/create/` endpoint
- **Error Codes**:
  - `40100`: Invalid access token
  - `40101`: Token expired
  - `40104`: Insufficient permissions
  - `40300`: Invalid music ID
  - `40301`: Music unavailable in region

### Music Logic Implementation

The agent enforces three music cases:

#### Case A: Existing Music ID
```python
# User provides music ID
music_id = "music_123"

# Agent validates via API
response = api_client.validate_music(music_id)

if response.error:
    # LLM interprets error
    agent_response = interpret_music_error(response)
    # Example: "This music ID doesn't exist in TikTok's library. 
    # Would you like to: 1) Try a different ID, 2) Upload custom music, 
    # or 3) Continue without music?"
```

#### Case B: Custom Music Upload
```python
# User wants to upload music
file_path = user_provides_file()

# Simulate upload (in production, use TikTok upload API)
music_id = mock_upload_music(file_path)  # Returns "music_custom_xxx"

# Validate uploaded music
response = api_client.validate_music(music_id)
```

#### Case C: No Music
```python
# Agent checks objective before allowing no music
if objective == "Conversions" and music_id is None:
    # BLOCK: Cannot proceed
    error = "Conversions campaigns require music. Please provide a music ID or upload custom music."
    
elif objective == "Traffic" and music_id is None:
    # ALLOW: Can proceed without music
    pass
```

## 🎯 Business Rule Enforcement

### Pre-Submission Validation

All rules are enforced **before** API submission:

```python
def validate_campaign(data):
    errors = []
    
    # Rule 1: Campaign name length
    if len(data['campaign_name']) < 3:
        errors.append("Campaign name must be at least 3 characters")
    
    # Rule 2: Ad text length
    if len(data['ad_text']) > 100:
        errors.append("Ad text cannot exceed 100 characters")
    
    # Rule 3: Music requirement
    if data['objective'] == 'Conversions' and not data['music_id']:
        errors.append("Conversions campaigns require music")
    
    return errors
```

### Runtime Rule Application

The LLM actively enforces rules during conversation:

- **Campaign Name**: Prompts for longer name if < 3 chars
- **Objective Selection**: Explains implications for music requirement
- **Ad Text**: Warns when approaching 100 character limit
- **Music Logic**: Blocks incompatible objective/music combinations

## 🛠️ Running the Agent

### Normal Mode (Real API)

```bash
# Ensure .env is configured with real TikTok credentials
python src/main.py
```

### Mock Mode (Testing)

```bash
# Use mock API for testing without credentials
USE_MOCK_API=true python src/main.py
```

### Debug Mode

```bash
# See detailed prompt/response logs
DEBUG=true python src/main.py
```

## 📁 Project Structure

```
tiktok-ads-agent/
├── src/
│   ├── main.py                 # Entry point
│   ├── agent.py                # Core AI agent logic
│   ├── prompts.py              # Prompt templates
│   ├── oauth_manager.py        # OAuth flow handling
│   ├── api_client.py           # TikTok API client
│   ├── mock_api.py             # Mock API for testing
│   ├── validators.py           # Business rule validators
│   └── config.py               # Configuration management
├── tests/
│   ├── test_agent.py           # Agent logic tests
│   ├── test_validators.py      # Validation tests
│   └── test_oauth.py           # OAuth flow tests
├── docs/
│   └── DESIGN.md               # Detailed design decisions
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .gitignore
└── README.md                   # This file
```

## 🎬 Demo Video Script

A 5-minute video demonstration covers:

1. **Prompt Structure** (1 min)
   - Show system prompt design
   - Explain structured output format
   - Demonstrate reasoning layer

2. **Business Rule Enforcement** (1.5 min)
   - Walk through music logic cases
   - Show pre-submission validation
   - Demonstrate rule-based blocking

3. **API Error Interpretation** (1.5 min)
   - Trigger OAuth errors
   - Show music validation failures
   - Demonstrate geo-restriction handling

4. **Future Improvements** (1 min)
   - Multi-turn error recovery
   - Advanced music recommendation
   - Batch campaign creation

## 🔮 Future Improvements

Given more time, I would add:

1. **Enhanced Music Intelligence**
   - Music recommendation based on campaign objective
   - Trend analysis integration
   - Copyright checking

2. **Multi-Campaign Management**
   - Batch creation workflows
   - Campaign templates
   - A/B testing setup

3. **Advanced Error Recovery**
   - Automatic retry with exponential backoff
   - Fallback music suggestions
   - Draft saving on errors

4. **Richer Conversation**
   - Multi-turn clarification
   - Campaign optimization suggestions
   - Historical campaign analysis

5. **Production Hardening**
   - Comprehensive logging
   - Metrics and monitoring
   - Rate limiting handling
   - Credential encryption

## 📚 References

- [TikTok Marketing API Documentation](https://ads.tiktok.com/marketing_api/docs)
- [OAuth 2.0 Authorization Code Flow](https://oauth.net/2/grant-types/authorization-code/)
- [Structured Outputs with LLMs](https://platform.openai.com/docs/guides/structured-outputs)

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This is an assignment project, but feedback is welcome via issues.

---

**Built with ❤️ for production-ready AI workflows**