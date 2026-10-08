"""
Core workflow engine (Ideas 1-10).
DAG-based workflow executor with parallel execution, conditional branching,
loops, retries, sub-workflows, versioning, templates, rollback, timeouts, and persistence.
"""

import ast
import hashlib
import json
import logging
import operator
import sqlite3
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

_AST_BIN_OPS: dict[type, Callable] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
}
_AST_UNARY_OPS: dict[type, Callable] = {
    ast.Not: operator.not_,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
_AST_BOOL_OPS: dict[type, Callable] = {ast.And: all, ast.Or: any}


def _safe_eval(node: ast.AST, context: dict[str, Any]) -> Any:
    """Evalua un AST con whitelist: nombres del contexto, atributos, literales,
    comparaciones, booleanos, subscripts y aritmetica basica. Nada de calls,
    lambdas, comprehensions ni builtins."""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body, context)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in context:
            return context[node.id]
        raise ValueError(f"nombre desconocido: {node.id}")
    if isinstance(node, ast.Attribute):
        return getattr(_safe_eval(node.value, context), node.attr)
    if isinstance(node, ast.Compare):
        left = _safe_eval(node.left, context)
        for op, comparator in zip(node.ops, node.comparators):
            right = _safe_eval(comparator, context)
            fn = _AST_BIN_OPS.get(type(op))
            if fn is None:
                raise ValueError(f"operador no permitido: {type(op).__name__}")
            if not fn(left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.BoolOp):
        return _AST_BOOL_OPS[type(node)]([_safe_eval(v, context) for v in node.values])
    if isinstance(node, ast.UnaryOp):
        fn = _AST_UNARY_OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"operador no permitido: {type(node.op).__name__}")
        return fn(_safe_eval(node.operand, context))
    if isinstance(node, ast.Subscript):
        return _safe_eval(node.value, context)[_safe_eval(node.slice, context)]
    if isinstance(node, ast.BinOp):
        fn = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
        }.get(type(node.op))
        if fn is None:
            raise ValueError(f"operador no permitido: {type(node.op).__name__}")
        return fn(_safe_eval(node.left, context), _safe_eval(node.right, context))
    raise ValueError(f"nodo no permitido: {type(node).__name__}")


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"
    TIMED_OUT = "timed_out"


class WorkflowStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    ROLLED_BACK = "rolled_back"


@dataclass
class Task:
    task_id: str
    name: str
    action_type: str
    params: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    timeout: int | None = None
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    rollback_action: str | None = None
    rollback_params: dict[str, Any] = field(default_factory=dict)
    condition: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    started_at: float | None = None
    finished_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        data["status"] = TaskStatus(data.get("status", "pending"))
        return cls(**data)


@dataclass
class WorkflowVersion:
    version: str
    tasks: list[Task]
    created_at: float
    checksum: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    workflow_id: str
    name: str
    tasks: list[Task]
    version: str = "1.0.0"
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    versions: list[WorkflowVersion] = field(default_factory=list)
    execution_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "tasks": [t.to_dict() for t in self.tasks],
            "version": self.version,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "execution_history": self.execution_history,
        }
        return d


