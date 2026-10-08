"""
Langfuse Integration for Daniela OS
LLM Observability - Traces, Evaluations, Prompt Management, Analytics.
"""
from __future__ import annotations

import os
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any

from langfuse import Langfuse
from langfuse.openai import openai as langfuse_openai
from langfuse.types import SpanLevel as SpanStatus


@dataclass
class LangfuseConfig:
    """Configuration for Langfuse."""
    public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    host: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    enabled: bool = True
    debug: bool = False


class DanielaLangfuse:
    """
    Langfuse wrapper for Daniela's LLM observability.
    Provides tracing, evaluations, prompt management, and analytics.
    """

    def __init__(self, config: LangfuseConfig | None = None):
        self.config = config or LangfuseConfig()
        self.client: Langfuse | None = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Langfuse client."""
        if not self.config.enabled or not self.config.public_key:
            return

        try:
            self.client = Langfuse(
                public_key=self.config.public_key,
                secret_key=self.config.secret_key,
                host=self.config.host,
                debug=self.config.debug,
            )
        except Exception as e:
            print(f"[Langfuse] Failed to initialize: {e}")
            self.client = None

    def flush(self) -> None:
        """Flush pending events."""
        if self.client:
            self.client.flush()

    # ==================== TRACING ====================

    @contextmanager
    def trace(
        self,
        name: str,
        input: Any | None = None,
        output: Any | None = None,
        metadata: dict | None = None,
        tags: list[str] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
    ):
        """Context manager for tracing a workflow."""
        if not self.client:
            yield None
            return

        trace = self.client.trace(
            id=trace_id or str(uuid.uuid4()),
            name=name,
            input=input,
            output=output,
            metadata=metadata or {},
            tags=tags or [],
            user_id=user_id,
            session_id=session_id,
        )

        try:
            yield trace
        except Exception as e:
            trace.update(
                status=SpanStatus.ERROR,
                output={"error": str(e)},
            )
            raise
        finally:
            self.client.flush()

    @contextmanager
    def span(
        self,
        name: str,
        input: Any | None = None,
        output: Any | None = None,
        metadata: dict | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ):
        """Context manager for a span within a trace."""
        if not self.client:
            yield None
            return

        span = self.client.span(
            name=name,
            input=input,
            output=output,
            metadata=metadata or {},
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )

        try:
            yield span
        except Exception as e:
            span.update(
                status=SpanStatus.ERROR,
                output={"error": str(e)},
            )
            raise
        finally:
            self.client.flush()

    def generation(
        self,
        name: str,
        model: str,
        input: list[dict],
        output: str | None = None,
        usage: dict | None = None,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        metadata: dict | None = None,
    ):
        """Create a generation (LLM call) span."""
        if not self.client:
            return None

        return self.client.generation(
            name=name,
            model=model,
            input=input,
            output=output,
            usage=usage,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            metadata=metadata or {},
        )

    # ==================== DECORATORS ====================

    def trace_function(
        self,
        name: str | None = None,
        tags: list[str] | None = None,
    ):
        """Decorator to trace a function."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.client:
                    return func(*args, **kwargs)

                trace_name = name or f"{func.__module__}.{func.__qualname__}"

                with self.trace(trace_name, tags=tags) as trace:
                    trace.update(input={"args": str(args)[:500], "kwargs": str(kwargs)[:500]})
                    result = func(*args, **kwargs)
                    trace.update(output={"result": str(result)[:500]})
                    return result

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.client:
                    return await func(*args, **kwargs)

                trace_name = name or f"{func.__module__}.{func.__qualname__}"

                with self.trace(trace_name, tags=tags) as trace:
                    trace.update(input={"args": str(args)[:500], "kwargs": str(kwargs)[:500]})
                    result = await func(*args, **kwargs)
                    trace.update(output={"result": str(result)[:500]})
                    return result

            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return wrapper
        return decorator

    def observe_llm(
        self,
        name: str | None = None,
        model: str | None = None,
    ):
        """Decorator to observe LLM calls."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.client:
                    return func(*args, **kwargs)

                generation_name = name or func.__name__

                # Extract model from kwargs or use default
                gen_model = model or kwargs.get("model", "unknown")

                generation = self.generation(
                    name=generation_name,
                    model=gen_model,
                    input=kwargs.get("messages", []),
                )

                try:
                    result = func(*args, **kwargs)
                    generation.update(output=result)
                    return result
                except Exception as e:
                    generation.update(
                        status=SpanStatus.ERROR,
                        output={"error": str(e)},
                    )
                    raise
                finally:
                    generation.end()
                    self.flush()

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not self.client:
                    return await func(*args, **kwargs)

                generation_name = name or func.__name__
                gen_model = model or kwargs.get("model", "unknown")

                generation = self.generation(
                    name=generation_name,
                    model=gen_model,
                    input=kwargs.get("messages", []),
                )

                try:
                    result = await func(*args, **kwargs)
                    generation.update(output=result)
                    return result
                except Exception as e:
                    generation.update(
                        status=SpanStatus.ERROR,
                        output={"error": str(e)},
                    )
                    raise
                finally:
                    generation.end()
                    self.flush()

            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return wrapper
        return decorator

    # ==================== EVALUATIONS ====================

    def create_evaluation(
        self,
        trace_id: str,
        name: str,
        value: float | int | bool | str,
        comment: str | None = None,
        dataset_name: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Create an evaluation for a trace."""
        if not self.client:
            return

        self.client.score(
            trace_id=trace_id,
            name=name,
            value=value,
            comment=comment,
            dataset_name=dataset_name,
            metadata=metadata or {},
        )
        self.flush()

    def evaluate_quality(
        self,
        trace_id: str,
        scores: dict[str, float | int | bool],
        comments: dict[str, str] | None = None,
    ) -> None:
        """Evaluate multiple quality dimensions."""
        for name, value in scores.items():
            self.create_evaluation(
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comments.get(name) if comments else None,
            )

    # ==================== PROMPT MANAGEMENT ====================

    def get_prompt(self, name: str, version: int | None = None) -> dict | None:
        """Get a prompt from Langfuse."""
        if not self.client:
            return None
        try:
            prompt = self.client.get_prompt(name, version=version)
            return {
                "name": prompt.name,
                "version": prompt.version,
                "prompt": prompt.prompt,
                "labels": prompt.labels,
                "tags": prompt.tags,
            }
        except Exception:
            return None

    def create_prompt(
        self,
        name: str,
        prompt: str,
        labels: list[str] | None = None,
        tags: list[str] | None = None,
        is_active: bool = True,
    ) -> bool:
        """Create or update a prompt."""
        if not self.client:
            return False
        try:
            self.client.create_prompt(
                name=name,
                prompt=prompt,
                labels=labels or [],
                tags=tags or [],
                is_active=is_active,
            )
            return True
        except Exception:
            return False

    # ==================== DATASETS ====================

    def create_dataset(self, name: str, description: str | None = None) -> bool:
        """Create a dataset for evaluations."""
        if not self.client:
            return False
        try:
            self.client.create_dataset(name=name, description=description or "")
            return True
        except Exception:
            return False

    def add_dataset_item(
        self,
        dataset_name: str,
        input: Any,
        expected_output: Any | None = None,
        metadata: dict | None = None,
    ) -> bool:
        """Add an item to a dataset."""
        if not self.client:
            return False
        try:
            self.client.create_dataset_item(
                dataset_name=dataset_name,
                input=input,
                expected_output=expected_output,
                metadata=metadata or {},
            )
            return True
        except Exception:
            return False

    def run_evaluation(
        self,
        dataset_name: str,
        evaluator: Callable,
        run_name: str | None = None,
    ) -> dict[str, Any]:
        """Run evaluation on a dataset."""
        if not self.client:
            return {"error": "Langfuse not initialized"}
        # This would use Langfuse's evaluation API
        return {"status": "not_implemented"}

    # ==================== ANALYTICS ====================

    def get_traces(
        self,
        name: str | None = None,
        user_id: str | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Get traces (requires Langfuse API)."""
        if not self.client:
            return []
        # Would use Langfuse API to fetch traces
        return []

    def get_metrics(
        self,
        from_timestamp: datetime,
        to_timestamp: datetime,
        interval: str = "hour",
    ) -> dict[str, Any]:
        """Get aggregate metrics."""
        if not self.client:
            return {}
        # Would use Langfuse API
        return {}

    # ==================== SESSION TRACKING ====================

    def track_session(
        self,
        session_id: str,
        user_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Track a user session."""
        if not self.client:
            return
        trace = self.client.trace(
            id=session_id,
            name="user_session",
            metadata=metadata or {},
            user_id=user_id,
            session_id=session_id,
        )
        trace.update(output={"status": "started"})
        self.flush()

    def end_session(self, session_id: str, metadata: dict | None = None) -> None:
        """End a user session."""
        if not self.client:
            return
        trace = self.client.trace(id=session_id)
        trace.update(
            output={"status": "ended", **(metadata or {})},
        )
        self.flush()


# ==================== OPENAI WRAPPER ====================

def get_langfuse_openai_client(
    config: LangfuseConfig | None = None,
) -> Any:
    """Get OpenAI client wrapped with Langfuse tracing."""
    config or LangfuseConfig()
    return langfuse_openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "sk-aig-master-key"),
        base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:4000/v1"),
    )


