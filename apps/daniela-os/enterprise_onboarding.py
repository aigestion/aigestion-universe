#!/usr/bin/env python3
"""
AIGestion Enterprise Onboarding v1.0
=====================================
Flujo de onboarding para clientes Enterprise:
1. Formulario de evaluacion de necesidades
2. Configuracion inicial personalizada
3. Integracion con sistemas existentes
4. Training y documentacion especifica
5. Go-live checklist

Autor: AIGestion Team
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class OnboardingStep:
    name: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, blocked
    assigned_to: str = ""
    due_date: str = ""
    notes: str = ""
    checklist: list[str] = field(default_factory=list)


class EnterpriseOnboarding:
    """Gestiona el onboarding de clientes Enterprise."""

    DEFAULT_STEPS = [
        OnboardingStep(
            name="Discovery Call",
            description="Llamada inicial para entender necesidades del cliente",
            checklist=[
                "Agendar call de 30 min",
                "Documentar requisitos",
                "Identificar integraciones necesarias",
            ],
        ),
        OnboardingStep(
            name="Technical Assessment",
            description="Evaluacion tecnica de sistemas existentes",
            checklist=[
                "Auditar sistemas actuales",
                "Identificar APIs disponibles",
                "Evaluar seguridad y compliance",
            ],
        ),
        OnboardingStep(
            name="Contract & Billing Setup",
            description="Configuracion de contrato y facturacion",
            checklist=[
                "Firmar contrato Enterprise",
                "Configurar facturacion mensual/anual",
                "Asignar account manager",
            ],
        ),
        OnboardingStep(
            name="Environment Provisioning",
            description="Provisionamiento de infraestructura dedicada",
            checklist=[
                "Crear tenant dedicado",
                "Configurar dominio personalizado",
                "Setup SSL y seguridad",
            ],
        ),
        OnboardingStep(
            name="Integration Configuration",
            description="Integracion con sistemas del cliente",
            checklist=[
                "Conectar Google Workspace/Office 365",
                "Configurar SSO/SAML",
                "Setup webhooks",
            ],
        ),
        OnboardingStep(
            name="Data Migration",
            description="Migracion de datos historicos si aplica",
            checklist=[
                "Exportar datos existentes",
                "Transformar y limpiar",
                "Importar a AIGestion",
            ],
        ),
        OnboardingStep(
            name="White-Label Configuration",
            description="Configuracion de marca personalizada",
            checklist=[
                "Subir logo y favicon",
                "Configurar colores de marca",
                "Personalizar nombre de la IA",
            ],
        ),
        OnboardingStep(
            name="User Training",
            description="Capacitacion del equipo del cliente",
            checklist=["Sesion de onboarding grupal", "Documentacion especifica", "Q&A session"],
        ),
        OnboardingStep(
            name="Testing & QA",
            description="Pruebas antes del go-live",
            checklist=[
                "Testear todos los modulos",
                "Verificar integraciones",
                "Validar white-label",
            ],
        ),
        OnboardingStep(
            name="Go-Live",
            description="Lanzamiento a produccion",
            checklist=[
                "Activar dominio",
                "Enviar comunicado a usuarios",
                "Monitorear primeras 24h",
            ],
        ),
    ]

    def __init__(self, client_name: str = "", client_id: str = ""):
        self.client_name = client_name
        self.client_id = client_id
        self.steps = [self._copy_step(s) for s in self.DEFAULT_STEPS]
        self.started_at = datetime.now().isoformat()
        self.completed_at = ""

    def _copy_step(self, step: OnboardingStep) -> OnboardingStep:
        return OnboardingStep(
            name=step.name,
            description=step.description,
            checklist=list(step.checklist),
        )

    def get_progress(self) -> dict[str, Any]:
        """Retorna progreso del onboarding."""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.status == "completed")
        in_progress = sum(1 for s in self.steps if s.status == "in_progress")
        blocked = sum(1 for s in self.steps if s.status == "blocked")

        return {
            "client": self.client_name,
            "total_steps": total,
            "completed": completed,
            "in_progress": in_progress,
            "blocked": blocked,
            "pending": total - completed - in_progress - blocked,
            "percent": round((completed / total) * 100, 1) if total > 0 else 0,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    def start_step(self, step_name: str) -> bool:
        """Marca un paso como en progreso."""
        for step in self.steps:
            if step.name == step_name:
                step.status = "in_progress"
                return True
        return False

    def complete_step(self, step_name: str, notes: str = "") -> bool:
        """Marca un paso como completado."""
        for step in self.steps:
            if step.name == step_name:
                step.status = "completed"
                step.notes = notes
                # Check if all completed
                if all(s.status == "completed" for s in self.steps):
                    self.completed_at = datetime.now().isoformat()
                return True
        return False

    def block_step(self, step_name: str, reason: str = "") -> bool:
        """Marca un paso como bloqueado."""
        for step in self.steps:
            if step.name == step_name:
                step.status = "blocked"
                step.notes = reason
                return True
        return False

    def to_dict(self) -> dict[str, Any]:

        return {
            "client_name": self.client_name,
            "client_id": self.client_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "progress": self.get_progress(),
            "steps": [
                {
                    "name": s.name,
                    "description": s.description,
                    "status": s.status,
                    "assigned_to": s.assigned_to,
                    "due_date": s.due_date,
                    "notes": s.notes,
                    "checklist": s.checklist,
                }
                for s in self.steps
            ],
        }

    def generate_report(self) -> str:
        """Genera reporte de onboarding en texto."""
        progress = self.get_progress()
        lines = [
            f"# Onboarding Report: {self.client_name}",
            "",
            f"**Progress:** {progress['percent']}% ({progress['completed']}/{progress['total_steps']} steps)",
            f"**Started:** {self.started_at}",
            f"**Completed:** {self.completed_at or 'In progress'}",
            "",
            "## Steps",
        ]

        for step in self.steps:
            icon = {"completed": "✅", "in_progress": "🔄", "blocked": "❌", "pending": "⏳"}.get(
                step.status, "⏳"
            )
            lines.append(f"\n### {icon} {step.name} ({step.status})")
            lines.append(f"{step.description}")
            if step.notes:
                lines.append(f"\n**Notes:** {step.notes}")
            if step.checklist:
                lines.append("\n**Checklist:**")
                for item in step.checklist:
                    lines.append(f"- [ ] {item}")

        return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Enterprise Onboarding")
    parser.add_argument("--client", required=True, help="Nombre del cliente")
    parser.add_argument("--client-id", required=True, help="ID del cliente")
    parser.add_argument("--start-step", help="Iniciar paso")
    parser.add_argument("--complete-step", help="Completar paso")
    parser.add_argument("--progress", action="store_true", help="Ver progreso")
    parser.add_argument("--report", action="store_true", help="Generar reporte")

    args = parser.parse_args()

    onboarding = EnterpriseOnboarding(args.client, args.client_id)

    if args.start_step:
        onboarding.start_step(args.start_step)
        print(f"Paso '{args.start_step}' iniciado")

    if args.complete_step:
        onboarding.complete_step(args.complete_step)
        print(f"Paso '{args.complete_step}' completado")

    if args.progress:
        print(json.dumps(onboarding.get_progress(), indent=2))

    if args.report:
        print(onboarding.generate_report())

    return 0


if __name__ == "__main__":
    sys.exit(main())
