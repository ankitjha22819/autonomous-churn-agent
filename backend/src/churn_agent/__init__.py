"""
Churn Agent - Autonomous Churn Prediction Agent.

A CrewAI-powered analysis system that predicts customer churn
and provides actionable retention strategies.

"""

__version__ = "0.1.0"
__author__ = "Ankit Jha"

from churn_agent.crew import ChurnAnalysisCrew, create_churn_crew

__all__ = [
    "__version__",
    "ChurnAnalysisCrew",
    "create_churn_crew",
]