# ==================== GLOBAL INSTANCE ====================

_default_langfuse: DanielaLangfuse | None = None


def get_langfuse() -> DanielaLangfuse:
    """Get global Langfuse instance."""
    global _default_langfuse
    if _default_langfuse is None:
        _default_langfuse = DanielaLangfuse()
    return _default_langfuse


def trace_workflow(name: str, **kwargs):
    """Decorator to trace a workflow function."""
    return get_langfuse().trace_function(name, **kwargs)


def observe_llm_call(name: str, model: str | None = None):
    """Decorator to observe an LLM call."""
    return get_langfuse().observe_llm(name, model)


# ==================== INTEGRATION WITH EXISTING SYSTEMS ====================

class LangfuseMiddleware:
    """Middleware to add Langfuse tracing to HTTP requests."""

    def __init__(self, app, langfuse: DanielaLangfuse | None = None):
        self.app = app
        self.langfuse = langfuse or get_langfuse()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if not self.langfuse.client:
            await self.app(scope, receive, send)
            return

        # Extract trace context from headers
        headers = dict(scope.get("headers", []))
        trace_id = None
        for k, v in headers.items():
            if k.decode() == "x-trace-id":
                trace_id = v.decode()
                break

        with self.langfuse.trace(
            name=f"HTTP {scope.get('method', 'GET')} {scope.get('path', '/')}",
            trace_id=trace_id,
            metadata={
                "method": scope.get("method"),
                "path": scope.get("path"),
                "query_string": scope.get("query_string", b"").decode(),
            },
        ) as trace:
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    trace.update(
                        output={"status_code": message.get("status")},
                        metadata={"status_code": message.get("status")},
                    )
                await send(message)

            await self.app(scope, receive, send_wrapper)


