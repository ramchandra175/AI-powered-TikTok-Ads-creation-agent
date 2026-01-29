# 5-Minute Video Demo Script

## Overview (30 seconds)

**[Show README on screen]**

"Hi! I'm going to demonstrate the TikTok Ads AI Agent I built for this assignment. This is a production-ready conversational agent that helps users create TikTok ad campaigns through natural language, with intelligent error handling and business rule enforcement."

**[Show architecture diagram from README]**

"The system has four main components:
1. OAuth integration for TikTok authentication
2. Conversational AI using structured prompts
3. Business rule validators
4. API client with error interpretation

Let's dive into each area."

---

## 1. Prompt Structure (1 minute)

**[Show prompts.py file, highlight SYSTEM_PROMPT]**

"First, let's talk about prompt design. I use a three-layer architecture:

**Layer 1** is the agent identity - who it is and what it does.

**Layer 2** contains all business rules - like campaign name minimum length, ad text maximum length, and critically, the music logic.

**Layer 3** defines the structured output format - JSON with fields for reasoning, conversation, collected data, and next action.

**[Show JSON schema in prompt]**

This structure is key because it separates:
- What the agent is thinking (internal_reasoning)
- What it says to users (conversation_response)  
- What data it has collected (collected_data)
- What it should do next (next_action)

**[Show AgentResponse class in agent.py]**

The AgentResponse class safely parses this JSON, with fallback handling if the LLM produces malformed output."

---

## 2. Business Rule Enforcement (1.5 minutes)

**[Show validators.py, highlight music logic]**

"The most important rule is the music logic. Let me show you how it works:

**[Highlight the three cases in prompt]**

Case A: User provides existing Music ID
- Agent validates it via API
- If invalid, interprets the error and suggests alternatives

Case B: User uploads custom music  
- Agent simulates upload
- Validates the uploaded music
- Handles failures gracefully

Case C: No music
- Allowed ONLY if objective is Traffic
- Blocked if objective is Conversions

**[Show validate_music_logic function]**

This rule is enforced in the validator BEFORE we even try to submit to the API.

**[Run test_validators.py, show the critical test]**

```bash
pytest tests/test_validators.py::TestMusicLogic::test_conversions_requires_music -v
```

See? This test ensures that Conversions without music MUST fail validation.

**[Show how it's also in the prompt]**

The rule is also in the prompt, so the LLM knows about it during conversation and can guide users appropriately."

---

## 3. API Error Interpretation (1.5 minutes)

**[Show api_client.py, highlight _interpret_music_error]**

"Now for error handling. When an API call fails, we don't just show the raw error. Watch this:

**[Show mock_api.py, highlight ERROR_MUSIC_IDS]**

The mock API can simulate different error scenarios:
- Music not found
- Geo-restrictions  
- Copyright issues

**[Show the interpretation function]**

We map these error codes to user-friendly explanations with specific suggestions.

**[Start the agent in terminal with DEBUG=true]**

Let me demonstrate:

```bash
USE_MOCK_API=true DEBUG=true python src/main.py
```

**[Type in conversation]**

> I want to create a campaign for Conversions with Music ID music_not_found

**[Show agent's response]**

See how it:
1. Detects the music validation failed
2. Explains WHY (music doesn't exist)
3. Suggests WHAT TO DO (try different ID, upload custom, etc.)

**[Show oauth_manager.py error handling]**

OAuth errors work the same way - interpret cryptic errors into actionable advice:
- Invalid credentials → Check your .env
- Missing scopes → Update developer dashboard  
- Token expired → Automatically refreshes
- Geo-restriction → Suggests VPN

**[Show _handle_token_error method]**

Each error type has specific recovery instructions."

---

## 4. Complete Flow Demonstration (1 minute)

**[Run agent normally]**

"Let me show a complete flow:

```bash
USE_MOCK_API=true python src/main.py
```

**[Type conversation]**

> I want to create a summer sale campaign

[Agent asks for name]

> Call it Summer Blast 2024

[Agent asks objective]  

> Conversions

[Agent explains music is required, asks for music ID]

> Let's use music_123

[Agent validates music successfully]

> The ad text is: Get 50% off all summer items this weekend only!

[Agent asks for CTA]

> SHOP_NOW

[Agent summarizes and asks to submit]

> Yes, submit it

[Agent creates ad successfully]

**[Show summary command]**

> summary

See all the collected data in one place.

**[Show the validation happening]**

If I had tried Conversions WITHOUT music, watch:

> reset
> Create a conversions campaign with no music

[Agent blocks this during conversation]

That's pre-submission enforcement - we catch the error before wasting an API call."

---

## 5. Future Improvements (30 seconds)

**[Show DESIGN.md file]**

"Given more time, I would add:

1. **Retry logic** with exponential backoff for transient failures
2. **Music recommendations** based on campaign objective  
3. **State persistence** to save draft campaigns
4. **Batch creation** for multiple campaigns
5. **Richer validation** like ad text policy compliance

**[Show architecture diagram again]**

The modular architecture makes all these additions straightforward."

---

## Closing (30 seconds)

**[Show README]**

"To summarize what makes this production-ready:

✅ Strong prompt design with structured outputs
✅ Clear separation of concerns
✅ Business rules enforced before API calls
✅ Intelligent error interpretation with suggestions  
✅ Comprehensive testing
✅ Mock API for development without credentials

The code is well-documented, tested, and ready to extend.

**[Show GitHub repo]**

Everything is in the GitHub repo with clear README and setup instructions.

Thanks for watching!"

---

## Technical Notes for Recording

- Terminal font: 18pt for visibility
- Use syntax highlighting
- Keep cursor visible
- Pause 2 seconds after each major point
- Show files in split screen when discussing code
- Use a clean terminal (no extra output)

## Demo Environment Setup

```bash
# Before recording:
cd tiktok-ads-agent
source venv/bin/activate
export USE_MOCK_API=true
export DEBUG=false  # except when showing debug
clear
```

## Backup Plan

If live demo fails, have pre-recorded terminal session as backup using `asciinema`.