class WorkflowTemplates:
    """Idea 7: Workflow templates library."""

    @staticmethod
    def etl_pipeline() -> dict[str, Any]:
        return {
            "name": "ETL Pipeline",
            "tasks": [
                {"task_id": "extract", "name": "Extract", "action_type": "http_request",
                 "params": {"method": "GET", "url": "https://api.source.com/data"}},
                {"task_id": "transform", "name": "Transform", "action_type": "data_transform",
                 "params": {"input_format": "json", "output_format": "json"},
                 "depends_on": ["extract"]},
                {"task_id": "load", "name": "Load", "action_type": "database_query",
                 "params": {"query": "INSERT INTO target VALUES (...)"},
                 "depends_on": ["transform"]},
            ],
        }

    @staticmethod
    def ci_cd_pipeline() -> dict[str, Any]:
        return {
            "name": "CI/CD Pipeline",
            "tasks": [
                {"task_id": "test", "name": "Run Tests", "action_type": "shell_command",
                 "params": {"command": "pytest tests/"}},
                {"task_id": "build", "name": "Build Docker", "action_type": "docker_build",
                 "params": {"context": ".", "tag": "latest"}, "depends_on": ["test"]},
                {"task_id": "push", "name": "Push to Registry", "action_type": "docker_push",
                 "params": {"tag": "latest"}, "depends_on": ["build"]},
                {"task_id": "deploy", "name": "Deploy", "action_type": "shell_command",
                 "params": {"command": "kubectl apply -f deploy.yaml"}, "depends_on": ["push"]},
            ],
        }

    @staticmethod
    def data_sync() -> dict[str, Any]:
        return {
            "name": "Data Sync",
            "tasks": [
                {"task_id": "fetch_source", "name": "Fetch Source", "action_type": "database_query",
                 "params": {"query": "SELECT * FROM source_table"}},
                {"task_id": "transform", "name": "Transform", "action_type": "data_transform",
                 "depends_on": ["fetch_source"]},
                {"task_id": "load_target", "name": "Load Target", "action_type": "database_query",
                 "params": {"query": "INSERT INTO target_table VALUES (...)"},
                 "depends_on": ["transform"]},
            ],
        }

    @staticmethod
    def notify_on_failure() -> dict[str, Any]:
        return {
            "name": "Notify on Failure",
            "tasks": [
                {"task_id": "main_task", "name": "Main Task", "action_type": "shell_command",
                 "params": {"command": "echo 'Running...'"}},
                {"task_id": "notify", "name": "Send Notification", "action_type": "send_notification",
                 "params": {"message": "Task failed!"}, "depends_on": ["main_task"],
                 "condition": "main_task.status == 'failed'"},
            ],
        }

    @staticmethod
    def get_template(name: str) -> dict[str, Any]:
        templates = {
            "etl": WorkflowTemplates.etl_pipeline,
            "cicd": WorkflowTemplates.ci_cd_pipeline,
            "data_sync": WorkflowTemplates.data_sync,
            "notify_failure": WorkflowTemplates.notify_on_failure,
        }
        factory = templates.get(name)
        return factory() if factory else {}


class DAGValidator:
    """Validates DAG structure for workflows."""

    @staticmethod
    def validate(tasks: list[Task]) -> tuple[bool, str]:
        task_ids = {t.task_id for t in tasks}
        task_map = {t.task_id: t for t in tasks}

        for task in tasks:
            for dep in task.depends_on:
                if dep not in task_ids:
                    return False, f"Task '{task.task_id}' depends on unknown task '{dep}'"

        visited = set()
        rec_stack = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            for dep in task_map[node_id].depends_on:
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.discard(node_id)
            return False

        for task in tasks:
            if task.task_id not in visited:
                if dfs(task.task_id):
                    return False, "Cycle detected in workflow DAG"

        return True, "Valid DAG"


