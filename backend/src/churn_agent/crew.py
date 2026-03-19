"""
CrewAI Crew Definition for Churn Analysis.

This module defines the crew of AI agents that work together
to analyze customer churn risk and generate retention strategies.
"""

from pathlib import Path
from typing import Any, Callable

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from churn_agent.core.config import get_settings
from churn_agent.core.logging import get_logger
from churn_agent.tools import (
    CustomerDataTool,
    EngagementAnalysisTool,
    ChurnScoreTool,
    RiskSegmentationTool,
    InsightGeneratorTool,
    RecommendationTool,
)

logger = get_logger(__name__)
settings = get_settings()


# Event Callback for SSE Integration


class CrewEventHandler:
    """
    Handles events from CrewAI execution for SSE streaming.

    This bridges CrewAI's internal events to our EventManager
    for real-time frontend updates.
    """

    def __init__(self, publish_callback: Callable[[dict], Any] | None = None):
        """
        Initialize the event handler.

        Args:
            publish_callback: Async function to publish events.
                              Signature: async def callback(event: dict) -> None
        """
        self.publish_callback = publish_callback
        self.event_counter = 0

    def _get_event_id(self) -> str:
        """Generate unique event ID."""
        self.event_counter += 1
        return f"crew-{self.event_counter}"

    async def on_agent_start(self, agent_name: str, task_description: str) -> None:
        """Called when an agent starts working on a task."""
        if self.publish_callback:
            await self.publish_callback(
                {
                    "event": "agent_activity",
                    "event_id": self._get_event_id(),
                    "data": {
                        "agent": agent_name,
                        "message": f"Starting: {task_description[:100]}...",
                        "status": "thinking",
                    },
                }
            )

    async def on_agent_thinking(self, agent_name: str, thought: str) -> None:
        """Called when an agent is reasoning."""
        if self.publish_callback:
            await self.publish_callback(
                {
                    "event": "thinking",
                    "event_id": self._get_event_id(),
                    "data": {
                        "agent": agent_name,
                        "thought": thought[:500],
                        "step": self.event_counter,
                    },
                }
            )

    async def on_tool_use(
        self,
        agent_name: str,
        tool_name: str,
        tool_input: dict,
        status: str = "started",
        result: Any = None,
    ) -> None:
        """Called when an agent uses a tool."""
        if self.publish_callback:
            await self.publish_callback(
                {
                    "event": "tool_usage",
                    "event_id": self._get_event_id(),
                    "data": {
                        "agent": agent_name,
                        "tool_name": tool_name,
                        "tool_input": tool_input,
                        "status": status,
                        "result": str(result)[:200] if result else None,
                    },
                }
            )

    async def on_agent_complete(self, agent_name: str, output: str) -> None:
        """Called when an agent completes a task."""
        if self.publish_callback:
            await self.publish_callback(
                {
                    "event": "agent_activity",
                    "event_id": self._get_event_id(),
                    "data": {
                        "agent": agent_name,
                        "message": "Task completed",
                        "status": "completed",
                    },
                }
            )

    async def on_progress(
        self,
        current_step: int,
        total_steps: int,
        step_name: str,
    ) -> None:
        """Called to report overall progress."""
        if self.publish_callback:
            await self.publish_callback(
                {
                    "event": "job_progress",
                    "event_id": self._get_event_id(),
                    "data": {
                        "current_step": current_step,
                        "total_steps": total_steps,
                        "step_name": step_name,
                        "percentage": (current_step / total_steps) * 100,
                    },
                }
            )


# Crew Definition


