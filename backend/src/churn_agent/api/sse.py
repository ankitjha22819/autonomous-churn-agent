"""
Server-Sent Events (SSE) Streaming Engine.

Handles the real-time event pipe from backend workers to frontend.
Includes Nginx-compatible headers, heartbeats, and reconnection support.
"""

import json
from typing import AsyncGenerator

from fastapi import Request
from sse_starlette.sse import EventSourceResponse

from churn_agent.api.dependencies import EventManager
from churn_agent.core.config import Settings
from churn_agent.core.logging import get_logger

logger = get_logger(__name__)


# SSE Response Headers

SSE_HEADERS = {
    # Prevent caching of the event stream
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
    
    # Keep connection alive
    "Connection": "keep-alive",
    
    # Disable Nginx buffering (critical for SSE)
    "X-Accel-Buffering": "no",
    
    # CORS headers (if not handled by middleware)
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Last-Event-ID",
}


# SSE Response Factory

async def create_sse_response(
    request: Request,
    job_id: str,
    event_manager: EventManager,
    settings: Settings,
) -> EventSourceResponse:
    """
    Create an SSE response for streaming job events.
    
    Args:
        request: FastAPI request object (for disconnect detection)
        job_id: The job ID to stream events for
        event_manager: The event pub/sub manager
        settings: Application settings
        
    Returns:
        EventSourceResponse that streams events to the client
    """
    # Get Last-Event-ID for reconnection support
    last_event_id = request.headers.get("Last-Event-ID")
    
    if last_event_id:
        logger.info(
            "SSE reconnection detected",
            job_id=job_id,
            last_event_id=last_event_id,
        )
    
    return EventSourceResponse(
        _event_generator(
            request=request,
            job_id=job_id,
            event_manager=event_manager,
            last_event_id=last_event_id,
            retry_timeout=settings.sse_retry_timeout,
        ),
        headers=SSE_HEADERS,
        media_type="text/event-stream",
    )


# Event Generator

async def _event_generator(
    request: Request,
    job_id: str,
    event_manager: EventManager,
    last_event_id: str | None,
    retry_timeout: int,
) -> AsyncGenerator[dict, None]:
    """
    Async generator that yields SSE events.
    
    This is the heart of the streaming system. It:
    1. Subscribes to the Redis pub/sub channel for the job
    2. Yields events in SSE format as they arrive
    3. Sends heartbeats to keep the connection alive
    4. Handles client disconnection gracefully
    5. Closes on terminal events (job_complete, job_error)
    
    Yields:
        Event dicts compatible with sse-starlette:
        - {"event": "...", "data": "...", "id": "..."} for real events
        - {"comment": "heartbeat"} for keep-alive pings
    """
    logger.info("SSE stream started", job_id=job_id)
    event_count = 0
    
    try:
        # Send initial retry timeout instruction to client
        yield {
            "event": "connected",
            "data": json.dumps({
                "job_id": job_id,
                "message": "Connected to event stream",
            }),
            "retry": retry_timeout,
        }
        
        # Subscribe and stream events
        async for event in event_manager.subscribe(job_id, last_event_id):
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info(
                    "Client disconnected",
                    job_id=job_id,
                    events_sent=event_count,
                )
                break
            
            # Handle heartbeat (keep-alive)
            if event.get("heartbeat"):
                yield {"comment": "heartbeat"}
                continue
            
            # Format and yield the event
            event_count += 1
            
            yield {
                "id": event.get("event_id", str(event_count)),
                "event": event["event"],
                "data": json.dumps(event.get("data", {})),
            }
            
            logger.debug(
                "Event sent",
                job_id=job_id,
                event_type=event["event"],
                event_count=event_count,
            )
            
            # Check for terminal events
            if event["event"] in {"job_complete", "job_error"}:
                logger.info(
                    "Terminal event reached",
                    job_id=job_id,
                    event_type=event["event"],
                    total_events=event_count,
                )
                break
                
    except Exception as e:
        logger.error(
            "SSE stream error",
            job_id=job_id,
            error=str(e),
            events_sent=event_count,
        )
        # Send error event before closing
        yield {
            "event": "job_error",
            "data": json.dumps({
                "error_code": "STREAM_ERROR",
                "detail": "Event stream encountered an error",
                "recoverable": True,
            }),
        }
        raise
        
    finally:
        logger.info(
            "SSE stream closed",
            job_id=job_id,
            total_events=event_count,
        )


# Helper: Direct Event Sender (for testing/debugging)

def format_sse_event(
    event_type: str,
    data: dict,
    event_id: str | None = None,
) -> str:
    """
    Format an event as raw SSE text.
    
    Useful for testing or when bypassing sse-starlette.
    
    Args:
        event_type: The event type (discriminator)
        data: The event data payload
        event_id: Optional event ID for reconnection
        
    Returns:
        Formatted SSE event string
        
    Example output:
        id: evt-123
        event: agent_activity
        data: {"agent": "Analyst", "status": "thinking"}
        
    """
    lines = []
    
    if event_id:
        lines.append(f"id: {event_id}")
    
    lines.append(f"event: {event_type}")
    lines.append(f"data: {json.dumps(data)}")
    lines.append("")  # Empty line terminates the event
    
    return "\n".join(lines)