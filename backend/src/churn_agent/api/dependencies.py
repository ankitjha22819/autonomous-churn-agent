"""
FastAPI Dependencies.

Injectable components for routes: database sessions, event managers,
job lookups, authentication, etc.
"""

from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, Header, Request, status
import redis.asyncio as redis

from churn_agent.core.config import Settings, get_settings
from churn_agent.core.logging import get_logger

logger = get_logger(__name__)


# Settings Dependency

def get_current_settings() -> Settings:
    """Inject application settings."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_current_settings)]


# Redis Connection Pool

# Global connection pool (initialized on startup)
_redis_pool: redis.ConnectionPool | None = None


async def init_redis_pool(settings: Settings) -> None:
    """Initialize Redis connection pool. Called from lifespan."""
    global _redis_pool
    _redis_pool = redis.ConnectionPool.from_url(
        str(settings.redis_url),
        max_connections=20,
        decode_responses=True,
    )
    logger.info("Redis connection pool initialized", url=str(settings.redis_url))


async def close_redis_pool() -> None:
    """Close Redis connection pool. Called from lifespan."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection pool closed")


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """
    Dependency that yields a Redis client from the pool.
    
    Usage:
        @router.get("/")
        async def my_route(redis: RedisDep):
            await redis.set("key", "value")
    """
    if _redis_pool is None:
        raise RuntimeError("Redis pool not initialized. Check application startup.")
    
    client = redis.Redis(connection_pool=_redis_pool)
    try:
        yield client
    finally:
        await client.aclose()


RedisDep = Annotated[redis.Redis, Depends(get_redis)]


# Event Manager (for SSE pub/sub)

class EventManager:
    """
    Manages Server-Sent Events pub/sub via Redis.
    
    Publishers (background workers) call `publish()`.
    SSE endpoints call `subscribe()` to get an async generator of events.
    """
    
    def __init__(self, redis_client: redis.Redis, settings: Settings):
        self.redis = redis_client
        self.settings = settings
        self.channel_prefix = settings.redis_sse_channel_prefix
    
    def _channel_name(self, job_id: str) -> str:
        """Get Redis channel name for a job."""
        return f"{self.channel_prefix}{job_id}"
    
    async def publish(self, job_id: str, event: dict) -> int:
        """
        Publish an event to a job's channel.
        
        Args:
            job_id: The job identifier
            event: Event dict with 'event' and 'data' keys
            
        Returns:
            Number of subscribers that received the message
        """
        import json
        channel = self._channel_name(job_id)
        message = json.dumps(event)
        count = await self.redis.publish(channel, message)
        logger.debug("Event published", job_id=job_id, event_type=event.get("event"), subscribers=count)
        return count
    
    async def subscribe(
        self, 
        job_id: str, 
        last_event_id: str | None = None
    ) -> AsyncGenerator[dict, None]:
        """
        Subscribe to events for a job.
        
        Yields event dicts as they arrive. Handles reconnection via last_event_id.
        
        Args:
            job_id: The job identifier
            last_event_id: Last event ID received (for reconnection)
            
        Yields:
            Event dictionaries with 'event', 'data', and optional 'id' keys
        """
        import asyncio
        import json
        
        channel = self._channel_name(job_id)
        pubsub = self.redis.pubsub()
        
        try:
            await pubsub.subscribe(channel)
            logger.debug("Subscribed to channel", channel=channel, job_id=job_id)
            
            # If reconnecting, replay missed events from Redis list
            if last_event_id:
                async for event in self._replay_missed_events(job_id, last_event_id):
                    yield event
            
            # Listen for new events
            heartbeat_interval = self.settings.sse_heartbeat_interval
            
            while True:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=heartbeat_interval
                    )
                    
                    if message and message["type"] == "message":
                        event = json.loads(message["data"])
                        yield event
                        
                        # Store event for replay on reconnection
                        await self._store_event_for_replay(job_id, event)
                        
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield {"heartbeat": True}
                    
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            logger.debug("Unsubscribed from channel", channel=channel, job_id=job_id)
    
    async def _store_event_for_replay(self, job_id: str, event: dict) -> None:
        """Store event in Redis list for potential replay."""
        import json
        key = f"events:replay:{job_id}"
        await self.redis.rpush(key, json.dumps(event))
        # Keep only last 1000 events, expire after 1 hour
        await self.redis.ltrim(key, -1000, -1)
        await self.redis.expire(key, 3600)
    
    async def _replay_missed_events(
        self, 
        job_id: str, 
        last_event_id: str
    ) -> AsyncGenerator[dict, None]:
        """Replay events missed during disconnection."""
        import json
        key = f"events:replay:{job_id}"
        events = await self.redis.lrange(key, 0, -1)
        
        found_last = False
        for event_json in events:
            event = json.loads(event_json)
            if found_last:
                yield event
            elif event.get("id") == last_event_id:
                found_last = True


async def get_event_manager(
    redis_client: RedisDep,
    settings: SettingsDep,
) -> EventManager:
    """Dependency that provides an EventManager."""
    return EventManager(redis_client, settings)


EventManagerDep = Annotated[EventManager, Depends(get_event_manager)]


# Job Lookup Dependencies

# In-memory job store (replace with DB in production)
# This is a placeholder - in real app, use SQLAlchemy + PostgreSQL
_jobs_store: dict[str, dict] = {}


async def get_job_or_404(
    job_id: UUID,
    redis_client: RedisDep,
) -> dict:
    """
    Fetch a job by ID or raise 404.
    
    In production, this would query PostgreSQL via SQLAlchemy.
    """
    job_key = f"job:{job_id}"
    
    # Try Redis first (for active jobs)
    import json
    job_data = await redis_client.get(job_key)
    
    if job_data:
        return json.loads(job_data)
    
    # Fallback to in-memory store (development only)
    if str(job_id) in _jobs_store:
        return _jobs_store[str(job_id)]
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Job {job_id} not found"
    )


JobDep = Annotated[dict, Depends(get_job_or_404)]


# Request Context Dependencies

async def get_request_id(
    request: Request,
    x_request_id: str | None = Header(default=None, alias="X-Request-ID"),
) -> str:
    """Extract or generate a request ID for tracing."""
    from uuid import uuid4
    return x_request_id or str(uuid4())


RequestIdDep = Annotated[str, Depends(get_request_id)]


# Optional: API Key Authentication (for production)

async def verify_api_key(
    settings: SettingsDep,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str | None:
    """
    Verify API key if authentication is enabled.
    
    In production, implement proper API key validation against a database.
    """
    # Skip auth in development
    if settings.is_development:
        return None
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header required",
        )
    
    # TODO: Validate against database
    # For now, just return the key
    return x_api_key


ApiKeyDep = Annotated[str | None, Depends(verify_api_key)]