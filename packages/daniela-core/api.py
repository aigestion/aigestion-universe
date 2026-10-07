"""
FastAPI application factory for Daniela Core.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from agents import AgentRegistry
from brain import Brain
from life import DigitalLife
from memory import MemoryVault
from orchestrator import Orchestrator
from persona import PersonaManager
from routes import admin, agents, brain, health, life, memory, orchestrator, persona, tools, voice
from security import SecurityEngine
from tools import ToolGateway
from voice import VoiceEngine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    app.state.brain = Brain()
    app.state.memory = MemoryVault()
    app.state.orchestrator = Orchestrator()
    app.state.persona = PersonaManager()
    app.state.life = DigitalLife()
    app.state.security = SecurityEngine()
    app.state.voice = VoiceEngine()
    app.state.agents = AgentRegistry()
    app.state.tools = ToolGateway()

    await app.state.brain.initialize()
    await app.state.memory.initialize()
    await app.state.orchestrator.initialize()
    await app.state.persona.initialize()
    await app.state.life.initialize()
    await app.state.security.initialize()
    await app.state.voice.initialize()
    await app.state.agents.initialize()
    await app.state.tools.initialize()

    yield

    # Shutdown
    await app.state.tools.shutdown()
    await app.state.agents.shutdown()
    await app.state.voice.shutdown()
    await app.state.security.shutdown()
    await app.state.life.shutdown()
    await app.state.orchestrator.shutdown()
    await app.state.memory.shutdown()
    await app.state.brain.shutdown()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Daniela Core API",
        description="Autonomous AI Service Management & Edge Orchestrator",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configurar en producción
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Prometheus metrics
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    # Routes
    app.include_router(health.router, tags=["health"])
    app.include_router(brain.router, prefix="/api/v1/brain", tags=["brain"])
    app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
    app.include_router(orchestrator.router, prefix="/api/v1/orchestrator", tags=["orchestrator"])
    app.include_router(persona.router, prefix="/api/v1/persona", tags=["persona"])
    app.include_router(life.router, prefix="/api/v1/life", tags=["life"])
    app.include_router(voice.router, prefix="/api/v1/voice", tags=["voice"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

    return app
