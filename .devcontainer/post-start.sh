#!/bin/bash
set -euo pipefail

echo "🚀 Starting aig development services..."

# Start Redis if not running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Starting Redis..."
    redis-server --daemonize yes
fi

# Start PostgreSQL if not running
if ! pg_isready > /dev/null 2>&1; then
    echo "Starting PostgreSQL..."
    service postgresql start
fi

# Start Docker if not running (for Docker-in-Docker)
if ! docker info > /dev/null 2>&1; then
    echo "Starting Docker daemon..."
    dockerd-entrypoint.sh &
    sleep 5
fi

# Pull latest docker images for aig stack
echo "Pulling docker images..."
docker compose -f /workspaces/aig/config/docker/docker-compose.slim.yml pull --quiet > /dev/null 2>&1 &

# Check git status
cd /workspaces/aig
if [ -d .git ]; then
    echo "Git status:"
    git status --short
fi

echo "✅ Services started!"
echo ""
echo "Available commands:"
echo "  uv run pytest tests/ -q                    # Run tests"
echo "  lefthook run pre-commit                    # Test hooks"
echo "  docker compose -f config/docker/docker-compose.prod.yml up -d  # Start stack"
echo "  /aig-audit                                 # Full audit"
echo "  /gate                                      # Quality gate"