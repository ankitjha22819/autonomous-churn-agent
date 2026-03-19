"""
Customer and Analysis Request Schemas.

Defines the data structures for incoming analysis requests
and customer data that will be processed by the CrewAI agents.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# Enums

class CustomerSegment(str, Enum):
    """Customer segmentation categories."""
    
    ENTERPRISE = "enterprise"
    MID_MARKET = "mid_market"
    SMB = "smb"
    STARTUP = "startup"
    INDIVIDUAL = "individual"


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""
    
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class RiskLevel(str, Enum):
    """Churn risk levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Customer Data Models

class CustomerRow(BaseModel):
    """
    Single customer record for analysis.
    
    This represents the data that would typically come from a CRM,
    data warehouse, or uploaded CSV file.
    """
    
    customer_id: str = Field(..., min_length=1, max_length=100)
    company_name: str | None = None
    email: str | None = None
    
    # Subscription info
    segment: CustomerSegment = CustomerSegment.SMB
    subscription_tier: SubscriptionTier = SubscriptionTier.BASIC
    mrr: Annotated[float, Field(ge=0, description="Monthly Recurring Revenue")]
    
    # Engagement metrics
    days_since_last_login: int = Field(ge=0)
    login_count_30d: int = Field(ge=0, description="Logins in last 30 days")
    feature_adoption_score: Annotated[float, Field(ge=0, le=100)]
    support_tickets_30d: int = Field(ge=0, description="Support tickets in last 30 days")
    nps_score: Annotated[int | None, Field(ge=-100, le=100)] = None
    
    # Contract info
    contract_start_date: datetime | None = None
    contract_end_date: datetime | None = None
    months_as_customer: int = Field(ge=0)
    
    # Historical
    previous_churn_flag: bool = False
    expansion_revenue_30d: float = Field(ge=0, default=0)
    contraction_revenue_30d: float = Field(ge=0, default=0)
    
    # Additional context
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None and "@" not in v:
            raise ValueError("Invalid email format")
        return v


class CustomerBatch(BaseModel):
    """Batch of customers for bulk analysis."""
    
    customers: list[CustomerRow] = Field(..., min_length=1, max_length=10000)
    batch_id: str = Field(default_factory=lambda: str(uuid4()))
    
    @property
    def count(self) -> int:
        return len(self.customers)


# Analysis Request Models

class AnalysisConfig(BaseModel):
    """Configuration options for the analysis job."""
    
    # Analysis depth
    include_recommendations: bool = True
    include_insights: bool = True
    include_individual_predictions: bool = True
    
    # Thresholds
    high_risk_threshold: float = Field(default=70.0, ge=0, le=100)
    critical_risk_threshold: float = Field(default=85.0, ge=0, le=100)
    
    # Focus areas
    focus_segments: list[CustomerSegment] | None = None
    focus_tiers: list[SubscriptionTier] | None = None
    
    # Output preferences
    max_recommendations: int = Field(default=10, ge=1, le=50)
    max_insights: int = Field(default=10, ge=1, le=50)


class AnalysisRequest(BaseModel):
    """
    Request payload for initiating a churn analysis job.
    
    Sent to POST /api/v1/analysis/jobs
    """
    
    # Customer data (one of these is required)
    customers: list[CustomerRow] | None = Field(
        default=None, 
        description="Inline customer data"
    )
    data_source_id: str | None = Field(
        default=None,
        description="Reference to pre-uploaded data source"
    )
    
    # Configuration
    config: AnalysisConfig = Field(default_factory=AnalysisConfig)
    
    # Metadata
    requested_by: str | None = Field(default=None, description="User ID or email")
    callback_url: str | None = Field(default=None, description="Webhook URL for completion")
    tags: list[str] = Field(default_factory=list, max_length=10)
    
    @field_validator("customers", "data_source_id")
    @classmethod
    def validate_data_source(cls, v: Any, info: Any) -> Any:
        return v
    
    def model_post_init(self, __context: Any) -> None:
        """Ensure at least one data source is provided."""
        if not self.customers and not self.data_source_id:
            raise ValueError("Either 'customers' or 'data_source_id' must be provided")


# Job Response Models

class JobStatus(str, Enum):
    """Analysis job status."""
    
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobCreatedResponse(BaseModel):
    """Response returned when a job is successfully created."""
    
    job_id: UUID
    status: JobStatus = JobStatus.PENDING
    events_url: str = Field(..., description="SSE endpoint URL for this job")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_duration_seconds: int | None = None
    
    class Config:
        json_encoders = {UUID: str}


class JobStatusResponse(BaseModel):
    """Response for job status queries."""
    
    job_id: UUID
    status: JobStatus
    progress: float | None = Field(default=None, ge=0, le=100)
    current_step: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    
    class Config:
        json_encoders = {UUID: str}