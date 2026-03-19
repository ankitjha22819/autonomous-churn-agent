"""Pydantic schemas for request/response validation and SSE events."""

from churn_agent.schemas.events import (
    # Base
    BaseEvent,
    # Event Types
    AgentActivityEvent,
    AgentActivityData,
    ThinkingEvent,
    ThinkingData,
    ToolUsageEvent,
    ToolUsageData,
    ReportReadyEvent,
    ReportReadyData,
    ChurnPrediction,
    JobProgressEvent,
    JobProgressData,
    JobCompleteEvent,
    JobCompleteData,
    JobErrorEvent,
    JobErrorData,
    # Union & Utilities
    DiscriminatorEvent,
    EVENT_TYPES,
    EVENT_CLASS_MAP,
)

from churn_agent.schemas.customer import (
    # Enums
    CustomerSegment,
    SubscriptionTier,
    RiskLevel,
    JobStatus,
    # Customer Models
    CustomerRow,
    CustomerBatch,
    # Request/Response
    AnalysisConfig,
    AnalysisRequest,
    JobCreatedResponse,
    JobStatusResponse,
)

__all__ = [
    # Events
    "BaseEvent",
    "AgentActivityEvent",
    "AgentActivityData",
    "ThinkingEvent",
    "ThinkingData",
    "ToolUsageEvent",
    "ToolUsageData",
    "ReportReadyEvent",
    "ReportReadyData",
    "ChurnPrediction",
    "JobProgressEvent",
    "JobProgressData",
    "JobCompleteEvent",
    "JobCompleteData",
    "JobErrorEvent",
    "JobErrorData",
    "DiscriminatorEvent",
    "EVENT_TYPES",
    "EVENT_CLASS_MAP",
    # Enums
    "CustomerSegment",
    "SubscriptionTier",
    "RiskLevel",
    "JobStatus",
    # Customer
    "CustomerRow",
    "CustomerBatch",
    # Request/Response
    "AnalysisConfig",
    "AnalysisRequest",
    "JobCreatedResponse",
    "JobStatusResponse",
]