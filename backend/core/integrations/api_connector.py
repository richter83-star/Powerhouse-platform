
"""
External API Connector Framework
Provides a unified interface for third-party API integrations
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel


class AuthType(str, Enum):
    """Authentication types"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer"
    OAUTH2 = "oauth2"
    BASIC = "basic"


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


class APICredentials(BaseModel):
    """API credentials model"""
    auth_type: AuthType
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    oauth_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    custom_headers: Dict[str, str] = {}


class RateLimitConfig(BaseModel):
    """Rate limit configuration"""
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    requests_per_second: float = 10.0
    burst_size: int = 20
    enabled: bool = True


class APIConnector(ABC):
    """Base class for API connectors"""
    
    def __init__(
        self,
        name: str,
        base_url: str,
        credentials: APICredentials,
        rate_limit: Optional[RateLimitConfig] = None,
        timeout: int = 30
    ):
        self.name = name
        self.base_url = base_url.rstrip('/')
        self.credentials = credentials
        self.rate_limit = rate_limit or RateLimitConfig()
        self.timeout = timeout
        
        self.client = httpx.AsyncClient(timeout=timeout)
        self._tokens = self.rate_limit.burst_size
        self._last_refill = datetime.utcnow()
        self._request_times: List[datetime] = []
        
    async def request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make authenticated API request with rate limiting"""
        await self._wait_for_rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._build_headers()
        headers.update(kwargs.pop('headers', {}))
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else {}
            
        except httpx.HTTPStatusError as e:
            raise APIError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code
            )
        except Exception as e:
            raise APIError(f"Request failed: {str(e)}")
    
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request"""
        return await self.request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """POST request"""
        return await self.request("POST", endpoint, **kwargs)
    
    async def put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """PUT request"""
        return await self.request("PUT", endpoint, **kwargs)
    
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """DELETE request"""
        return await self.request("DELETE", endpoint, **kwargs)
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        headers.update(self.credentials.custom_headers)
        
        if self.credentials.auth_type == AuthType.API_KEY:
            headers["X-API-Key"] = self.credentials.api_key or ""
        elif self.credentials.auth_type == AuthType.BEARER_TOKEN:
            headers["Authorization"] = f"Bearer {self.credentials.bearer_token}"
        elif self.credentials.auth_type == AuthType.OAUTH2:
            headers["Authorization"] = f"Bearer {self.credentials.oauth_token}"
        
        return headers
    
    async def _wait_for_rate_limit(self):
        """Wait if rate limit is reached"""
        if not self.rate_limit.enabled:
            return
        
        if self.rate_limit.strategy == RateLimitStrategy.TOKEN_BUCKET:
            await self._token_bucket_wait()
        elif self.rate_limit.strategy == RateLimitStrategy.SLIDING_WINDOW:
            await self._sliding_window_wait()
    
    async def _token_bucket_wait(self):
        """Token bucket rate limiting"""
        # Refill tokens
        now = datetime.utcnow()
        elapsed = (now - self._last_refill).total_seconds()
        refill = elapsed * self.rate_limit.requests_per_second
        self._tokens = min(self._tokens + refill, self.rate_limit.burst_size)
        self._last_refill = now
        
        # Wait if no tokens available
        while self._tokens < 1:
            wait_time = 1.0 / self.rate_limit.requests_per_second
            await asyncio.sleep(wait_time)
            elapsed = wait_time
            refill = elapsed * self.rate_limit.requests_per_second
            self._tokens = min(self._tokens + refill, self.rate_limit.burst_size)
        
        self._tokens -= 1
    
    async def _sliding_window_wait(self):
        """Sliding window rate limiting"""
        now = datetime.utcnow()
        window = timedelta(seconds=1.0)
        
        # Remove old requests
        self._request_times = [
            t for t in self._request_times
            if now - t < window
        ]
        
        # Wait if limit reached
        while len(self._request_times) >= self.rate_limit.requests_per_second:
            oldest = self._request_times[0]
            wait_time = (oldest + window - now).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            now = datetime.utcnow()
            self._request_times = [
                t for t in self._request_times
                if now - t < window
            ]
        
        self._request_times.append(now)
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test API connection"""
        pass
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class APIError(Exception):
    """API error exception"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ConnectorRegistry:
    """Registry for API connectors"""
    
    def __init__(self):
        self.connectors: Dict[str, APIConnector] = {}
    
    def register(self, name: str, connector: APIConnector):
        """Register a connector"""
        self.connectors[name] = connector
    
    def get(self, name: str) -> Optional[APIConnector]:
        """Get connector by name"""
        return self.connectors.get(name)
    
    def list(self) -> List[str]:
        """List registered connectors"""
        return list(self.connectors.keys())
    
    def unregister(self, name: str) -> bool:
        """Unregister a connector"""
        if name in self.connectors:
            del self.connectors[name]
            return True
        return False
    
    async def close_all(self):
        """Close all connectors"""
        for connector in self.connectors.values():
            await connector.close()


# Example connector implementations

class SlackConnector(APIConnector):
    """Slack API connector"""
    
    def __init__(self, token: str):
        credentials = APICredentials(
            auth_type=AuthType.BEARER_TOKEN,
            bearer_token=token
        )
        super().__init__(
            name="Slack",
            base_url="https://slack.com/api",
            credentials=credentials,
            rate_limit=RateLimitConfig(requests_per_second=1.0)
        )
    
    async def test_connection(self) -> bool:
        try:
            result = await self.post("auth.test")
            return result.get("ok", False)
        except:
            return False
    
    async def send_message(self, channel: str, text: str):
        return await self.post("chat.postMessage", json={
            "channel": channel,
            "text": text
        })


class GitHubConnector(APIConnector):
    """GitHub API connector"""
    
    def __init__(self, token: str):
        credentials = APICredentials(
            auth_type=AuthType.BEARER_TOKEN,
            bearer_token=token
        )
        super().__init__(
            name="GitHub",
            base_url="https://api.github.com",
            credentials=credentials,
            rate_limit=RateLimitConfig(requests_per_second=5000.0/3600.0)  # 5000/hour
        )
    
    async def test_connection(self) -> bool:
        try:
            result = await self.get("user")
            return "login" in result
        except:
            return False
    
    async def get_repo(self, owner: str, repo: str):
        return await self.get(f"repos/{owner}/{repo}")


# Global registry
connector_registry = ConnectorRegistry()
