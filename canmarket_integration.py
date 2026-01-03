"""
CanMarket Social Posting Integration
=====================================
Production-ready module for posting user-generated content to social media.

This module handles:
- Multi-platform posting via LATE API
- User account management
- Scheduling and queue management
- Error handling and retries
"""

import os
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class Platform(Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    THREADS = "threads"
    BLUESKY = "bluesky"


@dataclass
class PostResult:
    success: bool
    post_id: Optional[str] = None
    platform_post_ids: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    scheduled_for: Optional[datetime] = None


class SocialPostingClient:
    """
    Client for posting to social media via LATE API.

    Usage:
        client = SocialPostingClient(api_key="your_key")

        # Post immediately
        result = client.post(
            text="Hello world!",
            platforms=[Platform.TWITTER, Platform.LINKEDIN]
        )

        # Schedule for later
        result = client.post(
            text="Scheduled post",
            platforms=[Platform.TWITTER],
            scheduled_for=datetime(2025, 1, 10, 9, 0)
        )
    """

    BASE_URL = "https://getlate.dev/api/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LATE_API_KEY")
        if not self.api_key:
            raise ValueError("API key required. Set LATE_API_KEY or pass api_key.")

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all connected social media accounts."""
        response = requests.get(
            f"{self.BASE_URL}/accounts",
            headers=self._headers
        )
        response.raise_for_status()
        return response.json().get("accounts", [])

    def get_connected_platforms(self) -> List[str]:
        """Get list of platform names that are connected."""
        accounts = self.get_accounts()
        return [a.get("platform") for a in accounts]

    def get_account_info(self) -> List[Dict[str, str]]:
        """Get connected account names and platforms."""
        accounts = self.get_accounts()
        return [
            {
                "platform": a.get("platform"),
                "username": a.get("username") or a.get("displayName"),
                "id": a.get("_id")
            }
            for a in accounts
        ]

    def upload_media(self, image_url: str) -> Optional[str]:
        """
        Upload media via presigned URL for use in posts.

        Args:
            image_url: URL of image to download and upload

        Returns:
            Public URL of uploaded media, or None on failure
        """
        try:
            # Download image
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            img_data = img_response.content

            # Get presigned URL
            presign_response = requests.post(
                f"{self.BASE_URL}/media/presign",
                headers=self._headers,
                json={"filename": "media.jpg", "contentType": "image/jpeg"}
            )
            presign_response.raise_for_status()
            presign_data = presign_response.json()

            # Upload to presigned URL
            upload_response = requests.put(
                presign_data["uploadUrl"],
                data=img_data,
                headers={"Content-Type": "image/jpeg"}
            )
            upload_response.raise_for_status()

            return presign_data["publicUrl"]
        except Exception:
            return None

    def post(
        self,
        content: str,
        platforms: List[Platform],
        scheduled_for: Optional[datetime] = None,
        media_urls: Optional[List[str]] = None,
        title: Optional[str] = None
    ) -> PostResult:
        """
        Create a post across multiple platforms.

        Args:
            content: Post content
            platforms: List of Platform enums to post to
            scheduled_for: Optional datetime to schedule (UTC)
            media_urls: Optional list of media URLs (images/videos)
            title: Optional post title

        Returns:
            PostResult with success status and details

        Note:
            Instagram requires media - text-only posts will fail.
            Use upload_media() first to get proper media URLs.
        """
        # Get accounts for specified platforms
        accounts = self.get_accounts()
        platform_configs = []

        for platform in platforms:
            matching = [a for a in accounts if a.get("platform") == platform.value]
            if matching:
                account = matching[0]
                platform_configs.append({
                    "platform": platform.value,
                    "accountId": account["_id"],
                    "profileId": account["profileId"]["_id"]
                })

        if not platform_configs:
            return PostResult(
                success=False,
                error=f"No connected accounts for platforms: {[p.value for p in platforms]}"
            )

        payload = {
            "content": content,
            "platforms": platform_configs
        }

        if scheduled_for:
            payload["scheduledFor"] = scheduled_for.isoformat()

        if media_urls:
            # mediaItems must be objects with url and type fields
            payload["mediaItems"] = [
                {"url": url, "type": "image"} for url in media_urls
            ]

        if title:
            payload["title"] = title

        try:
            response = requests.post(
                f"{self.BASE_URL}/posts",
                headers=self._headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            post_data = data.get("post", {})
            return PostResult(
                success=True,
                post_id=post_data.get("_id"),
                platform_post_ids={
                    p["platform"]: p.get("platformPostId", p["_id"])
                    for p in post_data.get("platforms", [])
                },
                scheduled_for=scheduled_for
            )
        except requests.exceptions.HTTPError as e:
            return PostResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}"
            )
        except Exception as e:
            return PostResult(
                success=False,
                error=str(e)
            )

    def delete_post(self, post_id: str) -> bool:
        """Delete a scheduled post before it's published."""
        try:
            response = requests.delete(
                f"{self.BASE_URL}/posts/{post_id}",
                headers=self._headers
            )
            response.raise_for_status()
            return True
        except:
            return False

    def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get details of a post."""
        response = requests.get(
            f"{self.BASE_URL}/posts/{post_id}",
            headers=self._headers
        )
        response.raise_for_status()
        return response.json()

    def list_posts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all posts, optionally filtered by status."""
        params = {}
        if status:
            params["status"] = status
        response = requests.get(
            f"{self.BASE_URL}/posts",
            headers=self._headers,
            params=params
        )
        response.raise_for_status()
        return response.json().get("posts", [])


