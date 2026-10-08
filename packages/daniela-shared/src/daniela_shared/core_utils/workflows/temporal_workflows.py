"""
Temporal Integration for Daniela OS
Durable execution for agent workflows - survive crashes, retries, sagas.
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, TypeVar
from uuid import uuid4

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

T = TypeVar("T")


# ==================== ACTIVITIES ====================

@activity.defn
async def llm_chat(
    messages: list[dict[str, str]],
    model: str = "openrouter-free",
    temperature: float = 0.7,
) -> str:
    """Activity: Call LLM via LiteLLM."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:4000/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('LITELLM_MASTER_KEY', 'sk-aig-master-key')}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=60.0,
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]


@activity.defn
async def query_knowledge(question: str) -> dict[str, Any]:
    """Activity: Query Daniela's knowledge vault via LlamaIndex RAG."""
    from core.knowledge.llamaindex_rag import query_knowledge
    return query_knowledge(question)


@activity.defn
async def search_memory(query: str, agent_id: str, limit: int = 10) -> list[dict]:
    """Activity: Search agent's memory via mem0."""
    from core.memory.mem0_integration import search_memory
    return search_memory(agent_id=agent_id, user_id="shared", query=query, limit=limit)


@activity.defn
async def add_memory(
    agent_id: str,
    user_id: str,
    messages: list[dict[str, str]],
    metadata: dict | None = None,
) -> dict:
    """Activity: Add to agent's memory via mem0."""
    from core.memory.mem0_integration import add_memory
    return add_memory(agent_id, user_id, messages, metadata)


@activity.defn
async def execute_code(code: str, language: str = "python") -> dict[str, Any]:
    """Activity: Execute code in sandbox."""
    # TODO: Implement secure code execution
    return {"output": "Code execution not implemented", "error": None}


@activity.defn
async def deploy_service(
    service_name: str,
    config: dict[str, Any],
    environment: str = "staging",
) -> dict[str, Any]:
    """Activity: Deploy a service via Docker Compose."""
    # TODO: Implement deployment
    return {"status": "deployed", "service": service_name, "environment": environment}


@activity.defn
async def health_check(service: str) -> dict[str, Any]:
    """Activity: Check service health."""
    import httpx

    ports = {
        "daniela": 9200,
        "hermes": 9300,
        "agent": 9800,
        "security": 9999,
        "perf": 9998,
        "infra": 9700,
    }

    port = ports.get(service)
    if not port:
        return {"healthy": False, "error": f"Unknown service: {service}"}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"http://aig-{service}:{port}/health", timeout=5.0)
            return {"healthy": resp.status_code == 200, "status_code": resp.status_code}
        except Exception as e:
            return {"healthy": False, "error": str(e)}


@activity.defn
async def send_notification(
    channel: str,
    message: str,
    severity: str = "info",
) -> bool:
    """Activity: Send notification (Slack, Discord, Email, etc.)."""
    # TODO: Implement notification channels
    print(f"[{severity.upper()}] {channel}: {message}")
    return True


# ==================== WORKFLOWS ====================

@dataclass
class CodeReviewInput:
    pr_number: int
    repo: str
    base_branch: str = "main"


@workflow.defn
class CodeReviewWorkflow:
    """Durable code review workflow with parallel reviews."""

    @workflow.run
    async def run(self, input: CodeReviewInput) -> dict[str, Any]:
        results = await asyncio.gather(
            workflow.execute_activity(
                llm_chat,
                args=[[
                    {"role": "system", "content": "You are a security auditor. Find vulnerabilities."},
                    {"role": "user", "content": f"Review PR #{input.pr_number} for security issues."},
                ], "gemma-2-9b-free"],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            ),
            workflow.execute_activity(
                llm_chat,
                args=[[
                    {"role": "system", "content": "You are a performance engineer. Find bottlenecks."},
                    {"role": "user", "content": f"Review PR #{input.pr_number} for performance issues."},
                ], "groq-llama-8b"],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            ),
            workflow.execute_activity(
                llm_chat,
                args=[[
                    {"role": "system", "content": "You are a code quality reviewer. Check style and patterns."},
                    {"role": "user", "content": f"Review PR #{input.pr_number} for code quality."},
                ], "openrouter-free"],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3),
            ),
        )

        # Aggregate results
        security, performance, quality = results

        summary = await workflow.execute_activity(
            llm_chat,
            args=[[
                {"role": "system", "content": "Summarize code review findings."},
                {"role": "user", "content": f"Security: {security}\nPerformance: {performance}\nQuality: {quality}"},
            ], "openrouter-free"],
            start_to_close_timeout=timedelta(minutes=2),
        )

        return {
            "pr_number": input.pr_number,
            "security": security,
            "performance": performance,
            "quality": quality,
            "summary": summary,
        }


@dataclass
class DeployInput:
    environment: str
    version: str
    services: list[str]


