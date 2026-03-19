"""API layer - FastAPI routes, dependencies, and SSE streaming."""

from churn_agent.api.router import router
from churn_agent.api.dependencies import (
    get_settings,
    get_redis,
    get_event_manager,
    init_redis_pool,
    close_redis_pool,
    EventManager,
)
from churn_agent.api.sse import create_sse_response

__all__ = [
    "router",
    "get_settings",
    "get_redis",
    "get_event_manager",
    "init_redis_pool",
    "close_redis_pool",
    "EventManager",
    "create_sse_response",
]
