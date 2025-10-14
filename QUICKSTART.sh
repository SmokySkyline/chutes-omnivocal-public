#!/bin/bash
# Omnivocal Quick Start Script

set -e

echo "🎤 Omnivocal Quick Start"
echo "========================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Found Python $python_version"

# Check for system dependencies
echo ""
echo "Checking system dependencies..."

check_command() {
    if command -v "$1" &> /dev/null; then
        echo "  ✅ $1 found"
        return 0
    else
        echo "  ❌ $1 not found"
        return 1
    fi
}

all_deps_found=true

check_command "wl-copy" || all_deps_found=false
check_command "notify-send" || all_deps_found=false

if [ "$all_deps_found" = false ]; then
    echo ""
    echo "⚠️  Some system dependencies are missing."
    echo ""
    echo "On Arch Linux, install with:"
    echo "  sudo pacman -S wl-clipboard libnotify portaudio"
    echo ""
    echo "On Ubuntu/Debian, install with:"
    echo "  sudo apt-get install wl-clipboard libnotify-bin portaudio19-dev"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if uv is available
echo ""
if command -v uv &> /dev/null; then
    echo "✅ Found uv - using fast installation"
    USE_UV=true
else
    echo "⚠️  uv not found - using pip (slower)"
    echo "   Install uv from: https://github.com/astral-sh/uv"
    USE_UV=false
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ "$USE_UV" = true ]; then
    if [ ! -d ".venv" ]; then
        uv venv
        echo "✅ Virtual environment created with uv"
    else
        echo "✅ Virtual environment already exists"
    fi
    source .venv/bin/activate
else
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✅ Virtual environment created"
    else
        echo "✅ Virtual environment already exists"
    fi
    source venv/bin/activate
fi

# Install package
echo ""
echo "Installing Omnivocal..."
if [ "$USE_UV" = true ]; then
    uv pip install -e .
else
    pip install -q --upgrade pip
    pip install -e .
fi

echo "✅ Omnivocal installed"

# Check if config exists
echo ""
CONFIG_DIR="$HOME/.config/omnivocal"
CONFIG_FILE="$CONFIG_DIR/config.toml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "📝 Configuration file not found. Creating default config..."
    ovstt config show > /dev/null 2>&1
    echo "✅ Default configuration created at: $CONFIG_FILE"
    echo ""
    echo "⚠️  Important: You need to set your Chutes API key!"
    echo ""
    echo "Get your API key from: https://chutes.ai"
    echo ""
    read -p "Do you want to set your API key now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your Chutes API key: " api_key
        ovstt config set chutes.api_key "$api_key"
        echo "✅ API key configured"
    else
        echo ""
        echo "You can set your API key later with:"
        echo "  ovstt config set chutes.api_key \"your-api-key\""
    fi
else
    echo "✅ Configuration found at: $CONFIG_FILE"
fi

# Run diagnostics
echo ""
echo "Running system diagnostics..."
if ovstt doctor; then
    echo ""
    echo "🎉 Installation complete!"
    echo ""
    echo "Quick commands:"
    echo "  ovstt once              # Record and transcribe"
    echo "  ovstt once --vad        # With voice activity detection"
    echo "  ovstt config show       # View configuration"
    echo "  ovstt doctor            # Run diagnostics"
    echo "  ovstt test-api          # Test API connection"
    echo ""
    echo "For more information, see README.md or run: ovstt --help"
else
    echo ""
    echo "⚠️  Some issues were detected. Please review the output above."
    echo ""
    echo "Common fixes:"
    echo "  - Set API key: ovstt config set chutes.api_key \"your-key\""
    echo "  - Install dependencies: see INSTALL.md"
fi

echo ""
if [ "$USE_UV" = true ]; then
    echo "To activate the virtual environment in the future, run:"
    echo "  source .venv/bin/activate"
else
    echo "To activate the virtual environment in the future, run:"
    echo "  source venv/bin/activate"
fi
