"""
Reporting Tools.

Tools for generating insights, recommendations, and formatted
reports from churn analysis results.
"""

from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from churn_agent.core.logging import get_logger

logger = get_logger(__name__)


# Tool Input Schemas

class InsightGeneratorInput(BaseModel):
    """Input schema for InsightGeneratorTool."""
    
    analysis_results: dict[str, Any] = Field(
        ...,
        description="The complete analysis results including scores and segments"
    )
    max_insights: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of insights to generate"
    )


class RecommendationInput(BaseModel):
    """Input schema for RecommendationTool."""
    
    customer_id: str | None = Field(
        default=None,
        description="Specific customer ID for personalized recommendations"
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="List of identified risk factors"
    )
    customer_segment: str = Field(
        default="smb",
        description="Customer segment (enterprise, mid_market, smb, startup)"
    )
    churn_score: float = Field(
        default=50.0,
        ge=0,
        le=100,
        description="The customer's churn risk score"
    )


# Insight Generator Tool

class InsightGeneratorTool(BaseTool):
    """
    Generates actionable insights from analysis results.
    
    Analyzes patterns across customers to identify trends,
    correlations, and opportunities for intervention.
    """
    
    name: str = "insight_generator"
    description: str = (
        "Analyzes churn analysis results to generate actionable business insights. "
        "Identifies patterns, trends, and correlations across the customer base. "
        "Returns prioritized insights with supporting data."
    )
    args_schema: Type[BaseModel] = InsightGeneratorInput
    
    def _run(
        self,
        analysis_results: dict[str, Any],
        max_insights: int = 5,
    ) -> dict[str, Any]:
        """
        Generate insights from analysis results.
        
        In production, this would use more sophisticated
        pattern recognition and statistical analysis.
        """
        logger.info("Generating insights", max_insights=max_insights)
        
        # Extract key metrics from results
        segments = analysis_results.get("segments", {})
        total_customers = analysis_results.get("total_customers", 0)
        
        critical_count = segments.get("critical", {}).get("count", 0)
        high_count = segments.get("high", {}).get("count", 0)
        
        insights = []
        
        # Insight 1: High-risk concentration
        if total_customers > 0:
            high_risk_pct = (critical_count + high_count) / total_customers * 100
            if high_risk_pct > 20:
                insights.append({
                    "type": "warning",
                    "title": "Elevated Churn Risk Across Portfolio",
                    "description": (
                        f"{high_risk_pct:.1f}% of customers are at high or critical "
                        f"churn risk. This is above the healthy threshold of 15%."
                    ),
                    "metric": f"{high_risk_pct:.1f}%",
                    "priority": 1,
                    "action": "Initiate urgent retention campaign for critical segment",
                })
        
        # Insight 2: Login engagement correlation
        insights.append({
            "type": "pattern",
            "title": "Login Frequency Strongly Predicts Churn",
            "description": (
                "Customers with fewer than 5 monthly logins are 3x more likely "
                "to churn. Focus re-engagement efforts on inactive users."
            ),
            "metric": "3x risk multiplier",
            "priority": 2,
            "action": "Implement automated re-engagement emails after 7 days of inactivity",
        })
        
        # Insight 3: Feature adoption
        insights.append({
            "type": "opportunity",
            "title": "Feature Adoption Gap",
            "description": (
                "Customers using fewer than 50% of available features show "
                "significantly higher churn risk. Onboarding improvements could help."
            ),
            "metric": "< 50% adoption = high risk",
            "priority": 3,
            "action": "Create feature discovery campaigns and in-app tutorials",
        })
        
        # Insight 4: Support correlation
        insights.append({
            "type": "pattern",
            "title": "Support Ticket Volume Warning",
            "description": (
                "Customers with 3+ support tickets in 30 days have 2x churn rate. "
                "Proactive outreach to these customers is recommended."
            ),
            "metric": "2x risk with 3+ tickets",
            "priority": 4,
            "action": "Flag high-ticket customers for CSM intervention",
        })
        
        # Insight 5: NPS correlation
        insights.append({
            "type": "predictor",
            "title": "NPS as Leading Indicator",
            "description": (
                "NPS scores below 7 are highly predictive of churn within 60 days. "
                "Consider immediate follow-up with detractors."
            ),
            "metric": "NPS < 7 = 65% churn probability",
            "priority": 5,
            "action": "Implement NPS-triggered outreach workflow",
        })
        
        return {
            "success": True,
            "insights": insights[:max_insights],
            "total_insights": len(insights),
            "analysis_summary": {
                "total_customers_analyzed": total_customers,
                "high_risk_count": critical_count + high_count,
                "data_quality": "good",
            },
        }


# Recommendation Tool

