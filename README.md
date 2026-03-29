# Social Posting API

Multi-provider social media posting API with automatic fallback.

## What This Does

A unified Python client for posting content to social media platforms (Twitter, LinkedIn, Instagram, Facebook, TikTok, Threads, Bluesky, YouTube, Pinterest). Uses a dual-provider architecture — PostForMe as the primary (cheaper, volume-friendly) and LATE as the fallback (reliable backup). Supports text posts, media attachments, and multi-platform publishing in a single call.

## Tech Stack

- Python 3.11+
- requests (HTTP client)
- PostForMe API (primary provider)
- LATE API (fallback provider)

## Setup

```bash
git clone https://github.com/Canlah-AI/social-posting-api.git
cd social-posting-api
cp .env.example .env  # Fill in PostForMe and LATE API keys
pip install -r requirements.txt
```

## Usage

```python
from social_posting import SocialPostingClient

client = SocialPostingClient()
result = client.post(
    content="Hello world!",
    platforms=["linkedin", "instagram"],
    media_urls=["https://example.com/image.jpg"]
)
```

## Key Files

| File | Purpose |
|------|---------|
| `social_posting.py` | Unified client with provider abstraction and auto-fallback |
| `canmarket_integration.py` | Integration adapter for CanMarket pipeline |
| `test_late_api.py` | Provider test scripts |

## Related

Used by [canmarket-bot](https://github.com/Canlah-AI/canmarket-bot) for automated content publishing. Part of the [CanMarket](https://github.com/Canlah-AI/market) ecosystem.