# ==================== SPECIFIC DANIELA INTEGRATIONS ====================

def trace_daniela_request(operation: str):
    """Decorator for Daniela engine operations."""
    return get_langfuse().trace_function(f"daniela.{operation}", tags=["daniela", "engine"])


def trace_hermes_task(task_type: str):
    """Decorator for Hermes orchestrator tasks."""
    return get_langfuse().trace_function(f"hermes.{task_type}", tags=["hermes", "orchestrator"])


def trace_agent_action(agent_name: str, action: str):
    """Decorator for agent actions."""
    return get_langfuse().trace_function(f"agent.{agent_name}.{action}", tags=["agent", agent_name])


def trace_security_scan(scan_type: str):
    """Decorator for security scans."""
    return get_langfuse().trace_function(f"security.{scan_type}", tags=["security", "scan"])


def trace_performance_analysis(analysis_type: str):
    """Decorator for performance analysis."""
    return get_langfuse().trace_function(f"perf.{analysis_type}", tags=["performance", "analysis"])


# ==================== QUICK SETUP ====================

def setup_langfuse(
    public_key: str,
    secret_key: str,
    host: str = "https://cloud.langfuse.com",
) -> DanielaLangfuse:
    """Quick setup for Langfuse."""
    config = LangfuseConfig(
        public_key=public_key,
        secret_key=secret_key,
        host=host,
    )
    global _default_langfuse
    _default_langfuse = DanielaLangfuse(config)
    return _default_langfuse


# Example usage
if __name__ == "__main__":
    # Setup (add your keys)
    # langfuse = setup_langfuse("pk-...", "sk-...")

    # Trace a workflow
    # @trace_daniela_request("chat")
    # def chat(messages):
    #     return llm_call(messages)

    # Observe LLM call
    # @observe_llm_call("chat_completion", "gpt-4o-mini")
    # def llm_call(messages):
    #     return openai_client.chat.completions.create(...)

    print("Langfuse integration ready. Add LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to .env")
