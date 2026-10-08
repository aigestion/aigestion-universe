"""
LangGraph Integration for AIG Orchestration
Graph-based multi-agent workflow orchestration replacing custom orchestrator.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


class AgentRole(StrEnum):
    """Standard agent roles in AIG."""
    ORCHESTRATOR = "orchestrator"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ANDROID = "android"
    OBSERVABILITY = "observability"
    DEPLOY = "deploy"
    CODE_REVIEW = "code_review"
    TEST = "test"


class TaskStatus(StrEnum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Task:
    """Task definition for orchestration."""
    id: str
    name: str
    role: AgentRole
    description: str
    input_data: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: dict | None = None
    error: str | None = None
    retries: int = 0
    max_retries: int = 3
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: str | None = None
    completed_at: str | None = None


class OrchestrationState(TypedDict):
    """State for LangGraph orchestration."""
    messages: Annotated[list[BaseMessage], add_messages]
    tasks: dict[str, Task]
    current_task_id: str | None
    context: dict[str, Any]
    results: dict[str, Any]
    errors: list[str]


@dataclass
class AgentConfig:
    """Configuration for an agent in the graph."""
    role: AgentRole
    name: str
    system_prompt: str
    tools: list[BaseTool] = field(default_factory=list)
    model: str = "gpt-4o-mini"
    temperature: float = 0.7


class LangGraphOrchestrator:
    """
    LangGraph-based orchestrator for AIG multi-agent workflows.
    Replaces custom orchestrator with graph-based execution, checkpoints, and streaming.
    """

    def __init__(self, agents: dict[AgentRole, AgentConfig], checkpointer=None):
        self.agents = agents
        self.checkpointer = checkpointer or MemorySaver()
        self.has_tools = any(bool(c.tools) for c in agents.values())
        self.graph = self._build_graph()
        self.app = self.graph.compile(checkpointer=self.checkpointer)

    def _build_graph(self) -> StateGraph:
        """Build the orchestration graph."""
        workflow = StateGraph(OrchestrationState)

        # Add nodes for each agent
        for role, config in self.agents.items():
            workflow.add_node(role.value, self._create_agent_node(config))

        # Add tool nodes
        all_tools = []
        for config in self.agents.values():
            all_tools.extend(config.tools)
        if all_tools:
            workflow.add_node("tools", ToolNode(all_tools))

        # Add supervisor node (named to avoid collision with AgentRole.ORCHESTRATOR)
        workflow.add_node("supervisor", self._orchestrator_node)

        # Define edges
        workflow.add_edge(START, "supervisor")

        # Supervisor routes to agents (single conditional edge)
        workflow.add_conditional_edges(
            "supervisor",
            self._route_to_agent,
            {role.value: role.value for role in self.agents},
        )

        # Agents can go to tools (if any) or back to supervisor
        after_agent_map = {"supervisor": "supervisor", END: END}
        if all_tools:
            after_agent_map["tools"] = "tools"
        for role in self.agents:
            workflow.add_conditional_edges(
                role.value,
                self._route_after_agent,
                after_agent_map,
            )

        if all_tools:
            workflow.add_edge("tools", "supervisor")

        return workflow

    def _create_agent_node(self, config: AgentConfig) -> Callable:
        """Create a node function for an agent."""
        llm = ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1"),
        )

        if config.tools:
            llm = llm.bind_tools(config.tools)

        def agent_node(state: OrchestrationState) -> OrchestrationState:
            task_id = state.get("current_task_id")
            task = state["tasks"].get(task_id) if task_id else None

            messages = state["messages"] + [
                SystemMessage(content=config.system_prompt),
                HumanMessage(content=task.description if task else "Process the current task")
            ]

            # Add context
            if state.get("context"):
                context_msg = SystemMessage(content=f"Context: {state['context']}")
                messages.insert(-1, context_msg)

            response = llm.invoke(messages)

            new_state = state.copy()
            new_state["messages"] = state["messages"] + [response]

            if task:
                task.status = TaskStatus.COMPLETED
                task.result = {"response": response.content}
                task.completed_at = datetime.utcnow().isoformat()
                new_state["results"][task.id] = task.result

            return new_state

        return agent_node

    def _orchestrator_node(self, state: OrchestrationState) -> OrchestrationState:
        """Orchestrator decides next task/agent."""
        tasks = state.get("tasks", {})
        pending = [t for t in tasks.values() if t.status == TaskStatus.PENDING]

        if not pending:
            return {**state, "current_task_id": None}

        # Simple dependency resolution
        for task in pending:
            deps_met = all(
                tasks.get(dep, Task(id="", name="", role=AgentRole.ORCHESTRATOR, description="")).status == TaskStatus.COMPLETED
                for dep in task.dependencies
            )
            if deps_met:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.utcnow().isoformat()
                return {**state, "current_task_id": task.id}

        return {**state, "current_task_id": None}

    def _route_to_agent(self, state: OrchestrationState) -> str:
        """Route to appropriate agent based on current task."""
        task_id = state.get("current_task_id")
        if not task_id:
            return END

        task = state["tasks"].get(task_id)
        if task:
            return task.role.value
        return END

    def _route_after_agent(self, state: OrchestrationState) -> str:
        """Route after agent execution."""
        messages = state.get("messages", [])
        last_message = messages[-1] if messages else None

        if (
            self.has_tools
            and last_message
            and hasattr(last_message, "tool_calls")
            and last_message.tool_calls
        ):
            return "tools"

        task_id = state.get("current_task_id")
        if task_id:
            task = state["tasks"].get(task_id)
            if task and task.status == TaskStatus.COMPLETED:
                return "supervisor"

        return END

    def run(self, tasks: list[Task], initial_context: dict | None = None, thread_id: str = "default") -> dict[str, Any]:
        """
        Execute orchestration workflow.

        Args:
            tasks: List of tasks to execute
            initial_context: Initial context for the workflow
            thread_id: Thread ID for checkpointing

        Returns:
            Final state with results
        """
        task_dict = {task.id: task for task in tasks}

        initial_state: OrchestrationState = {
            "messages": [],
            "tasks": task_dict,
            "current_task_id": None,
            "context": initial_context or {},
            "results": {},
            "errors": []
        }

        config = RunnableConfig(configurable={"thread_id": thread_id})

        final_state = self.app.invoke(initial_state, config=config)
        return final_state

    def stream(self, tasks: list[Task], initial_context: dict | None = None, thread_id: str = "default"):
        """Stream orchestration execution."""
        task_dict = {task.id: task for task in tasks}

        initial_state: OrchestrationState = {
            "messages": [],
            "tasks": task_dict,
            "current_task_id": None,
            "context": initial_context or {},
            "results": {},
            "errors": []
        }

        config = RunnableConfig(configurable={"thread_id": thread_id})

        yield from self.app.stream(initial_state, config=config)

    def get_state(self, thread_id: str = "default") -> OrchestrationState | None:
        """Get current state from checkpointer."""
        config = RunnableConfig(configurable={"thread_id": thread_id})
        try:
            return self.app.get_state(config)
        except Exception:
            return None


# Pre-built agent configurations for AIG
def create_aig_agents() -> dict[AgentRole, AgentConfig]:
    """Create standard AIG agent configurations."""
    return {
        AgentRole.ORCHESTRATOR: AgentConfig(
            role=AgentRole.ORCHESTRATOR,
            name="Orchestrator",
            system_prompt="""You are the AIG Orchestrator. Decompose high-level goals into tasks,
            assign to specialized agents, manage dependencies, and track progress.
            Use the task tool to create and track work items.""",
        ),
        AgentRole.SECURITY: AgentConfig(
            role=AgentRole.SECURITY,
            name="Security Auditor",
            system_prompt="""You are a Security Auditor. Analyze code, infrastructure, and configurations
            for vulnerabilities. Check for: injection flaws, auth issues, secrets exposure,
            insecure dependencies, and compliance violations.""",
        ),
        AgentRole.PERFORMANCE: AgentConfig(
            role=AgentRole.PERFORMANCE,
            name="Performance Engineer",
            system_prompt="""You are a Performance Engineer. Identify bottlenecks, optimize queries,
            analyze resource usage, and recommend scaling strategies. Focus on latency, throughput,
            and resource efficiency.""",
        ),
        AgentRole.ANDROID: AgentConfig(
            role=AgentRole.ANDROID,
            name="Android Lead",
            system_prompt="""You are the Android Lead. Handle Kotlin/Jetpack Compose development,
            Gradle optimization, Pixel device integration, and mobile-specific concerns.
            Use the android tool for device operations.""",
        ),
        AgentRole.OBSERVABILITY: AgentConfig(
            role=AgentRole.OBSERVABILITY,
            name="Observability Engineer",
            system_prompt="""You are an Observability Engineer. Manage Prometheus, Grafana, Loki, Tempo.
            Create dashboards, alerts, SLOs. Analyze logs, traces, and metrics for system health.""",
        ),
        AgentRole.DEPLOY: AgentConfig(
            role=AgentRole.DEPLOY,
            name="Deploy Engineer",
            system_prompt="""You are a Deploy Engineer. Manage Docker Compose stacks, health gates,
            rollback strategies, and zero-downtime deployments. Use the deploy tool.""",
        ),
    }


# High-level workflow builders
def build_code_review_workflow(pr_number: int, repo: str) -> list[Task]:
    """Build a code review workflow."""
    return [
        Task(id="fetch_pr", name="Fetch PR", role=AgentRole.ORCHESTRATOR,
             description=f"Fetch PR #{pr_number} from {repo}"),
        Task(id="security_review", name="Security Review", role=AgentRole.SECURITY,
             description="Analyze code for security vulnerabilities", dependencies=["fetch_pr"]),
        Task(id="perf_review", name="Performance Review", role=AgentRole.PERFORMANCE,
             description="Analyze performance implications", dependencies=["fetch_pr"]),
        Task(id="code_quality", name="Code Quality", role=AgentRole.CODE_REVIEW,
             description="Check style, patterns, and best practices", dependencies=["fetch_pr"]),
        Task(id="test_analysis", name="Test Analysis", role=AgentRole.TEST,
             description="Verify test coverage and quality", dependencies=["fetch_pr"]),
        Task(id="summary", name="Generate Summary", role=AgentRole.ORCHESTRATOR,
             description="Compile review summary", dependencies=["security_review", "perf_review", "code_quality", "test_analysis"]),
    ]


def build_deploy_workflow(environment: str, version: str) -> list[Task]:
    """Build a deployment workflow."""
    return [
        Task(id="pre_check", name="Pre-deploy Checks", role=AgentRole.ORCHESTRATOR,
             description=f"Run pre-deploy checks for {environment} v{version}"),
        Task(id="security_scan", name="Security Scan", role=AgentRole.SECURITY,
             description="Scan images and config for vulnerabilities", dependencies=["pre_check"]),
        Task(id="deploy_staging", name="Deploy Staging", role=AgentRole.DEPLOY,
             description="Deploy to staging environment", dependencies=["security_scan"]),
        Task(id="health_check", name="Health Checks", role=AgentRole.OBSERVABILITY,
             description="Run health checks on staging", dependencies=["deploy_staging"]),
        Task(id="deploy_prod", name="Deploy Production", role=AgentRole.DEPLOY,
             description="Deploy to production with rollback ready", dependencies=["health_check"]),
        Task(id="post_verify", name="Post-deploy Verification", role=AgentRole.OBSERVABILITY,
             description="Verify production deployment", dependencies=["deploy_prod"]),
    ]


def build_android_workflow(feature: str) -> list[Task]:
    """Build an Android feature workflow."""
    return [
        Task(id="design", name="Design", role=AgentRole.ANDROID,
             description=f"Design {feature} for Android"),
        Task(id="implement", name="Implementation", role=AgentRole.ANDROID,
             description=f"Implement {feature} in Kotlin/Compose", dependencies=["design"]),
        Task(id="test_unit", name="Unit Tests", role=AgentRole.TEST,
             description="Write and run unit tests", dependencies=["implement"]),
        Task(id="test_device", name="Device Tests", role=AgentRole.ANDROID,
             description="Run on Pixel device via Termux", dependencies=["test_unit"]),
        Task(id="build_release", name="Build Release", role=AgentRole.DEPLOY,
             description="Build signed release APK/AAB", dependencies=["test_device"]),
    ]
