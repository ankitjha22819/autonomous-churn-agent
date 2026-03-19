"""
Customer Data Tools.

Tools for fetching, analyzing, and transforming customer data
for the churn analysis pipeline.
"""

from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from churn_agent.core.logging import get_logger

logger = get_logger(__name__)


# Tool Input Schemas

class CustomerDataInput(BaseModel):
    """Input schema for CustomerDataTool."""
    
    customer_ids: list[str] | None = Field(
        default=None,
        description="List of specific customer IDs to fetch. If None, fetches all."
    )
    segment: str | None = Field(
        default=None,
        description="Filter by customer segment (enterprise, mid_market, smb, startup)"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of customers to return"
    )


class EngagementAnalysisInput(BaseModel):
    """Input schema for EngagementAnalysisTool."""
    
    customer_id: str = Field(
        ...,
        description="The customer ID to analyze engagement for"
    )
    time_period_days: int = Field(
        default=30,
        ge=7,
        le=365,
        description="Number of days to analyze"
    )


# Customer Data Tool

class CustomerDataTool(BaseTool):
    """
    Fetches customer data from the data source.
    
    Use this tool to retrieve customer records for analysis.
    Returns customer profiles with engagement metrics, subscription info,
    and historical data.
    """
    
    name: str = "customer_data_fetcher"
    description: str = (
        "Fetches customer data including engagement metrics, subscription details, "
        "and historical information. Use this to get the raw data needed for "
        "churn analysis. Can filter by customer IDs or segment."
    )
    args_schema: Type[BaseModel] = CustomerDataInput
    
    def _run(
        self,
        customer_ids: list[str] | None = None,
        segment: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Execute the customer data fetch.
        
        In production, this would query your data warehouse or CRM.
        """
        logger.info(
            "Fetching customer data",
            customer_ids=customer_ids,
            segment=segment,
            limit=limit,
        )
        
        # TODO: Replace with actual data source query
        # This is a mock implementation
        mock_customers = [
            {
                "customer_id": f"CUST-{i:04d}",
                "company_name": f"Company {i}",
                "segment": segment or "smb",
                "mrr": 500 + (i * 50),
                "days_since_last_login": i % 30,
                "login_count_30d": max(1, 30 - i),
                "feature_adoption_score": 80 - (i * 2),
                "support_tickets_30d": i % 5,
                "months_as_customer": 12 + i,
                "nps_score": 8 - (i % 4),
            }
            for i in range(min(limit, 10))
        ]
        
        if customer_ids:
            mock_customers = [
                c for c in mock_customers 
                if c["customer_id"] in customer_ids
            ]
        
        return {
            "success": True,
            "count": len(mock_customers),
            "customers": mock_customers,
        }


# Engagement Analysis Tool

class EngagementAnalysisTool(BaseTool):
    """
    Analyzes customer engagement patterns over time.
    
    Use this tool to get detailed engagement analytics for a specific
    customer, including usage trends, feature adoption, and activity patterns.
    """
    
    name: str = "engagement_analyzer"
    description: str = (
        "Analyzes a customer's engagement patterns including login frequency, "
        "feature usage, support interactions, and activity trends. "
        "Returns engagement score and trend analysis."
    )
    args_schema: Type[BaseModel] = EngagementAnalysisInput
    
    def _run(
        self,
        customer_id: str,
        time_period_days: int = 30,
    ) -> dict[str, Any]:
        """
        Execute engagement analysis for a customer.
        """
        logger.info(
            "Analyzing engagement",
            customer_id=customer_id,
            time_period_days=time_period_days,
        )
        
        # TODO: Replace with actual engagement analytics
        # This is a mock implementation
        return {
            "success": True,
            "customer_id": customer_id,
            "time_period_days": time_period_days,
            "engagement_score": 72.5,
            "trend": "declining",
            "trend_percentage": -15.3,
            "metrics": {
                "avg_daily_logins": 0.8,
                "features_used": 5,
                "total_features": 12,
                "support_tickets": 3,
                "last_active": "2024-01-15",
            },
            "risk_indicators": [
                "Login frequency decreased 40% from previous period",
                "Key features unused in last 2 weeks",
                "Multiple support tickets about same issue",
            ],
        }