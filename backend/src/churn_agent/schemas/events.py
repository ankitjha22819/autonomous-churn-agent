"""
SSE Event Schemas - The Discriminator Pattern.

These Pydantic models define the strict contract for all events
streamed from the backend to the frontend via Server-Sent Events.

The TypeScript types in frontend/src/types/events.ts should mirror these exactly.
"""

from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# Base Event Structure

class BaseEvent(BaseModel):
    """
    Base class for all SSE events.
    
    Every event has:
    - event: The discriminator field (used by EventSource.addEventListener)
    - timestamp: When the event was generated
    - event_id: Unique ID for reconnection handling (Last-Event-ID)
    """
    
    event: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_id: str | None = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str,
        }


# Agent Activity Events

class AgentActivityData(BaseModel):
    """Data payload for agent activity updates."""
    
    agent: str = Field(..., description="Name of the agent (e.g., 'Data Analyst')")
    message: str = Field(..., description="What the agent is currently doing")
    status: Literal["thinking", "executing", "completed", "error"] = Field(
        ..., description="Current agent status"
    )
    progress: float | None = Field(
        default=None, 
        ge=0, 
        le=100,
        description="Optional progress percentage"
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional context (tool being used, etc.)"
    )


class AgentActivityEvent(BaseEvent):
    """
    Fired when an agent starts/updates/completes a task.
    
    Frontend handler: Updates the activity log panel.
    """
    
    event: Literal["agent_activity"] = "agent_activity"
    data: AgentActivityData


# Thinking/Reasoning Events

class ThinkingData(BaseModel):
    """Data payload for agent thinking/reasoning updates."""
    
    agent: str
    thought: str = Field(..., description="The agent's current reasoning step")
    step: int = Field(default=1, ge=1, description="Step number in reasoning chain")
    total_steps: int | None = Field(default=None, description="Expected total steps if known")


class ThinkingEvent(BaseEvent):
    """
    Fired when an agent is reasoning through a problem.
    
    Frontend handler: Updates a "thinking" indicator with streaming text.
    """
    
    event: Literal["thinking"] = "thinking"
    data: ThinkingData


# Tool Usage Events

class ToolUsageData(BaseModel):
    """Data payload for tool invocation events."""
    
    agent: str
    tool_name: str = Field(..., description="Name of the tool being used")
    tool_input: dict[str, Any] = Field(default_factory=dict, description="Tool input parameters")
    status: Literal["started", "completed", "error"] = "started"
    result: Any | None = Field(default=None, description="Tool output (on completion)")
    error: str | None = Field(default=None, description="Error message if failed")
    duration_ms: int | None = Field(default=None, description="Execution time in milliseconds")


class ToolUsageEvent(BaseEvent):
    """
    Fired when an agent uses a tool.
    
    Frontend handler: Updates tool activity indicator.
    """
    
    event: Literal["tool_usage"] = "tool_usage"
    data: ToolUsageData


# Report/Analysis Events

class ChurnPrediction(BaseModel):
    """Individual customer churn prediction."""
    
    customer_id: str
    risk_score: Annotated[float, Field(ge=0, le=100)]
    risk_level: Literal["low", "medium", "high", "critical"]
    confidence: Annotated[float, Field(ge=0, le=1)]
    top_factors: list[str] = Field(default_factory=list)


class ReportReadyData(BaseModel):
    """Data payload for completed analysis reports."""
    
    summary: str = Field(..., description="Executive summary of the analysis")
    risk_score: Annotated[float, Field(ge=0, le=100, description="Overall cohort risk score")]
    total_analyzed: int = Field(..., ge=0)
    high_risk_count: int = Field(default=0, ge=0)
    predictions: list[ChurnPrediction] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ReportReadyEvent(BaseEvent):
    """
    Fired when the analysis report is ready.
    
    Frontend handler: Renders the full report panel.
    """
    
    event: Literal["report_ready"] = "report_ready"
    data: ReportReadyData


# Job Lifecycle Events

class JobProgressData(BaseModel):
    """Data payload for job progress updates."""
    
    current_step: int
    total_steps: int
    step_name: str
    percentage: Annotated[float, Field(ge=0, le=100)]


class JobProgressEvent(BaseEvent):
    """
    Fired to update overall job progress.
    
    Frontend handler: Updates progress bar.
    """
    
    event: Literal["job_progress"] = "job_progress"
    data: JobProgressData


class JobCompleteData(BaseModel):
    """Data payload for job completion."""
    
    status: Literal["success", "partial"] = "success"
    message: str = "Analysis completed successfully"
    duration_seconds: float | None = None


class JobCompleteEvent(BaseEvent):
    """
    Fired when the job finishes successfully.
    
    Frontend handler: Closes SSE connection, updates UI to complete state.
    """
    
    event: Literal["job_complete"] = "job_complete"
    data: JobCompleteData


class JobErrorData(BaseModel):
    """Data payload for job errors."""
    
    error_code: str = Field(default="UNKNOWN_ERROR")
    detail: str
    recoverable: bool = False
    retry_after_seconds: int | None = None


class JobErrorEvent(BaseEvent):
    """
    Fired when the job encounters a fatal error.
    
    Frontend handler: Shows error state, offers retry option.
    """
    
    event: Literal["job_error"] = "job_error"
    data: JobErrorData


# Union Type for Type Safety

DiscriminatorEvent = (
    AgentActivityEvent
    | ThinkingEvent
    | ToolUsageEvent
    | ReportReadyEvent
    | JobProgressEvent
    | JobCompleteEvent
    | JobErrorEvent
)

# Event type string literals for validation
EVENT_TYPES = Literal[
    "agent_activity",
    "thinking",
    "tool_usage",
    "report_ready",
    "job_progress",
    "job_complete",
    "job_error",
]

# Mapping for dynamic event creation
EVENT_CLASS_MAP: dict[str, type[BaseEvent]] = {
    "agent_activity": AgentActivityEvent,
    "thinking": ThinkingEvent,
    "tool_usage": ToolUsageEvent,
    "report_ready": ReportReadyEvent,
    "job_progress": JobProgressEvent,
    "job_complete": JobCompleteEvent,
    "job_error": JobErrorEvent,
}