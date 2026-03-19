"""
API Router - Route definitions for the Churn Analysis API.

This module defines all HTTP endpoints. Business logic is delegated
to services; this layer handles HTTP concerns only.
"""

import json
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from churn_agent.api.dependencies import (
    EventManagerDep,
    JobDep,
    RedisDep,
    RequestIdDep,
    SettingsDep,
    _jobs_store,
)
from churn_agent.api.sse import create_sse_response
from churn_agent.core.logging import get_logger, LogContext
from churn_agent.schemas import (
    AnalysisRequest,
    JobCreatedResponse,
    JobStatus,
    JobStatusResponse,
)

logger = get_logger(__name__)

# Router Setup

router = APIRouter(prefix="/analysis", tags=["Analysis"])


# Health & Info Endpoints

@router.get("/health", tags=["Health"])
async def health_check(redis: RedisDep) -> dict:
    """
    Health check endpoint.
    
    Verifies core dependencies (Redis) are accessible.
    """
    try:
        await redis.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {e}"
    
    return {
        "status": "healthy" if redis_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "redis": redis_status,
        },
    }


# Job Management Endpoints

@router.post(
    "/jobs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobCreatedResponse,
    summary="Create Analysis Job",
    description="Initiate a new churn analysis job. Returns immediately with job ID.",
)
async def create_analysis_job(
    payload: AnalysisRequest,
    background_tasks: BackgroundTasks,
    redis: RedisDep,
    settings: SettingsDep,
    request_id: RequestIdDep,
) -> JobCreatedResponse:
    """
    Create a new churn analysis job.
    
    This endpoint:
    1. Validates the request payload
    2. Creates a job record
    3. Enqueues the job for background processing
    4. Returns immediately with the job ID (HTTP 202)
    
    The client should then connect to the SSE endpoint to receive updates.
    """
    job_id = uuid4()
    
    with LogContext(job_id=str(job_id), request_id=request_id):
        logger.info(
            "Creating analysis job",
            customer_count=len(payload.customers) if payload.customers else 0,
            data_source_id=payload.data_source_id,
        )
        
        # Create job record
        job_data = {
            "id": str(job_id),
            "status": JobStatus.PENDING.value,
            "payload": payload.model_dump(mode="json"),
            "created_at": datetime.utcnow().isoformat(),
            "request_id": request_id,
        }
        
        # Store in Redis (with 24h expiry)
        job_key = f"job:{job_id}"
        await redis.set(job_key, json.dumps(job_data), ex=86400)
        
        # Also store in memory for development
        _jobs_store[str(job_id)] = job_data
        
        # Enqueue for background processing
        # In production: celery_app.send_task("process_analysis", args=[str(job_id)])
        background_tasks.add_task(
            _mock_background_processing,
            str(job_id),
            redis,
            settings,
        )
        
        logger.info("Job created and enqueued", job_id=str(job_id))
        
        return JobCreatedResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            events_url=f"{settings.api_prefix}/analysis/jobs/{job_id}/events",
            estimated_duration_seconds=30,
        )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get Job Status",
)
async def get_job_status(
    job: JobDep,
) -> JobStatusResponse:
    """
    Get the current status of a job.
    
    For real-time updates, use the SSE endpoint instead.
    """
    return JobStatusResponse(
        job_id=UUID(job["id"]),
        status=JobStatus(job["status"]),
        progress=job.get("progress"),
        current_step=job.get("current_step"),
        created_at=datetime.fromisoformat(job["created_at"]),
        started_at=datetime.fromisoformat(job["started_at"]) if job.get("started_at") else None,
        completed_at=datetime.fromisoformat(job["completed_at"]) if job.get("completed_at") else None,
        error=job.get("error"),
    )


@router.get(
    "/jobs/{job_id}/events",
    summary="Stream Job Events",
    description="Server-Sent Events endpoint for real-time job updates.",
    responses={
        200: {
            "description": "SSE event stream",
            "content": {"text/event-stream": {}},
        },
        404: {"description": "Job not found"},
    },
)
async def stream_job_events(
    request: Request,
    job_id: UUID,
    job: JobDep,
    events: EventManagerDep,
    settings: SettingsDep,
):
    """
    Stream real-time events for a job via Server-Sent Events.
    
    Event types:
    - `agent_activity`: Agent status updates
    - `thinking`: Agent reasoning steps
    - `tool_usage`: Tool invocations
    - `report_ready`: Final analysis report
    - `job_progress`: Overall progress updates
    - `job_complete`: Job finished successfully
    - `job_error`: Job failed
    
    Supports automatic reconnection via Last-Event-ID header.
    """
    logger.info("SSE connection requested", job_id=str(job_id))
    
    return await create_sse_response(
        request=request,
        job_id=str(job_id),
        event_manager=events,
        settings=settings,
    )


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel Job",
)
async def cancel_job(
    job_id: UUID,
    job: JobDep,
    redis: RedisDep,
) -> None:
    """
    Cancel a running or pending job.
    
    Already completed jobs cannot be cancelled.
    """
    current_status = JobStatus(job["status"])
    
    if current_status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {current_status.value}",
        )
    
    # Update status
    job["status"] = JobStatus.CANCELLED.value
    job["completed_at"] = datetime.utcnow().isoformat()
    
    job_key = f"job:{job_id}"
    await redis.set(job_key, json.dumps(job), ex=86400)
    
    if str(job_id) in _jobs_store:
        _jobs_store[str(job_id)] = job
    
    # TODO: Actually cancel the Celery task
    # celery_app.control.revoke(task_id, terminate=True)
    
    logger.info("Job cancelled", job_id=str(job_id))