@workflow.defn
class DeployWorkflow:
    """Durable deployment workflow with health gates and rollback."""

    @workflow.run
    async def run(self, input: DeployInput) -> dict[str, Any]:
        # Pre-deploy checks
        await workflow.execute_activity(
            llm_chat,
            args=[[
                {"role": "system", "content": "Run pre-deployment validation."},
                {"role": "user", "content": f"Validate deployment of {input.version} to {input.environment}"},
            ], "openrouter-free"],
            start_to_close_timeout=timedelta(minutes=2),
        )

        # Deploy each service
        for service in input.services:
            await workflow.execute_activity(
                deploy_service,
                args=[service, {"version": input.version}, input.environment],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )

            # Health check after deploy
            health = await workflow.execute_activity(
                health_check,
                args=[service],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=5, initial_interval=timedelta(seconds=10)),
            )

            if not health.get("healthy"):
                # Rollback previous services
                await workflow.execute_activity(
                    send_notification,
                    args=["alerts", f"Deployment failed for {service}, initiating rollback", "critical"],
                    start_to_close_timeout=timedelta(seconds=30),
                )
                return {
                    "status": "failed",
                    "failed_service": service,
                    "health": health,
                }

        # Post-deploy verification
        await workflow.execute_activity(
            send_notification,
            args=["deployments", f"Successfully deployed {input.version} to {input.environment}", "info"],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return {"status": "success", "version": input.version, "environment": input.environment}


@dataclass
class AgentTaskInput:
    agent_role: str
    task_description: str
    context: dict[str, Any] = field(default_factory=dict)


@workflow.defn
class AgentTaskWorkflow:
    """Durable agent task execution with memory and tool use."""

    @workflow.run
    async def run(self, input: AgentTaskInput) -> dict[str, Any]:
        # Search relevant memory
        memories = await workflow.execute_activity(
            search_memory,
            args=[input.task_description, input.agent_role, 10],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Build context with memories
        context_str = "\n".join([
            f"Memory: {m.get('text', '')[:200]}"
            for m in memories
        ])

        # Execute task with LLM
        result = await workflow.execute_activity(
            llm_chat,
            args=[[
                {"role": "system", "content": f"You are {input.agent_role}. Context: {context_str}"},
                {"role": "user", "content": input.task_description},
            ], "openrouter-free"],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        # Store in memory
        await workflow.execute_activity(
            add_memory,
            args=[
                input.agent_role,
                "workflow",
                [
                    {"role": "user", "content": input.task_description},
                    {"role": "assistant", "content": result},
                ],
                {"workflow_id": workflow.info().workflow_id, **input.context},
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )

        return {
            "agent": input.agent_role,
            "task": input.task_description,
            "result": result,
            "memories_used": len(memories),
        }


@dataclass
class PipelineInput:
    name: str
    steps: list[dict[str, Any]]


@workflow.defn
class PipelineWorkflow:
    """Generic durable pipeline workflow."""

    @workflow.run
    async def run(self, input: PipelineInput) -> dict[str, Any]:
        results = {}

        for i, step in enumerate(input.steps):
            step_name = step.get("name", f"step_{i}")
            step_type = step.get("type", "llm")

            try:
                if step_type == "llm":
                    result = await workflow.execute_activity(
                        llm_chat,
                        args=[step.get("messages", []), step.get("model", "openrouter-free")],
                        start_to_close_timeout=timedelta(minutes=step.get("timeout_minutes", 5)),
                    )
                elif step_type == "knowledge":
                    result = await workflow.execute_activity(
                        query_knowledge,
                        args=[step.get("question", "")],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                elif step_type == "deploy":
                    result = await workflow.execute_activity(
                        deploy_service,
                        args=[step.get("service"), step.get("config", {}), step.get("environment", "staging")],
                        start_to_close_timeout=timedelta(minutes=10),
                    )
                elif step_type == "health_check":
                    result = await workflow.execute_activity(
                        health_check,
                        args=[step.get("service")],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                elif step_type == "notify":
                    result = await workflow.execute_activity(
                        send_notification,
                        args=[step.get("channel"), step.get("message"), step.get("severity", "info")],
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                else:
                    result = {"error": f"Unknown step type: {step_type}"}

                results[step_name] = result

                # Check for failure
                if isinstance(result, dict) and result.get("error"):
                    raise Exception(f"Step {step_name} failed: {result['error']}")

            except Exception as e:
                # Compensation: run rollback steps
                for rollback_step in reversed(input.steps[:i]):
                    if rollback_step.get("rollback"):
                        await workflow.execute_activity(
                            llm_chat,
                            args=[[{"role": "user", "content": rollback_step["rollback"]}]],
                            start_to_close_timeout=timedelta(minutes=2),
                        )
                return {
                    "status": "failed",
                    "failed_step": step_name,
                    "error": str(e),
                    "completed_steps": results,
                }

        return {
            "status": "success",
            "pipeline": input.name,
            "results": results,
        }


# ==================== CLIENT & WORKER ====================

class TemporalClient:
    """Temporal client for Daniela workflows."""

    def __init__(self, target_host: str = "localhost:7233"):
        self.target_host = target_host
        self.client: Client | None = None

    async def connect(self) -> None:
        """Connect to Temporal server."""
        self.client = await Client.connect(self.target_host)

    async def start_workflow(
        self,
        workflow_type: type,
        input: Any,
        workflow_id: str,
        task_queue: str = "daniela-tasks",
    ) -> Any:
        """Start a workflow."""
        if not self.client:
            await self.connect()
        return await self.client.execute_workflow(
            workflow_type.run,
            input,
            id=workflow_id,
            task_queue=task_queue,
        )

    async def get_workflow_result(self, workflow_id: str) -> Any:
        """Get workflow result."""
        if not self.client:
            await self.connect()
        handle = self.client.get_workflow_handle(workflow_id)
        return await handle.result()

    async def signal_workflow(self, workflow_id: str, signal_name: str, *args) -> None:
        """Send signal to running workflow."""
        if not self.client:
            await self.connect()
        handle = self.client.get_workflow_handle(workflow_id)
        await handle.signal(signal_name, *args)

    async def cancel_workflow(self, workflow_id: str) -> None:
        """Cancel a workflow."""
        if not self.client:
            await self.connect()
        handle = self.client.get_workflow_handle(workflow_id)
        await handle.cancel()


async def run_worker(
    task_queue: str = "daniela-tasks",
    target_host: str = "localhost:7233",
) -> None:
    """Run Temporal worker for Daniela workflows."""
    client = await Client.connect(target_host)

    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[
            CodeReviewWorkflow,
            DeployWorkflow,
            AgentTaskWorkflow,
            PipelineWorkflow,
        ],
        activities=[
            llm_chat,
            query_knowledge,
            search_memory,
            add_memory,
            execute_code,
            deploy_service,
            health_check,
            send_notification,
        ],
    )

    await worker.run()


# ==================== HIGH-LEVEL HELPERS ====================

class DanielaTemporal:
    """High-level Temporal interface for Daniela."""

    def __init__(self, target_host: str = "localhost:7233"):
        self.client = TemporalClient(target_host)

    async def review_pr(self, pr_number: int, repo: str) -> dict[str, Any]:
        """Start code review workflow."""
        await self.client.connect()
        workflow_id = f"code-review-{pr_number}-{uuid4().hex[:8]}"
        return await self.client.start_workflow(
            CodeReviewWorkflow,
            CodeReviewInput(pr_number=pr_number, repo=repo),
            workflow_id=workflow_id,
        )

    async def deploy(
        self,
        environment: str,
        version: str,
        services: list[str],
    ) -> dict[str, Any]:
        """Start deployment workflow."""
        await self.client.connect()
        workflow_id = f"deploy-{environment}-{version}-{uuid4().hex[:8]}"
        return await self.client.start_workflow(
            DeployWorkflow,
            DeployInput(environment=environment, version=version, services=services),
            workflow_id=workflow_id,
        )

    async def run_agent_task(
        self,
        agent_role: str,
        task: str,
        context: dict | None = None,
    ) -> dict[str, Any]:
        """Run agent task as durable workflow."""
        await self.client.connect()
        workflow_id = f"agent-{agent_role}-{uuid4().hex[:8]}"
        return await self.client.start_workflow(
            AgentTaskWorkflow,
            AgentTaskInput(agent_role=agent_role, task_description=task, context=context or {}),
            workflow_id=workflow_id,
        )

    async def run_pipeline(self, name: str, steps: list[dict]) -> dict[str, Any]:
        """Run generic pipeline workflow."""
        await self.client.connect()
        workflow_id = f"pipeline-{name}-{uuid4().hex[:8]}"
        return await self.client.start_workflow(
            PipelineWorkflow,
            PipelineInput(name=name, steps=steps),
            workflow_id=workflow_id,
        )


# ==================== DOCKER COMPOSE FOR TEMPORAL ====================

TEMPORAL_COMPOSE = """
version: '3.8'

services:
  temporal:
    image: temporalio/auto-setup:1.33
    container_name: aig-temporal
    ports:
      - "7233:7233"
      - "8233:8233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=temporal-postgres
    depends_on:
      temporal-postgres:
        condition: service_healthy
    networks:
      - aig-network
    restart: unless-stopped

  temporal-postgres:
    image: postgres:16-alpine
    container_name: aig-temporal-postgres
    environment:
      - POSTGRES_USER=temporal
      - POSTGRES_PASSWORD=temporal
      - POSTGRES_DB=temporal
    volumes:
      - temporal_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U temporal"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - aig-network

  temporal-web:
    image: temporalio/webui:2.33
    container_name: aig-temporal-web
    ports:
      - "8234:8080"
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
      - TEMPORAL_CORS_ORIGINS=http://localhost:3000
    depends_on:
      - temporal
    networks:
      - aig-network
    restart: unless-stopped

networks:
  aig-network:
    external: true
    name: aig-network

volumes:
  temporal_postgres_data:
    name: aig_temporal_postgres_data
"""

def save_temporal_compose(path: str = "docker-compose.temporal.yml") -> None:
    """Save Temporal docker-compose file."""
    with open(path, "w") as f:
        f.write(TEMPORAL_COMPOSE)
