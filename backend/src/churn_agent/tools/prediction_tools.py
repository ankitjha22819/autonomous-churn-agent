"""
Prediction Tools.

Tools for calculating churn risk scores and segmenting customers
by risk level using ML models and heuristics.
"""

from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from churn_agent.core.logging import get_logger

logger = get_logger(__name__)


# Tool Input Schemas

class ChurnScoreInput(BaseModel):
    """Input schema for ChurnScoreTool."""
    
    customer_data: dict[str, Any] = Field(
        ...,
        description="Customer data dictionary with engagement metrics"
    )


class RiskSegmentationInput(BaseModel):
    """Input schema for RiskSegmentationTool."""
    
    customers: list[dict[str, Any]] = Field(
        ...,
        description="List of customer records with churn scores"
    )
    high_risk_threshold: float = Field(
        default=70.0,
        ge=0,
        le=100,
        description="Score threshold for high risk classification"
    )
    critical_risk_threshold: float = Field(
        default=85.0,
        ge=0,
        le=100,
        description="Score threshold for critical risk classification"
    )


# Churn Score Tool

class ChurnScoreTool(BaseTool):
    """
    Calculates churn risk score for a customer.
    
    Uses a combination of engagement metrics, usage patterns, and
    historical factors to predict churn probability.
    """
    
    name: str = "churn_score_calculator"
    description: str = (
        "Calculates a churn risk score (0-100) for a customer based on their "
        "engagement data, usage patterns, and historical factors. Higher scores "
        "indicate higher risk of churning. Also returns confidence level and "
        "top contributing factors."
    )
    args_schema: Type[BaseModel] = ChurnScoreInput
    
    def _run(self, customer_data: dict[str, Any]) -> dict[str, Any]:
        """
        Calculate churn score for a customer.
        
        In production, this would use a trained ML model.
        Currently uses a weighted heuristic approach.
        """
        customer_id = customer_data.get("customer_id", "unknown")
        
        logger.info("Calculating churn score", customer_id=customer_id)
        
        # Extract metrics (with defaults)
        days_since_login = customer_data.get("days_since_last_login", 0)
        login_count = customer_data.get("login_count_30d", 0)
        feature_adoption = customer_data.get("feature_adoption_score", 50)
        support_tickets = customer_data.get("support_tickets_30d", 0)
        nps_score = customer_data.get("nps_score")
        months_customer = customer_data.get("months_as_customer", 0)
        
        # Calculate component scores
        factors = []
        score_components = []
        
        # Login recency (0-25 points)
        if days_since_login > 14:
            login_score = min(25, (days_since_login - 14) * 1.5)
            factors.append(f"No login in {days_since_login} days")
        else:
            login_score = 0
        score_components.append(("login_recency", login_score, 25))
        
        # Login frequency (0-20 points)
        if login_count < 5:
            freq_score = (5 - login_count) * 4
            factors.append(f"Low login frequency ({login_count}/month)")
        else:
            freq_score = 0
        score_components.append(("login_frequency", freq_score, 20))
        
        # Feature adoption (0-25 points)
        adoption_score = max(0, (50 - feature_adoption) * 0.5)
        if feature_adoption < 40:
            factors.append(f"Low feature adoption ({feature_adoption}%)")
        score_components.append(("feature_adoption", adoption_score, 25))
        
        # Support tickets (0-15 points)
        ticket_score = min(15, support_tickets * 3)
        if support_tickets > 2:
            factors.append(f"High support volume ({support_tickets} tickets)")
        score_components.append(("support_tickets", ticket_score, 15))
        
        # NPS score (0-15 points)
        if nps_score is not None and nps_score < 7:
            nps_risk = (7 - nps_score) * 2.5
            factors.append(f"Low NPS score ({nps_score})")
        else:
            nps_risk = 0
        score_components.append(("nps_score", nps_risk, 15))
        
        # Calculate total score
        total_score = sum(c[1] for c in score_components)
        total_score = min(100, max(0, total_score))
        
        # Determine risk level
        if total_score >= 85:
            risk_level = "critical"
        elif total_score >= 70:
            risk_level = "high"
        elif total_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Calculate confidence based on data completeness
        data_completeness = sum(1 for k in [
            "days_since_last_login", "login_count_30d", "feature_adoption_score",
            "support_tickets_30d", "nps_score", "months_as_customer"
        ] if k in customer_data) / 6
        
        confidence = 0.6 + (data_completeness * 0.35)
        
        return {
            "success": True,
            "customer_id": customer_id,
            "churn_score": round(total_score, 2),
            "risk_level": risk_level,
            "confidence": round(confidence, 2),
            "top_factors": factors[:3] if factors else ["No significant risk factors"],
            "score_breakdown": {
                name: {"score": round(score, 2), "max": max_score}
                for name, score, max_score in score_components
            },
        }


# Risk Segmentation Tool

class RiskSegmentationTool(BaseTool):
    """
    Segments a list of customers by churn risk level.
    
    Takes customers with churn scores and groups them into
    risk categories for prioritized action.
    """
    
    name: str = "risk_segmenter"
    description: str = (
        "Segments customers into risk categories (critical, high, medium, low) "
        "based on their churn scores. Returns grouped lists and summary statistics "
        "for each segment. Useful for prioritizing retention efforts."
    )
    args_schema: Type[BaseModel] = RiskSegmentationInput
    
    def _run(
        self,
        customers: list[dict[str, Any]],
        high_risk_threshold: float = 70.0,
        critical_risk_threshold: float = 85.0,
    ) -> dict[str, Any]:
        """
        Segment customers by risk level.
        """
        logger.info(
            "Segmenting customers by risk",
            customer_count=len(customers),
            high_threshold=high_risk_threshold,
            critical_threshold=critical_risk_threshold,
        )
        
        segments = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }
        
        total_mrr_at_risk = 0
        
        for customer in customers:
            score = customer.get("churn_score", 0)
            mrr = customer.get("mrr", 0)
            
            if score >= critical_risk_threshold:
                segments["critical"].append(customer)
                total_mrr_at_risk += mrr
            elif score >= high_risk_threshold:
                segments["high"].append(customer)
                total_mrr_at_risk += mrr * 0.7  # Weighted risk
            elif score >= 40:
                segments["medium"].append(customer)
                total_mrr_at_risk += mrr * 0.3
            else:
                segments["low"].append(customer)
        
        return {
            "success": True,
            "total_customers": len(customers),
            "segments": {
                name: {
                    "count": len(custs),
                    "percentage": round(len(custs) / len(customers) * 100, 1) if customers else 0,
                    "customer_ids": [c.get("customer_id") for c in custs],
                    "avg_score": round(
                        sum(c.get("churn_score", 0) for c in custs) / len(custs), 2
                    ) if custs else 0,
                }
                for name, custs in segments.items()
            },
            "mrr_at_risk": round(total_mrr_at_risk, 2),
            "action_priority": [
                c.get("customer_id")
                for c in sorted(
                    segments["critical"] + segments["high"],
                    key=lambda x: x.get("churn_score", 0),
                    reverse=True
                )[:10]
            ],
        }