# Mock Background Processing (Development Only)

async def _mock_background_processing(
    job_id: str,
    redis: RedisDep,
    settings: SettingsDep,
) -> None:
    """
    Simulate CrewAI processing for development/testing.
    
    In production, this would be a Celery task that runs the actual
    CrewAI agents and publishes events via EventManager.
    """
    import asyncio
    from churn_agent.api.dependencies import EventManager
    
    event_manager = EventManager(redis, settings)
    
    logger.info("Starting mock background processing", job_id=job_id)
    
    # Update job status to running
    job_key = f"job:{job_id}"
    job_data = json.loads(await redis.get(job_key))
    job_data["status"] = JobStatus.RUNNING.value
    job_data["started_at"] = datetime.utcnow().isoformat()
    await redis.set(job_key, json.dumps(job_data), ex=86400)
    
    try:
        # Simulate agent activities
        agents = [
            ("Data Analyst", "Analyzing customer engagement patterns"),
            ("Risk Assessor", "Calculating churn probability scores"),
            ("Strategy Expert", "Generating retention recommendations"),
        ]
        
        for i, (agent, task) in enumerate(agents):
            # Agent thinking
            await event_manager.publish(job_id, {
                "event": "agent_activity",
                "event_id": f"evt-{i*3+1}",
                "data": {
                    "agent": agent,
                    "message": f"Starting: {task}",
                    "status": "thinking",
                },
            })
            await asyncio.sleep(1)
            
            # Agent executing
            await event_manager.publish(job_id, {
                "event": "agent_activity",
                "event_id": f"evt-{i*3+2}",
                "data": {
                    "agent": agent,
                    "message": f"Processing: {task}",
                    "status": "executing",
                },
            })
            await asyncio.sleep(2)
            
            # Progress update
            await event_manager.publish(job_id, {
                "event": "job_progress",
                "event_id": f"evt-{i*3+3}",
                "data": {
                    "current_step": i + 1,
                    "total_steps": len(agents),
                    "step_name": task,
                    "percentage": ((i + 1) / len(agents)) * 100,
                },
            })
        
        # Report ready
        await event_manager.publish(job_id, {
            "event": "report_ready",
            "event_id": "evt-report",
            "data": {
                "summary": "Analysis complete. 15% of customers are at high churn risk.",
                "risk_score": 42.5,
                "total_analyzed": 150,
                "high_risk_count": 23,
                "predictions": [
                    {
                        "customer_id": "CUST-001",
                        "risk_score": 85.2,
                        "risk_level": "critical",
                        "confidence": 0.92,
                        "top_factors": ["Low engagement", "Support tickets"],
                    },
                    {
                        "customer_id": "CUST-002",
                        "risk_score": 72.1,
                        "risk_level": "high",
                        "confidence": 0.87,
                        "top_factors": ["Contract ending", "Decreased usage"],
                    },
                ],
                "recommended_actions": [
                    "Schedule check-in calls with critical risk customers",
                    "Launch re-engagement campaign for high-risk segment",
                    "Review pricing for customers with contract renewals",
                ],
                "insights": [
                    "Customers with < 5 logins/month have 3x higher churn risk",
                    "NPS scores below 6 correlate with 65% churn probability",
                    "Enterprise segment shows lowest churn risk overall",
                ],
                "generated_at": datetime.utcnow().isoformat(),
            },
        })
        
        # Job complete
        await event_manager.publish(job_id, {
            "event": "job_complete",
            "event_id": "evt-complete",
            "data": {
                "status": "success",
                "message": "Analysis completed successfully",
                "duration_seconds": 10.5,
            },
        })
        
        # Update job record
        job_data["status"] = JobStatus.COMPLETED.value
        job_data["completed_at"] = datetime.utcnow().isoformat()
        job_data["progress"] = 100
        await redis.set(job_key, json.dumps(job_data), ex=86400)
        
        if job_id in _jobs_store:
            _jobs_store[job_id] = job_data
            
    except Exception as e:
        logger.error("Mock processing failed", job_id=job_id, error=str(e))
        
        await event_manager.publish(job_id, {
            "event": "job_error",
            "event_id": "evt-error",
            "data": {
                "error_code": "PROCESSING_ERROR",
                "detail": str(e),
                "recoverable": False,
            },
        })
        
        job_data["status"] = JobStatus.FAILED.value
        job_data["error"] = str(e)
        await redis.set(job_key, json.dumps(job_data), ex=86400)