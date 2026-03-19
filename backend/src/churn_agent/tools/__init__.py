"""
Custom Tools for Churn Analysis Agents.

These tools extend CrewAI's capabilities with domain-specific
functionality for customer data analysis and churn prediction.
"""

from churn_agent.tools.customer_tools import (
    CustomerDataTool,
    EngagementAnalysisTool,
)
from churn_agent.tools.prediction_tools import (
    ChurnScoreTool,
    RiskSegmentationTool,
)
from churn_agent.tools.reporting_tools import (
    InsightGeneratorTool,
    RecommendationTool,
)

__all__ = [
    # Customer Tools
    "CustomerDataTool",
    "EngagementAnalysisTool",
    # Prediction Tools
    "ChurnScoreTool",
    "RiskSegmentationTool",
    # Reporting Tools
    "InsightGeneratorTool",
    "RecommendationTool",
]