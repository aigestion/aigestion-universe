from typing import Any

from hermes.model_router import FreeModelRouter, get_router


class FreeModelBridge:
    """Connects Hermes orchestration to free model ecosystem"""

    SKILL_TO_TASK = {
        "orchestration": "planning",
        "code_review": "code_review",
        "security_audit": "security_audit",
        "debugging": "debugging",
        "architecture": "architecture",
        "testing": "testing",
        "documentation": "documentation",
        "refactoring": "refactoring",
        "code_generation": "code_generation",
        "quick_fix": "quick_fix",
    }

    def __init__(self, router: FreeModelRouter | None = None):
        self.router = get_router()
        self.memory = None  # Will be set by Hermes

    def set_memory(self, memory):
        self.memory = memory

    async def execute_skill(self, skill_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a skill using the best free model"""
        self.SKILL_TO_TASK.get(skill_name, "general")

        # Get relevant context from memory
        context = {}
        if self.memory:
            memories = await self.memory.search(
                query=skill_name,
                target_harness="opencode",
                limit=5
            )
            context["memories"] = memories

        # Add params to context
        context["params"] = params

        # Route to best free model
        router = get_router()
        await router.route(self._skill_to_task_type(skill_name), params)

        # Build prompt with context
        prompt = self._build_prompt(skill_name, params, context)
        messages = [
            {"role": "system", "content": self._get_skill_system_prompt(skill_name)},
            {"role": "user", "content": prompt}
        ]

        # Execute with best free model
        try:
            result = await self.router.chat(messages, task_type=self._skill_to_task_type(skill_name))

            # Store result in memory
            if self.memory:
                await self.memory.save(
                    title=f"Skill Result: {skill_name}",
                    body=result,
                    kind="lesson",
                    tags=[skill_name, "free-model-result"],
                    source_harness="hermes"
                )

            return {
                "success": True,
                "result": result,
                "model_used": "free",
                "skill": skill_name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "skill": skill_name
            }

    def _skill_to_task_type(self, skill: str) -> str:
        return self.SKILL_TO_TASK.get(skill, "general")

    def _get_skill_system_prompt(self, skill: str) -> str:
        prompts = {
            "orchestration": "You are the aig Master Orchestrator. Decompose epics, coordinate 19 engines, manage cross-engine workflows.",
            "code_review": "You are an expert code reviewer. Focus on security, performance, maintainability. Use ruff baseline.",
            "security_audit": "You are a security auditor. Check for injection, XSS, secrets, dependencies. Zero-cost tools only.",
            "debugging": "You are a debugging expert. Find root cause, minimal fix, verify solution.",
            "architecture": "You are a software architect. Design scalable, maintainable systems.",
            "testing": "You are a TDD expert. Write tests first, 80%+ coverage, pytest.",
            "documentation": "You write clear, concise docs. Follow AGENTS.md style.",
            "refactoring": "You remove dead code, consolidate duplicates, improve structure.",
            "code_generation": "You write clean, typed, tested code. Follow project conventions.",
            "quick_fix": "You fix bugs with minimal changes. No refactoring.",
        }
        return prompts.get(skill, "You are an expert AI assistant.")

    def _build_prompt(self, skill: str, params: dict, context: dict) -> str:
        base = f"Skill: {skill}\nParams: {params}\n"
        if context.get("memories"):
            base += "\nRelevant memories:\n"
            for mem in context["memories"][:3]:
                base += f"- {mem.get('title', '')}: {mem.get('body', '')[:200]}\n"
        base += f"\nExecute {skill} with params: {params}"
        return base

# Singleton
_bridge_instance = None

def get_bridge() -> FreeModelBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = FreeModelBridge()
    return _bridge_instance
