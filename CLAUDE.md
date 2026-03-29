# CLAUDE.md

## What This Is
Multi-provider social media posting API with automatic fallback. Unified `SocialPostingClient` that posts to Twitter, LinkedIn, Instagram, Facebook, TikTok, Threads, Bluesky, YouTube, and Pinterest.

## Tech Stack
- Python 3.11+
- PostForMe API (primary provider, cheaper)
- LATE API (fallback provider)

## How to Run
```bash
source venv/bin/activate
python social_posting.py          # Test client
python test_late_api.py           # Test LATE provider
python canmarket_integration.py   # Production integration example
```

## Key Files
- `social_posting.py` — Core module: `SocialPostingClient`, `PostForMeProvider`, `LateProvider`
- `canmarket_integration.py` — Production-ready CanMarket integration
- `test_late_api.py` — LATE API evaluation script

## Architecture
```
SocialPostingClient (unified interface)
  -> PostForMeProvider (primary)
  -> LateProvider (fallback)
Each provider: get_accounts() -> upload_media() -> post()
```

## Environment Variables
```bash
POSTFORME_API_KEY   # Primary provider
LATE_API_KEY        # Fallback provider
```

## Watch Out For
- Twitter/X platform name normalization: "twitter" maps to both "twitter" and "x" for PostForMe
- Long-form posts (>280 chars) require X Premium — `long_post=True` is default
- OAuth flow (`get_oauth_url`) only available via PostForMe provider