class WorkflowStatePersistence:
    """Idea 10: Workflow state persistence with SQLite."""

    def __init__(self, db_path: str = "workflow_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    name TEXT,
                    data TEXT,
                    created_at REAL,
                    updated_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS executions (
                    execution_id TEXT PRIMARY KEY,
                    workflow_id TEXT,
                    status TEXT,
                    started_at REAL,
                    finished_at REAL,
                    result TEXT,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT,
                    task_id TEXT,
                    status TEXT,
                    result TEXT,
                    error TEXT,
                    started_at REAL,
                    finished_at REAL,
                    FOREIGN KEY (execution_id) REFERENCES executions(execution_id)
                )
            """)

    def save_workflow(self, workflow: Workflow):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO workflows VALUES (?, ?, ?, ?, ?)",
                (workflow.workflow_id, workflow.name, json.dumps(workflow.to_dict()),
                 workflow.created_at, workflow.updated_at),
            )

    def load_workflow(self, workflow_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT data FROM workflows WHERE workflow_id = ?", (workflow_id,)
            ).fetchone()
            return json.loads(row[0]) if row else None

    def list_workflows(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT data FROM workflows").fetchall()
            return [json.loads(r[0]) for r in rows]

    def save_execution(self, execution_id: str, workflow_id: str, status: str,
                       started_at: float, finished_at: float | None, result: str | None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO executions VALUES (?, ?, ?, ?, ?, ?)",
                (execution_id, workflow_id, status, started_at, finished_at, result),
            )

    def get_executions(self, workflow_id: str | None = None) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            if workflow_id:
                rows = conn.execute(
                    "SELECT * FROM executions WHERE workflow_id = ?", (workflow_id,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM executions").fetchall()
            return [{"execution_id": r[0], "workflow_id": r[1], "status": r[2],
                      "started_at": r[3], "finished_at": r[4], "result": r[5]} for r in rows]


class WorkflowEngine:
    """Core workflow engine (Ideas 1-10)."""

    def __init__(self, db_path: str = "workflow_state.db", max_workers: int = 5):
        self.workflows: dict[str, Workflow] = {}
        self.action_handlers: dict[str, Callable] = {}
        self.persistence = WorkflowStatePersistence(db_path)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._load_saved_workflows()

    def shutdown(self):
        self.executor.shutdown(wait=False)

    def _load_saved_workflows(self):
        for data in self.persistence.list_workflows():
            wf = Workflow(
                workflow_id=data["workflow_id"],
                name=data["name"],
                tasks=[Task.from_dict(t) for t in data.get("tasks", [])],
                version=data.get("version", "1.0.0"),
                status=WorkflowStatus(data.get("status", "draft")),
                created_at=data.get("created_at", 0),
                updated_at=data.get("updated_at", 0),
                metadata=data.get("metadata", {}),
            )
            self.workflows[wf.workflow_id] = wf

    def register_action(self, action_type: str, handler: Callable):
        self.action_handlers[action_type] = handler

    def create_workflow(self, name: str, tasks_data: list[dict[str, Any]],
                        version: str = "1.0.0", metadata: dict | None = None) -> Workflow:
        tasks = []
        for t in tasks_data:
            tasks.append(Task(
                task_id=t["task_id"],
                name=t.get("name", t["task_id"]),
                action_type=t["action_type"],
                params=t.get("params", {}),
                depends_on=t.get("depends_on", []),
                timeout=t.get("timeout"),
                max_retries=t.get("max_retries", 3),
                retry_delay=t.get("retry_delay", 1.0),
                backoff_factor=t.get("backoff_factor", 2.0),
                rollback_action=t.get("rollback_action"),
                rollback_params=t.get("rollback_params", {}),
                condition=t.get("condition"),
            ))

        valid, msg = DAGValidator.validate(tasks)
        if not valid:
            raise ValueError(f"Invalid workflow: {msg}")

        wf = Workflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            tasks=tasks,
            version=version,
            metadata=metadata or {},
        )
        self.workflows[wf.workflow_id] = wf
        self.persistence.save_workflow(wf)
        return wf

    def create_from_template(self, template_name: str, **kwargs) -> Workflow:
        tpl = WorkflowTemplates.get_template(template_name)
        if not tpl:
            raise ValueError(f"Unknown template: {template_name}")
        name = kwargs.get("name", tpl["name"])
        return self.create_workflow(name, tpl["tasks"])

    def list_workflows(self) -> list[dict]:
        return [wf.to_dict() for wf in self.workflows.values()]

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self.workflows.get(workflow_id)

    def _save_version(self, workflow: Workflow):
        checksum = hashlib.md5(
            json.dumps([t.to_dict() for t in workflow.tasks], sort_keys=True).encode()
        ).hexdigest()
        ver = WorkflowVersion(
            version=workflow.version,
            tasks=list(workflow.tasks),
            created_at=time.time(),
            checksum=checksum,
        )
        workflow.versions.append(ver)

    def update_workflow_version(self, workflow_id: str, new_version: str,
                                tasks_data: list[dict] | None = None):
        wf = self.workflows.get(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")
        self._save_version(wf)
        wf.version = new_version
        if tasks_data:
            wf.tasks = []
            for t in tasks_data:
                wf.tasks.append(Task(
                    task_id=t["task_id"],
                    name=t.get("name", t["task_id"]),
                    action_type=t["action_type"],
                    params=t.get("params", {}),
                    depends_on=t.get("depends_on", []),
                ))
        wf.updated_at = time.time()
        self.persistence.save_workflow(wf)

    def _get_ready_tasks(self, tasks: list[Task]) -> list[Task]:
        ready = []
        for task in tasks:
            if task.status != TaskStatus.PENDING:
                continue
            deps_met = all(
                next((t for t in tasks if t.task_id == dep and t.status == TaskStatus.COMPLETED), None)
                is not None
                for dep in task.depends_on
            )
            if deps_met:
                ready.append(task)
        return ready

    def _evaluate_condition(self, condition: str, tasks: list[Task]) -> bool:
        if not condition:
            return True
        task_map = {t.task_id: t for t in tasks}
        context = {}
        for tid, task in task_map.items():
            context[f"{tid}.status"] = task.status.value
            context[f"{tid}.result"] = task.result
        # 2026-10-04 (S9): `eval()` era RCE (escape via
        # `().__class__.__mro__[...].__subclasses__()`) y el except devolvia True
        # (fail-open). Ahora: whitelist AST + fail-closed.
        try:
            tree = ast.parse(condition, mode="eval")
            return bool(_safe_eval(tree, context))
        except Exception:
            return False

    def _execute_task(self, task: Task, workflow: Workflow) -> Task:
        if task.condition:
            if not self._evaluate_condition(task.condition, workflow.tasks):
                task.status = TaskStatus.SKIPPED
                return task

        handler = self.action_handlers.get(task.action_type)
        if not handler:
            task.status = TaskStatus.FAILED
            task.error = f"No handler for action type: {task.action_type}"
            return task

        task.status = TaskStatus.RUNNING
        task.started_at = time.time()

        for attempt in range(task.max_retries + 1):
            try:
                if task.timeout:
                    result = [None]
                    error = [None]

                    def run(_handler=handler, _task=task, _result=result, _error=error):
                        try:
                            _result[0] = _handler(_task.params)
                        except Exception as e:
                            _error[0] = e

                    thread = threading.Thread(target=run)
                    thread.start()
                    thread.join(timeout=task.timeout)

                    if thread.is_alive():
                        raise TimeoutError(f"Task timed out after {task.timeout}s")
                    if error[0]:
                        raise error[0]
                    task.result = result[0]
                else:
                    task.result = handler(task.params)

                task.status = TaskStatus.COMPLETED
                task.finished_at = time.time()
                return task

            except Exception as e:
                task.error = str(e)
                if attempt < task.max_retries:
                    delay = task.retry_delay * (task.backoff_factor ** attempt)
                    logger.info(f"Retrying task {task.task_id} in {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                else:
                    task.status = TaskStatus.FAILED
                    task.finished_at = time.time()

        return task

    def _rollback_task(self, task: Task):
        if task.rollback_action and task.status == TaskStatus.FAILED:
            handler = self.action_handlers.get(task.rollback_action)
            if handler:
                try:
                    handler(task.rollback_params)
                    task.status = TaskStatus.ROLLED_BACK
                except Exception as e:
                    logger.error(f"Rollback failed for {task.task_id}: {e}")

    def execute_workflow(self, workflow_id: str) -> dict[str, Any]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")

        wf.status = WorkflowStatus.RUNNING
        execution_id = str(uuid.uuid4())
        started_at = time.time()


        try:
            while True:
                ready = self._get_ready_tasks(wf.tasks)
                if not ready:
                    all_done = all(
                        t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                                     TaskStatus.SKIPPED, TaskStatus.ROLLED_BACK, TaskStatus.TIMED_OUT)
                        for t in wf.tasks
                    )
                    if all_done:
                        break
                    if not any(t.status == TaskStatus.RUNNING for t in wf.tasks):
                        wf.status = WorkflowStatus.FAILED
                        break

                running_futures = {}
                for task in ready:
                    future = self.executor.submit(self._execute_task, task, wf)
                    running_futures[future] = task

                for future in as_completed(running_futures):
                    task = running_futures[future]
                    if task.status == TaskStatus.FAILED:
                        self._rollback_task(task)

            wf.status = WorkflowStatus.COMPLETED if all(
                t.status == TaskStatus.COMPLETED for t in wf.tasks
            ) else WorkflowStatus.FAILED

            finished_at = time.time()
            result = {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": wf.status.value,
                "started_at": started_at,
                "finished_at": finished_at,
                "duration": finished_at - started_at,
                "tasks": {t.task_id: t.to_dict() for t in wf.tasks},
            }

            self.persistence.save_execution(
                execution_id, workflow_id, wf.status.value, started_at, finished_at,
                json.dumps(result),
            )

            wf.execution_history.append(result)
            self.persistence.save_workflow(wf)

            for t in wf.tasks:
                t.status = TaskStatus.PENDING
                t.result = None
                t.error = None

            return result

        except Exception:
            wf.status = WorkflowStatus.FAILED
            raise

    def pause_workflow(self, workflow_id: str):
        wf = self.workflows.get(workflow_id)
        if wf:
            wf.status = WorkflowStatus.PAUSED

    def resume_workflow(self, workflow_id: str):
        wf = self.workflows.get(workflow_id)
        if wf and wf.status == WorkflowStatus.PAUSED:
            wf.status = WorkflowStatus.RUNNING

    def delete_workflow(self, workflow_id: str):
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]


import threading
