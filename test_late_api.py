"""
LATE Social Media API Test Script
==================================
Test posting to Twitter/X and LinkedIn via LATE unified API.

Setup:
1. Sign up at https://getlate.dev (free tier: 10 posts/mo)
2. Connect your social accounts in the dashboard
3. Get your API key from Settings > API
4. Set LATE_API_KEY environment variable
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional

# API Configuration
LATE_API_BASE = "https://api.getlate.dev/v1"


def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.getenv("LATE_API_KEY")
    if not api_key:
        raise ValueError(
            "LATE_API_KEY not set. Get your key from https://getlate.dev/dashboard/settings"
        )
    return api_key


def get_headers() -> dict:
    """Get authorization headers."""
    return {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json"
    }


# =============================================================================
# API Functions
# =============================================================================

def list_profiles() -> dict:
    """
    List all connected social media profiles.
    Returns profiles the user has connected via OAuth.
    """
    response = requests.get(
        f"{LATE_API_BASE}/profiles",
        headers=get_headers()
    )
    response.raise_for_status()
    return response.json()


def create_post(
    text: str,
    platforms: list[str],
    scheduled_for: Optional[datetime] = None,
    media_urls: Optional[list[str]] = None
) -> dict:
    """
    Create a post across multiple platforms.

    Args:
        text: Post content
        platforms: List of platforms ["twitter", "linkedin", "instagram", etc.]
        scheduled_for: Optional datetime to schedule the post
        media_urls: Optional list of media URLs to attach

    Returns:
        API response with post details
    """
    payload = {
        "text": text,
        "platforms": platforms
    }

    if scheduled_for:
        payload["scheduledFor"] = scheduled_for.isoformat()

    if media_urls:
        payload["mediaUrls"] = media_urls

    response = requests.post(
        f"{LATE_API_BASE}/post",
        headers=get_headers(),
        json=payload
    )
    response.raise_for_status()
    return response.json()


def get_post_status(post_id: str) -> dict:
    """Get the status of a scheduled/published post."""
    response = requests.get(
        f"{LATE_API_BASE}/post/{post_id}",
        headers=get_headers()
    )
    response.raise_for_status()
    return response.json()


def delete_post(post_id: str) -> dict:
    """Delete a scheduled post (before it's published)."""
    response = requests.delete(
        f"{LATE_API_BASE}/post/{post_id}",
        headers=get_headers()
    )
    response.raise_for_status()
    return response.json()


# =============================================================================
# Test Functions
# =============================================================================

def test_connection():
    """Test API connection and list connected profiles."""
    print("=" * 50)
    print("Testing LATE API Connection")
    print("=" * 50)

    try:
        profiles = list_profiles()
        print(f"\n✅ Connected successfully!")
        print(f"\nConnected profiles ({len(profiles.get('profiles', []))}):")

        for profile in profiles.get("profiles", []):
            print(f"  - {profile.get('platform')}: {profile.get('username', 'N/A')}")

        return profiles
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e.response.status_code}")
        print(f"   {e.response.text}")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def test_draft_post():
    """
    Test creating a scheduled post (scheduled far in future so we can delete it).
    This is a safe way to test without actually posting.
    """
    print("\n" + "=" * 50)
    print("Testing Draft Post Creation")
    print("=" * 50)

    # Schedule for 7 days from now (gives us time to delete)
    scheduled_time = datetime.now() + timedelta(days=7)

    test_content = f"""🧪 [TEST POST - WILL BE DELETED]

This is a test post from CanMarket's social posting integration.
Scheduled for: {scheduled_time.strftime('%Y-%m-%d %H:%M')}

#test #canmarket"""

    try:
        # Only post to platforms you have connected
        # Modify this list based on your connected accounts
        result = create_post(
            text=test_content,
            platforms=["twitter"],  # Start with just Twitter
            scheduled_for=scheduled_time
        )

        post_id = result.get("id") or result.get("postId")
        print(f"\n✅ Draft post created!")
        print(f"   Post ID: {post_id}")
        print(f"   Scheduled for: {scheduled_time}")
        print(f"\n   Response: {result}")

        return result
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e.response.status_code}")
        print(f"   {e.response.text}")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def test_immediate_post(text: str, platforms: list[str]):
    """
    Post immediately to specified platforms.
    ⚠️  WARNING: This will actually post to your accounts!
    """
    print("\n" + "=" * 50)
    print("⚠️  IMMEDIATE POST (This will be published!)")
    print("=" * 50)

    confirm = input(f"\nPost to {platforms}? (yes/no): ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        return None

    try:
        result = create_post(
            text=text,
            platforms=platforms
        )

        print(f"\n✅ Post published!")
        print(f"   Response: {result}")
        return result
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e.response.status_code}")
        print(f"   {e.response.text}")
        return None


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════╗
║         LATE Social Media API Test Script                ║
║         For CanMarket Social Posting Integration         ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # Check for API key
    try:
        api_key = get_api_key()
        print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    except ValueError as e:
        print(f"❌ {e}")
        print("\nTo get started:")
        print("1. Sign up at https://getlate.dev")
        print("2. Connect your social accounts")
        print("3. Get API key from Settings > API")
        print("4. Run: export LATE_API_KEY='your_key_here'")
        exit(1)

    # Run tests
    print("\n" + "-" * 50)
    print("Select test to run:")
    print("1. Test connection & list profiles")
    print("2. Create draft post (scheduled, safe to delete)")
    print("3. Post immediately (⚠️ will publish)")
    print("-" * 50)

    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice == "1":
        test_connection()
    elif choice == "2":
        profiles = test_connection()
        if profiles:
            test_draft_post()
    elif choice == "3":
        text = input("Enter post text: ")
        platforms = input("Platforms (comma-separated, e.g., twitter,linkedin): ").split(",")
        platforms = [p.strip() for p in platforms]
        test_immediate_post(text, platforms)
    else:
        print("Invalid choice.")
