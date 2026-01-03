"""
CanMarket Social Posting - Multi-Provider Architecture
=======================================================
Unified interface for social media posting with automatic fallback.

Providers:
- PostForMe (primary) - Cheaper, volume-friendly
- LATE (fallback) - Reliable backup

Usage:
    client = SocialPostingClient()

    # Post to multiple platforms
    result = client.post(
        content="Hello world!",
        platforms=["linkedin", "instagram"],
        media_urls=["https://example.com/image.jpg"]
    )
"""

import os
import time
import requests
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class Platform(Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    THREADS = "threads"
    BLUESKY = "bluesky"
    YOUTUBE = "youtube"
    PINTEREST = "pinterest"


@dataclass
class PostResult:
    success: bool
    post_id: Optional[str] = None
    platform_post_ids: Optional[Dict[str, str]] = None
    platform_post_urls: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    scheduled_for: Optional[datetime] = None


@dataclass
class AccountInfo:
    id: str
    platform: str
    username: str
    profile_id: Optional[str] = None


# =============================================================================
# Abstract Provider Interface
# =============================================================================

class SocialPostingProvider(ABC):
    """Abstract base class for social posting providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        pass

    @abstractmethod
    def get_accounts(self) -> List[AccountInfo]:
        """Get connected social accounts."""
        pass

    @abstractmethod
    def upload_media(self, image_url: str) -> Optional[str]:
        """Upload media and return the hosted URL."""
        pass

    @abstractmethod
    def post(
        self,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None,
        scheduled_for: Optional[datetime] = None
    ) -> PostResult:
        """Create a post across platforms."""
        pass


# =============================================================================
# Post for Me Provider
# =============================================================================

class PostForMeProvider(SocialPostingProvider):
    """Post for Me API provider - primary, cheaper option."""

    BASE_URL = "https://api.postforme.dev/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("POSTFORME_API_KEY")
        if not self.api_key:
            raise ValueError("POSTFORME_API_KEY required")

    def get_oauth_url(self, platform: str, redirect_url: str) -> Optional[str]:
        """
        Generate OAuth URL for a user to connect their social account.

        This enables multi-tenant support - YOUR users connect THEIR accounts.

        Args:
            platform: 'linkedin', 'instagram', 'facebook', 'tiktok', etc.
            redirect_url: Your app's callback URL

        Returns:
            OAuth URL to redirect user to, or None on failure
        """
        try:
            response = requests.post(
                f"{self.BASE_URL}/social-accounts/auth-url",
                headers=self._headers,
                json={
                    "platform": platform,
                    "redirect_url": redirect_url
                }
            )
            response.raise_for_status()
            data = response.json()
            return data.get("url") or data.get("data", {}).get("auth_url")
        except Exception:
            return None

    @property
    def name(self) -> str:
        return "PostForMe"

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_accounts(self) -> List[AccountInfo]:
        """Get connected social accounts."""
        response = requests.get(
            f"{self.BASE_URL}/social-accounts",
            headers=self._headers
        )
        response.raise_for_status()
        data = response.json()

        accounts = []
        for item in data.get("data", []):
            accounts.append(AccountInfo(
                id=item.get("id"),
                platform=item.get("platform"),
                username=item.get("username") or item.get("user_id"),
                profile_id=None
            ))
        return accounts

    def upload_media(self, image_url: str) -> Optional[str]:
        """Upload media via presigned URL."""
        try:
            # Download image
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            img_data = img_response.content

            # Get upload URL
            upload_response = requests.post(
                f"{self.BASE_URL}/media/create-upload-url",
                headers=self._headers,
                json={"content_type": "image/jpeg"}
            )
            upload_response.raise_for_status()
            upload_data = upload_response.json()

            # Upload to presigned URL
            requests.put(
                upload_data["upload_url"],
                data=img_data,
                headers={"Content-Type": "image/jpeg"}
            )

            return upload_data.get("media_url")
        except Exception:
            return None

    def post(
        self,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None,
        scheduled_for: Optional[datetime] = None
    ) -> PostResult:
        """Create post via Post for Me API."""
        try:
            # Get accounts matching platforms
            accounts = self.get_accounts()
            account_ids = [
                a.id for a in accounts
                if a.platform in platforms
            ]

            if not account_ids:
                return PostResult(
                    success=False,
                    error=f"No connected accounts for: {platforms}",
                    provider=self.name
                )

            payload = {
                "caption": content,
                "social_accounts": account_ids
            }

            if media_urls:
                payload["media"] = [{"url": url} for url in media_urls]

            if scheduled_for:
                payload["scheduled_at"] = scheduled_for.isoformat()

            response = requests.post(
                f"{self.BASE_URL}/social-posts",
                headers=self._headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # PostForMe returns post directly, not wrapped in "data"
            post_id = data.get("id") or data.get("data", {}).get("id")
            return PostResult(
                success=True,
                post_id=post_id,
                provider=self.name
            )

        except requests.exceptions.HTTPError as e:
            return PostResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
                provider=self.name
            )
        except Exception as e:
            return PostResult(
                success=False,
                error=str(e),
                provider=self.name
            )


# =============================================================================
# LATE Provider
# =============================================================================

class LateProvider(SocialPostingProvider):
    """LATE API provider - reliable fallback."""

    BASE_URL = "https://getlate.dev/api/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LATE_API_KEY")
        if not self.api_key:
            raise ValueError("LATE_API_KEY required")

    @property
    def name(self) -> str:
        return "LATE"

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_accounts(self) -> List[AccountInfo]:
        """Get connected social accounts."""
        response = requests.get(
            f"{self.BASE_URL}/accounts",
            headers=self._headers
        )
        response.raise_for_status()
        data = response.json()

        accounts = []
        for item in data.get("accounts", []):
            accounts.append(AccountInfo(
                id=item.get("_id"),
                platform=item.get("platform"),
                username=item.get("username") or item.get("displayName"),
                profile_id=item.get("profileId", {}).get("_id") if isinstance(item.get("profileId"), dict) else item.get("profileId")
            ))
        return accounts

    def upload_media(self, image_url: str) -> Optional[str]:
        """Upload media via presigned URL."""
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

            # Upload
            requests.put(
                presign_data["uploadUrl"],
                data=img_data,
                headers={"Content-Type": "image/jpeg"}
            )

            time.sleep(1)  # Allow propagation
            return presign_data.get("publicUrl")
        except Exception:
            return None

    def post(
        self,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None,
        scheduled_for: Optional[datetime] = None
    ) -> PostResult:
        """Create post via LATE API."""
        try:
            # Get accounts matching platforms
            accounts = self.get_accounts()
            platform_configs = []

            for platform in platforms:
                matching = [a for a in accounts if a.platform == platform]
                if matching:
                    account = matching[0]
                    platform_configs.append({
                        "platform": platform,
                        "accountId": account.id,
                        "profileId": account.profile_id
                    })

            if not platform_configs:
                return PostResult(
                    success=False,
                    error=f"No connected accounts for: {platforms}",
                    provider=self.name
                )

            payload = {
                "content": content,
                "platforms": platform_configs
            }

            if media_urls:
                payload["mediaItems"] = [
                    {"url": url, "type": "image"} for url in media_urls
                ]

            if scheduled_for:
                payload["scheduledFor"] = scheduled_for.isoformat()

            response = requests.post(
                f"{self.BASE_URL}/posts",
                headers=self._headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            post_data = data.get("post", {})
            platform_ids = {}
            platform_urls = {}

            for p in post_data.get("platforms", []):
                platform_ids[p["platform"]] = p.get("platformPostId", p.get("_id"))
                if p.get("platformPostUrl"):
                    platform_urls[p["platform"]] = p["platformPostUrl"]

            return PostResult(
                success=True,
                post_id=post_data.get("_id"),
                platform_post_ids=platform_ids,
                platform_post_urls=platform_urls,
                provider=self.name
            )

        except requests.exceptions.HTTPError as e:
            return PostResult(
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
                provider=self.name
            )
        except Exception as e:
            return PostResult(
                success=False,
                error=str(e),
                provider=self.name
            )


# =============================================================================
# Unified Client with Fallback
# =============================================================================

class SocialPostingClient:
    """
    Unified social posting client with automatic provider fallback.

    Usage:
        client = SocialPostingClient()

        # Uses PostForMe first, falls back to LATE if it fails
        result = client.post(
            content="Hello!",
            platforms=["linkedin", "instagram"],
            media_urls=["https://example.com/image.jpg"]
        )

        print(f"Posted via: {result.provider}")
    """

    def __init__(
        self,
        postforme_key: Optional[str] = None,
        late_key: Optional[str] = None,
        primary: str = "postforme"  # or "late"
    ):
        self.providers: List[SocialPostingProvider] = []

        # Initialize providers based on available keys
        if primary == "postforme":
            self._try_add_provider(PostForMeProvider, postforme_key, "POSTFORME_API_KEY")
            self._try_add_provider(LateProvider, late_key, "LATE_API_KEY")
        else:
            self._try_add_provider(LateProvider, late_key, "LATE_API_KEY")
            self._try_add_provider(PostForMeProvider, postforme_key, "POSTFORME_API_KEY")

        if not self.providers:
            raise ValueError("No valid API keys found. Set POSTFORME_API_KEY or LATE_API_KEY")

    def _try_add_provider(self, provider_class, key: Optional[str], env_var: str):
        """Try to initialize a provider, skip if no key available."""
        try:
            if key or os.getenv(env_var):
                self.providers.append(provider_class(api_key=key))
        except ValueError:
            pass  # No key available, skip this provider

    @property
    def primary_provider(self) -> SocialPostingProvider:
        """Get the primary provider."""
        return self.providers[0]

    @property
    def available_providers(self) -> List[str]:
        """List available provider names."""
        return [p.name for p in self.providers]

    def get_accounts(self, provider: Optional[str] = None) -> List[AccountInfo]:
        """Get connected accounts from specified or primary provider."""
        if provider:
            for p in self.providers:
                if p.name.lower() == provider.lower():
                    return p.get_accounts()
        return self.primary_provider.get_accounts()

    def upload_media(self, image_url: str, provider: Optional[str] = None) -> Optional[str]:
        """Upload media using specified or primary provider."""
        if provider:
            for p in self.providers:
                if p.name.lower() == provider.lower():
                    return p.upload_media(image_url)

        # Try each provider until one works
        for p in self.providers:
            result = p.upload_media(image_url)
            if result:
                return result
        return None

    def get_oauth_url(self, platform: str, redirect_url: str) -> Optional[str]:
        """
        Generate OAuth URL for user to connect their social account.
        Only available with PostForMe provider.

        Usage in your app:
            url = client.get_oauth_url('instagram', 'https://yourapp.com/callback')
            # Redirect user to this URL
            # After auth, they'll be redirected back with connected account
        """
        for p in self.providers:
            if hasattr(p, 'get_oauth_url'):
                return p.get_oauth_url(platform, redirect_url)
        return None

    def post(
        self,
        content: str,
        platforms: List[str],
        media_urls: Optional[List[str]] = None,
        scheduled_for: Optional[datetime] = None,
        provider: Optional[str] = None
    ) -> PostResult:
        """
        Post to social platforms with automatic fallback.

        Args:
            content: Post text
            platforms: List of platform names ["linkedin", "instagram"]
            media_urls: Optional list of media URLs
            scheduled_for: Optional schedule datetime (UTC)
            provider: Force specific provider (skip fallback)

        Returns:
            PostResult with success status and provider used
        """
        # If specific provider requested
        if provider:
            for p in self.providers:
                if p.name.lower() == provider.lower():
                    return p.post(content, platforms, media_urls, scheduled_for)
            return PostResult(
                success=False,
                error=f"Provider '{provider}' not available"
            )

        # Try each provider with fallback
        last_error = None
        for p in self.providers:
            result = p.post(content, platforms, media_urls, scheduled_for)
            if result.success:
                return result
            last_error = result.error

        return PostResult(
            success=False,
            error=f"All providers failed. Last error: {last_error}"
        )


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    print("Social Posting - Multi-Provider Test\n")

    try:
        client = SocialPostingClient()
        print(f"Available providers: {client.available_providers}")
        print(f"Primary: {client.primary_provider.name}\n")

        print("Connected accounts:")
        for account in client.get_accounts():
            print(f"  - {account.platform}: {account.username}")

    except ValueError as e:
        print(f"Setup needed: {e}")
        print("\nSet environment variables:")
        print("  POSTFORME_API_KEY=your_key")
        print("  LATE_API_KEY=your_key")