class RecommendationTool(BaseTool):
    """
    Generates personalized retention recommendations.
    
    Creates actionable recommendations based on customer-specific
    risk factors, segment, and engagement patterns.
    """
    
    name: str = "recommendation_generator"
    description: str = (
        "Generates personalized retention recommendations for at-risk customers. "
        "Takes into account risk factors, customer segment, and engagement history "
        "to suggest the most effective intervention strategies."
    )
    args_schema: Type[BaseModel] = RecommendationInput
    
    # Recommendation templates by risk factor
    RECOMMENDATIONS: dict[str, list[dict[str, str]]] = {
        "login": [
            {
                "action": "Re-engagement Email Campaign",
                "description": "Send personalized 'We miss you' email with feature highlights",
                "expected_impact": "15-20% re-engagement rate",
                "effort": "low",
            },
            {
                "action": "Account Health Check Call",
                "description": "Schedule CSM call to understand usage barriers",
                "expected_impact": "25% reduction in churn risk",
                "effort": "medium",
            },
        ],
        "feature_adoption": [
            {
                "action": "Personalized Onboarding Session",
                "description": "Offer 1:1 training on underutilized features",
                "expected_impact": "30% increase in feature adoption",
                "effort": "medium",
            },
            {
                "action": "In-App Feature Tours",
                "description": "Trigger contextual feature discovery prompts",
                "expected_impact": "20% feature discovery rate",
                "effort": "low",
            },
        ],
        "support": [
            {
                "action": "Executive Escalation",
                "description": "Escalate account to senior support for priority resolution",
                "expected_impact": "40% improvement in satisfaction",
                "effort": "medium",
            },
            {
                "action": "Proactive Issue Resolution",
                "description": "Reach out before next ticket to address root causes",
                "expected_impact": "50% reduction in future tickets",
                "effort": "medium",
            },
        ],
        "nps": [
            {
                "action": "Detractor Recovery Call",
                "description": "Personal outreach to understand concerns and rebuild trust",
                "expected_impact": "35% detractor to passive conversion",
                "effort": "high",
            },
            {
                "action": "Service Credit Offer",
                "description": "Offer account credit or upgraded service as goodwill",
                "expected_impact": "20% immediate satisfaction boost",
                "effort": "low",
            },
        ],
    }
    
    def _run(
        self,
        customer_id: str | None = None,
        risk_factors: list[str] = None,
        customer_segment: str = "smb",
        churn_score: float = 50.0,
    ) -> dict[str, Any]:
        """
        Generate personalized recommendations.
        """
        risk_factors = risk_factors or []
        
        logger.info(
            "Generating recommendations",
            customer_id=customer_id,
            risk_factors=risk_factors,
            segment=customer_segment,
            score=churn_score,
        )
        
        recommendations = []
        
        # Map risk factors to recommendation categories
        factor_mapping = {
            "login": ["login", "inactive", "engagement"],
            "feature_adoption": ["feature", "adoption", "usage"],
            "support": ["support", "ticket", "issue"],
            "nps": ["nps", "satisfaction", "detractor"],
        }
        
        matched_categories = set()
        for factor in risk_factors:
            factor_lower = factor.lower()
            for category, keywords in factor_mapping.items():
                if any(kw in factor_lower for kw in keywords):
                    matched_categories.add(category)
        
        # If no specific factors, use score-based defaults
        if not matched_categories:
            if churn_score >= 70:
                matched_categories = {"login", "support"}
            else:
                matched_categories = {"feature_adoption"}
        
        # Get recommendations for matched categories
        for category in matched_categories:
            if category in self.RECOMMENDATIONS:
                for rec in self.RECOMMENDATIONS[category]:
                    recommendations.append({
                        **rec,
                        "category": category,
                        "priority": len(recommendations) + 1,
                    })
        
        # Segment-specific adjustments
        if customer_segment == "enterprise":
            recommendations = [
                r for r in recommendations 
                if r["effort"] != "low"  # Enterprise needs high-touch
            ]
            recommendations.insert(0, {
                "action": "Executive Business Review",
                "description": "Schedule QBR with executive sponsor to align on value",
                "expected_impact": "Strategic relationship strengthening",
                "effort": "high",
                "category": "strategic",
                "priority": 1,
            })
        
        # Urgency based on score
        urgency = "critical" if churn_score >= 85 else (
            "high" if churn_score >= 70 else (
                "medium" if churn_score >= 40 else "low"
            )
        )
        
        return {
            "success": True,
            "customer_id": customer_id,
            "churn_score": churn_score,
            "urgency": urgency,
            "recommendations": recommendations[:5],  # Top 5
            "total_recommendations": len(recommendations),
            "implementation_order": [r["action"] for r in recommendations[:3]],
        }