# =============================================================================
# CanMarket-specific wrapper for multi-user scenarios
# =============================================================================

class CanMarketSocialPoster:
    """
    Higher-level wrapper for CanMarket's multi-user posting needs.

    In production, you would:
    1. Store user's LATE API key in your database (after they OAuth connect)
    2. Retrieve it when posting on their behalf
    3. Track post history and analytics
    """

    def __init__(self):
        # In production, this would be a database connection
        self._user_keys: Dict[str, str] = {}

    def register_user_key(self, user_id: str, late_api_key: str):
        """
        Store a user's LATE API key after they complete OAuth.
        In production, encrypt and store in database.
        """
        self._user_keys[user_id] = late_api_key

    def post_for_user(
        self,
        user_id: str,
        content: str,
        platforms: List[str],
        scheduled_for: Optional[datetime] = None
    ) -> PostResult:
        """
        Post content on behalf of a user.

        Args:
            user_id: Your internal user ID
            content: The content generated by CanMarket
            platforms: List of platform names ["twitter", "linkedin"]
            scheduled_for: Optional schedule time
        """
        api_key = self._user_keys.get(user_id)
        if not api_key:
            return PostResult(
                success=False,
                error=f"User {user_id} has not connected their social accounts"
            )

        client = SocialPostingClient(api_key=api_key)

        platform_enums = []
        for p in platforms:
            try:
                platform_enums.append(Platform(p.lower()))
            except ValueError:
                pass  # Skip invalid platform names

        if not platform_enums:
            return PostResult(
                success=False,
                error="No valid platforms specified"
            )

        return client.post(
            content=content,
            platforms=platform_enums,
            scheduled_for=scheduled_for
        )


# =============================================================================
# Example usage
# =============================================================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("Testing CanMarket Social Posting Integration\n")

    try:
        client = SocialPostingClient()

        print("Connected accounts:")
        for account in client.get_account_info():
            print(f"  - {account['platform']}: {account['username']}")

        print(f"\nPlatforms: {client.get_connected_platforms()}")
        print("\nIntegration ready!")

    except ValueError as e:
        print(f"Setup needed: {e}")
        print("\nTo test:")
        print("1. Sign up at https://getlate.dev")
        print("2. Connect your social accounts")
        print("3. Add LATE_API_KEY to .env file")
        print("4. python canmarket_integration.py")