@CrewBase
class ChurnAnalysisCrew:
    """
    Crew for autonomous churn analysis.

    This crew consists of specialized agents that work together
    to analyze customer data, assess risk, and generate strategies.
    """

    # Config file paths
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, event_handler: CrewEventHandler | None = None):
        """
        Initialize the crew.

        Args:
            event_handler: Optional handler for SSE event publishing
        """
        self.event_handler = event_handler or CrewEventHandler()
        self._load_configs()

    def _load_configs(self) -> None:
        """Load agent and task configurations from YAML files."""
        # Resolve paths relative to backend root
        backend_root = Path(__file__).parent.parent.parent

        agents_path = backend_root / self.agents_config
        tasks_path = backend_root / self.tasks_config

        with open(agents_path) as f:
            self.agents_config_data = yaml.safe_load(f)

        with open(tasks_path) as f:
            self.tasks_config_data = yaml.safe_load(f)

        logger.info(
            "Loaded crew configurations",
            agents=list(self.agents_config_data.keys()),
            tasks=list(self.tasks_config_data.keys()),
        )

    
    # Agent Definitions
    

    @agent
    def data_analyst(self) -> Agent:
        """Data Analyst agent for customer data analysis."""
        config = self.agents_config_data["data_analyst"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config.get("verbose", settings.crew_verbose),
            allow_delegation=config.get("allow_delegation", False),
            max_iter=config.get("max_iter", 5),
            tools=[
                CustomerDataTool(),
                EngagementAnalysisTool(),
            ],
        )

    @agent
    def risk_assessor(self) -> Agent:
        """Risk Assessor agent for churn scoring."""
        config = self.agents_config_data["risk_assessor"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config.get("verbose", settings.crew_verbose),
            allow_delegation=config.get("allow_delegation", False),
            max_iter=config.get("max_iter", 5),
            tools=[
                ChurnScoreTool(),
                RiskSegmentationTool(),
            ],
        )

    @agent
    def strategy_expert(self) -> Agent:
        """Strategy Expert agent for retention recommendations."""
        config = self.agents_config_data["strategy_expert"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config.get("verbose", settings.crew_verbose),
            allow_delegation=config.get("allow_delegation", True),
            max_iter=config.get("max_iter", 5),
            tools=[
                InsightGeneratorTool(),
                RecommendationTool(),
            ],
        )

    @agent
    def report_compiler(self) -> Agent:
        """Report Compiler agent for executive summaries."""
        config = self.agents_config_data["report_compiler"]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            verbose=config.get("verbose", settings.crew_verbose),
            allow_delegation=config.get("allow_delegation", False),
            max_iter=config.get("max_iter", 3),
            tools=[],  # Report compiler synthesizes, doesn't need tools
        )

    
    # Task Definitions
    

    @task
    def analyze_customer_data(self) -> Task:
        """Task: Analyze customer engagement data."""
        config = self.tasks_config_data["analyze_customer_data"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.data_analyst(),
        )

    @task
    def calculate_risk_scores(self) -> Task:
        """Task: Calculate churn risk scores."""
        config = self.tasks_config_data["calculate_risk_scores"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.risk_assessor(),
            context=[self.analyze_customer_data()],
        )

    @task
    def generate_retention_strategies(self) -> Task:
        """Task: Generate retention strategies."""
        config = self.tasks_config_data["generate_retention_strategies"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.strategy_expert(),
            context=[self.calculate_risk_scores()],
        )

    @task
    def compile_executive_report(self) -> Task:
        """Task: Compile executive report."""
        config = self.tasks_config_data["compile_executive_report"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.report_compiler(),
            context=[
                self.analyze_customer_data(),
                self.calculate_risk_scores(),
                self.generate_retention_strategies(),
            ],
        )

    
    # Crew Definition
    

    @crew
    def crew(self) -> Crew:
        """Create the churn analysis crew."""
        return Crew(
            agents=[
                self.data_analyst(),
                self.risk_assessor(),
                self.strategy_expert(),
                self.report_compiler(),
            ],
            tasks=[
                self.analyze_customer_data(),
                self.calculate_risk_scores(),
                self.generate_retention_strategies(),
                self.compile_executive_report(),
            ],
            process=Process.sequential,
            verbose=settings.crew_verbose,
            memory=settings.crew_memory,
        )

    
    # Execution
    

    def kickoff(self, inputs: dict[str, Any]) -> Any:
        """
        Start the crew execution.

        Args:
            inputs: Dictionary with input variables for tasks.
                    Must include 'customer_data' key.

        Returns:
            The final crew output (executive report).
        """
        logger.info("Starting churn analysis crew", input_keys=list(inputs.keys()))

        crew_instance = self.crew()
        result = crew_instance.kickoff(inputs=inputs)

        logger.info("Crew execution completed")
        return result

    async def kickoff_async(self, inputs: dict[str, Any]) -> Any:
        """
        Async version of kickoff for use in FastAPI background tasks.

        Args:
            inputs: Dictionary with input variables for tasks.

        Returns:
            The final crew output.
        """
        logger.info("Starting async churn analysis", input_keys=list(inputs.keys()))

        crew_instance = self.crew()
        result = await crew_instance.kickoff_async(inputs=inputs)

        logger.info("Async crew execution completed")
        return result


# Factory Function


def create_churn_crew(
    publish_callback: Callable[[dict], Any] | None = None,
) -> ChurnAnalysisCrew:
    """
    Factory function to create a configured ChurnAnalysisCrew.

    Args:
        publish_callback: Optional async callback for SSE events

    Returns:
        Configured ChurnAnalysisCrew instance
    """
    event_handler = CrewEventHandler(publish_callback)
    return ChurnAnalysisCrew(event_handler=event_handler)
