# Social Media Posting API Test

Test scripts for evaluating unified social media APIs for CanMarket.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up LATE account (free tier)
# Go to https://getlate.dev and sign up
# Connect your Twitter/LinkedIn accounts
# Get API key from Settings > API

# 3. Set environment variable
export LATE_API_KEY='your_key_here'

# 4. Run test
python test_late_api.py
```

## API Options Evaluated

| Provider | Free Tier | Price | Best For |
|----------|-----------|-------|----------|
| LATE | 10 posts/mo | $19-49/mo | Developer experience |
| Post for Me | No | $10+/mo | Volume pricing |
| Ayrshare | 20 posts/mo | $149+/mo | Enterprise |

## Integration for CanMarket

See `canmarket_integration.py` for production-ready code.
