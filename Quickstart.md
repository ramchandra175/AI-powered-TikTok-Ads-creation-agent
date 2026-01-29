# Quick Start Guide

Get the TikTok Ads AI Agent running in 5 minutes.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- (Optional) TikTok Developer account for real API usage

## Step 1: Clone and Install (2 minutes)

```bash
# Clone the repository
git clone <your-repo-url>
cd tiktok-ads-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment (1 minute)

### Option A: Mock Mode (No TikTok Account Needed)

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your LLM API key
# Either:
OPENAI_API_KEY=sk-your-key-here
# Or:
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Enable mock mode
USE_MOCK_API=true
```

### Option B: Real TikTok API

```bash
# Copy example env file  
cp .env.example .env

# Edit .env and add:
OPENAI_API_KEY=sk-your-key-here  # or ANTHROPIC_API_KEY
TIKTOK_APP_ID=your_app_id
TIKTOK_APP_SECRET=your_app_secret
USE_MOCK_API=false
```

**To get TikTok credentials:**
1. Go to https://ads.tiktok.com/marketing_api/homepage
2. Create a developer account
3. Create a new app
4. Add OAuth redirect: `http://localhost:8080/callback`
5. Request scopes: `ad_management`, `ad_creation`
6. Copy App ID and Secret to `.env`

## Step 3: Run the Agent (1 minute)

```bash
python src/main.py
```

You should see:

```
============================================================
TikTok Ads AI Agent
Conversational Ad Campaign Creation
============================================================

LLM Provider: openai
Model: gpt-4-turbo-preview
Mock API Mode: true
Debug Mode: false
...

Agent Ready!
============================================================

I'll help you create a TikTok ad campaign.
Just chat with me naturally, and I'll guide you through the process.

Agent: I'll help you create a TikTok ad campaign! Let's start with the basics...
```

## Step 4: Create Your First Campaign (2 minutes)

Follow the conversational flow:

```
You: I want to create a new campaign

Agent: Great! What would you like to name your campaign?

You: Summer Sale 2024

Agent: Perfect! Now, what's your objective? Traffic or Conversions?

You: Conversions

Agent: Since you chose Conversions, you'll need to include music. 
       Do you have a Music ID, or would you like to upload custom music?

You: Use music_123

Agent: Let me validate that... Great! Music ID 'music_123' is valid.
       What text would you like for your ad? (Max 100 characters)

You: Get 50% off all summer items! Limited time only.

Agent: Excellent! What call-to-action would you like? 
       Options: LEARN_MORE, SHOP_NOW, SIGN_UP, DOWNLOAD, etc.

You: SHOP_NOW

Agent: Perfect! I have all the information. Ready to submit your campaign?

You: Yes

Agent: 🎉 Success! Your ad campaign has been created.
       Ad ID: ad_123456
       Campaign: Summer Sale 2024
       ...
```

## Quick Commands

While using the agent:

```bash
summary  # View current campaign data
reset    # Start a new campaign
quit     # Exit the agent
```

## Testing the Music Logic

### Test Case 1: Valid Music

```
You: Create a Conversions campaign with music_123
[Should succeed]
```

### Test Case 2: Invalid Music  

```
You: Create a Conversions campaign with music_not_found
[Should explain error and offer alternatives]
```

### Test Case 3: No Music (Traffic - Allowed)

```
You: Create a Traffic campaign with no music
[Should succeed]
```

### Test Case 4: No Music (Conversions - Blocked)

```
You: Create a Conversions campaign with no music  
[Should block and explain requirement]
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_validators.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Debug Mode

To see detailed LLM interactions:

```bash
DEBUG=true python src/main.py
```

This shows:
- Full LLM prompts
- Structured JSON responses  
- API calls and responses

## Troubleshooting

### "No LLM API key configured"

Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` to `.env`

### "TIKTOK_APP_ID not set"

Either:
- Set `USE_MOCK_API=true` in `.env` for testing
- Add TikTok credentials to `.env`

### "Module not found"

```bash
# Make sure you're in virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### "JSON parsing error"

Enable debug mode to see raw LLM responses:
```bash
DEBUG=true python src/main.py
```

Usually means LLM isn't following the JSON schema. Try:
- Different model (Claude is more reliable with JSON)
- Add `"response_format": {"type": "json_object"}` for OpenAI

## Next Steps

1. Read the [Design Documentation](docs/DESIGN.md) to understand architecture
2. Watch the [Video Demo](docs/VIDEO_SCRIPT.md) (script included)
3. Review [Main README](README.md) for comprehensive documentation
4. Explore the code starting from `src/main.py`

## Common Workflows

### Workflow 1: Create Basic Campaign

```bash
python src/main.py
> Create a Traffic campaign called "Brand Awareness"
> Text: "Discover our new collection"  
> CTA: LEARN_MORE
> No music
> Submit
```

### Workflow 2: Handle Music Error

```bash
python src/main.py
> Create Conversions campaign "Holiday Sale"
> Use music_not_found
[See error interpretation and suggestions]
> Try music_123 instead
[Continue to completion]
```

### Workflow 3: Test OAuth

```bash
# With real credentials in .env
USE_MOCK_API=false python src/main.py
[Follow OAuth flow]
[Create campaign with real API]
```

## Production Deployment

For production use:

1. **Environment Variables**: Use secure secret management
2. **Logging**: Add comprehensive logging
3. **Monitoring**: Track success rates and errors  
4. **Rate Limiting**: Implement backoff for API calls
5. **State Persistence**: Save drafts to database
6. **User Sessions**: Support multiple concurrent users

See `docs/DESIGN.md` section "What Would I Improve?" for details.

---

**Need Help?**

- Check [README.md](README.md) for full documentation
- See [DESIGN.md](docs/DESIGN.md) for architecture details
- Review tests in `tests/` for usage examples