#!/bin/bash
set -euo pipefail

echo "🚀 Setting up aig development environment..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install Python dependencies with uv
echo "Installing Python dependencies..."
cd /workspaces/aig
uv sync --dev --all-extras

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
if command -v lefthook &> /dev/null; then
    lefthook install --force
else
    pip install lefthook
    lefthook install --force
fi

# Install gitleaks
if ! command -v gitleaks &> /dev/null; then
    echo "Installing gitleaks..."
    curl -sSfL https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_linux_x64.tar.gz | tar -xz -C /usr/local/bin
fi

# Setup Android SDK
echo "Setting up Android SDK..."
if [ ! -d "/opt/android-sdk" ]; then
    mkdir -p /opt/android-sdk/cmdline-tools
    cd /tmp
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
    unzip -q commandlinetools-linux-11076708_latest.zip -d /opt/android-sdk/cmdline-tools
    mv /opt/android-sdk/cmdline-tools/cmdline-tools /opt/android-sdk/cmdline-tools/latest
    rm commandlinetools-linux-11076708_latest.zip
fi

export ANDROID_HOME=/opt/android-sdk
export ANDROID_SDK_ROOT=/opt/android-sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

# Accept licenses and install required components
yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --licenses > /dev/null 2>&1
$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0" "cmdline-tools;latest" "emulator" "system-images;android-34;default;arm64-v8a" > /dev/null 2>&1

# Create AVD for testing
if [ ! -d "$HOME/.android/avd/pixel_api34.avd" ]; then
    echo "no" | $ANDROID_HOME/cmdline-tools/latest/bin/avdmanager create avd -n pixel_api34 -k "system-images;android-34;default;arm64-v8a" -d pixel --force
fi

# Install Ruff and tools
echo "Installing dev tools..."
uv tool install ruff@latest
uv tool install mypy@latest
uv tool install black@latest

# Install Kotlin/Gradle tools
if command -v sdk &> /dev/null; then
    sdk install kotlin 1.9.22
    sdk install gradle 8.6
fi

# Create uv cache directory
mkdir -p /workspaces/aig/.uv-cache

echo "✅ Development environment ready!"
echo ""
echo "Next steps:"
echo "  1. Run 'uv run pytest tests/ -q' to verify tests"
echo "  2. Run 'lefthook run pre-commit' to test hooks"
echo "  3. Start services with 'docker compose -f config/docker/docker-compose.prod.yml up -d'"