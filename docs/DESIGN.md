# Design Decisions & Architecture

This document explains the key design decisions made in building the TikTok Ads AI Agent.

## Table of Contents
1. [Architectural Principles](#architectural-principles)
2. [Prompt Engineering Strategy](#prompt-engineering-strategy)
3. [Business Rules Enforcement](#business-rules-enforcement)
4. [Error Handling Philosophy](#error-handling-philosophy)
5. [API Integration](#api-integration)
6. [Testing Strategy](#testing-strategy)

## Architectural Principles

### Separation of Concerns

The agent is built with clear layer separation:

```
┌─────────────────────────────────────┐
│     User Interface (CLI)            │  ← Handles I/O, formatting
├─────────────────────────────────────┤
│     Agent Core                      │  ← Conversation logic, state
├─────────────────────────────────────┤
│     Business Rules                  │  ← Validation, enforcement
├─────────────────────────────────────┤
│     API Client                      │  ← TikTok API interactions
├─────────────────────────────────────┤
│     OAuth Manager                   │  ← Authentication
└─────────────────────────────────────┘
```

**Why this matters:**
- Each layer can be tested independently
- Business rules are isolated from LLM logic
- API client can be swapped or mocked
- Clear boundaries make the code maintainable

### Structured Output Pattern

Instead of free-form LLM responses, we enforce JSON structure:

```json
{
  "internal_reasoning": "...",
  "conversation_response": "...",
  "collected_data": {...},
  "validation_status": "...",
  "next_action": "..."
}
```

**Benefits:**
- Predictable parsing (no regex or heuristics)
- Separation of internal reasoning from user-facing text
- Easy state extraction
- Debugging visibility into LLM thinking

**Implementation:**
The system prompt explicitly requires JSON output. We use `AgentResponse` class to safely parse and extract fields, with fallback handling for malformed responses.

## Prompt Engineering Strategy

### Three-Layer Prompt Design

**Layer 1: Identity & Role**
```
You are a TikTok Ads Campaign Creation Assistant...
```
Establishes the agent's purpose and responsibilities.

**Layer 2: Business Rules**
```
CRITICAL BUSINESS RULES
- Campaign Name: Minimum 3 characters
- Music Logic: If Conversions → Music required
...
```
Embeds domain knowledge directly in the prompt.

**Layer 3: Output Schema**
```
You MUST respond with valid JSON in this exact structure...
```
Enforces structured output format.

### Why This Works

1. **Rule Enforcement in Prompt**: By putting business rules in the system prompt, the LLM naturally enforces them during conversation, not just at validation time.

2. **Reasoning Transparency**: The `internal_reasoning` field lets us see how the LLM is thinking, making debugging easier.

3. **Context Preservation**: Full conversation history maintains state without complex state management.

4. **Graceful Degradation**: Even if JSON parsing fails, we have error handlers to keep conversation going.

### Prompt Composition

Different prompt templates are composed for different scenarios:

- **Base System Prompt**: Always present, defines agent behavior
- **Music Validation Prompt**: Added when validating music
- **Error Interpretation Prompt**: Added when API calls fail
- **Submission Prompt**: Added for final validation

This modular approach keeps prompts focused and maintainable.

## Business Rules Enforcement

### Pre-Submission Validation Philosophy

**Critical Design Decision**: Enforce rules BEFORE API submission, not after failure.

```python
# GOOD: Check before submitting
errors = CampaignValidator.validate_all(campaign_data)
if errors:
    return format_validation_errors(errors)
    
api_client.create_ad(campaign_data)

# BAD: Submit and handle failure
result = api_client.create_ad(campaign_data)
if result.error == "Music required":
    ...
```

**Why this matters:**
- Saves API quota (don't waste calls on invalid data)
- Better UX (immediate feedback vs waiting for API)
- Cleaner error messages (we control the wording)
- Prevents cascading failures

### Music Logic Implementation

The most complex rule is music requirement based on objective:

```python
class BusinessRules:
    MUSIC_REQUIRED_FOR = ["Conversions"]
    MUSIC_OPTIONAL_FOR = ["Traffic"]
    
    @classmethod
    def requires_music(cls, objective: str) -> bool:
        return objective in cls.MUSIC_REQUIRED_FOR
```

This is enforced in THREE places:

1. **Prompt**: LLM knows the rule and asks appropriately
2. **Validator**: Pre-submission check blocks invalid submissions
3. **Agent Logic**: Won't proceed to submission without music if required

**Redundancy is intentional**: Defense in depth prevents rule violations.

### Validation Error Design

```python
class ValidationError:
    field: str          # What field has the error
    message: str        # What's wrong
    suggestion: str     # How to fix it
```

Errors are **actionable**, not just descriptive. User always knows what to do next.

## Error Handling Philosophy

### Error Interpretation Layer

Raw API errors are cryptic:
```json
{"code": 40300, "message": "Invalid music_id"}
```

We interpret them for users:
```
"This Music ID doesn't exist in TikTok's library.

What would you like to do?
1. Try a different Music ID
2. Upload your own custom music
3. Continue without music (only for Traffic campaigns)"
```

### Error Handler Architecture

```python
try:
    result = api_client.validate_music(music_id)
except APIError as e:
    # Interpret error
    interpretation = interpret_music_error(e)
    
    # Have LLM explain in context
    prompt = get_error_interpretation_prompt(...)
    llm_response = call_llm(prompt)
    
    return llm_response
```

**Two-stage interpretation:**
1. Rule-based mapping (code → explanation)
2. LLM contextualization (explanation → conversational response)

This combines reliability of rules with naturalness of LLM.

### OAuth Error Handling

OAuth errors are particularly tricky because they're often configuration issues:

```python
class OAuthError(Exception):
    error_type: str    # Categorize the error
    message: str       # What happened
    suggestion: str    # How to fix it
```

Each error type has specific recovery instructions:
- Invalid credentials → Check .env file
- Missing scopes → Update app in developer dashboard
- Expired token → Automatic refresh attempt
- Geo-restriction → Suggest VPN or regional account

## API Integration

### Mock vs Real API

**Design Decision**: Full mock API implementation, not just stubs.

```python
class MockTikTokAPI:
    """Simulates real API behavior including errors"""
    
    VALID_MUSIC_IDS = ["music_123", ...]
    ERROR_MUSIC_IDS = {
        "music_not_found": {"code": "40300", ...},
        ...
    }
```

**Why this is valuable:**
1. Development without TikTok account
2. Consistent testing (no API rate limits)
3. Error scenario testing (trigger specific errors)
4. Demonstrations (works without credentials)

### API Client Design

```python
class TikTokAPIClient:
    def __init__(self, oauth_manager, use_mock):
        self.oauth_manager = oauth_manager
        self.use_mock = use_mock
    
    def validate_music(self, music_id):
        if self.use_mock:
            return self._mock_validate_music(music_id)
        else:
            return self._real_validate_music(music_id)
```

**Single interface, dual implementation**: Code using the client doesn't know or care if it's mock or real.

### Response Normalization

All API methods return normalized responses:

```python
{
    "success": bool,
    "data": {...} or None,
    "error": str or None,
    "error_details": {...} or None
}
```

This makes error handling consistent across all API calls.

## Testing Strategy

### Test Pyramid

```
    ┌─────────┐
    │   E2E   │  ← Full conversation flows
    ├─────────┤
    │  Agent  │  ← Agent logic, state management
    ├─────────┤
    │Business │  ← Validators, business rules
    │  Rules  │
    └─────────┘
```

Most tests are at the business rules layer (fast, reliable). Fewer at agent layer (LLM calls). Minimal E2E (expensive, fragile).

### Critical Test Cases

The music logic tests are most important:

```python
def test_conversions_requires_music():
    """CRITICAL: This is the primary evaluation area"""
    error = validate_music_logic("Conversions", None)
    assert error is not None  # MUST error
```

These tests document AND enforce the critical business rule.

### Mock Testing

The mock API enables comprehensive error testing:

```python
def test_music_not_found_error():
    result = api_client.validate_music("music_not_found")
    assert result["valid"] is False
    assert "doesn't exist" in result["error"]
```

Can test all error scenarios without real API.

## Key Takeaways

1. **Separation of Concerns**: Clear layers make code maintainable
2. **Structured Outputs**: JSON schemas make LLM responses predictable
3. **Pre-Submission Validation**: Catch errors before API calls
4. **Layered Prompts**: Modular prompts for different scenarios
5. **Error Interpretation**: Transform cryptic errors into actionable guidance
6. **Mock API**: Enable development and testing without credentials
7. **Defense in Depth**: Multiple enforcement points for critical rules

## What Would I Improve?

Given more time:

1. **Retry Logic**: Exponential backoff for transient failures
2. **State Persistence**: Save draft campaigns
3. **Music Recommendations**: Suggest popular music based on objective
4. **Richer Validation**: Check ad text for policy compliance
5. **Metrics**: Track conversation success rate, common failures
6. **Multi-Language**: Support for non-English campaigns
7. **Batch Creation**: Create multiple campaigns in one session
8. **A/B Testing**: Help user create variant campaigns

The current design makes all these additions straightforward because of clear separation and extensible architecture.