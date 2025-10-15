Read the readme for humans if you're a human

Install for your user and bind the command to your keyboard in your wm
eg. for Hyprland `bind = SUPER, O, exec, ~/.local/bin/ovstt once`
or in the GUI's for KDE/Gnome

# Omnivocal

**Omnivocal** is a Wayland-friendly CLI tool for fast, privacy-focused speech-to-text transcription powered by the Chutes Whisper Large V3 API.

## ✨ Features

- 🎤 **Quick Audio Capture**: Record from your microphone, automatically stops when you stop talking
- 🤖 **Voice Activity Detection (VAD)**: Smart auto-stop on silence detection (enabled by default)
- 🔒 **Privacy-Focused**: Uses decentralized Chutes platform, no Big Tech
- 📋 **Clipboard Integration**: Automatic copy via `wl-copy` (Wayland)
- 🔔 **Desktop Notifications**: Visual feedback via `notify-send`
- ⚙️ **Configurable**: TOML configuration with environment variable overrides
- 🩺 **Built-in Diagnostics**: Health checks and API testing

## 🚀 Quick Start

### Installation

```bash
# Install system dependencies (Arch Linux)
sudo pacman -S wl-clipboard libnotify portaudio

# Install Omnivocal (using uv - recommended)
uv venv
uv pip install -e .

# Or using pip
pip install .

# Configure your API key
ovstt config set chutes.api_key "your-chutes-api-key"

# Test the installation
ovstt doctor
ovstt test-api
```

### Basic Usage

```bash
# Record and transcribe (automatically stops when you stop talking)
ovstt once

# Disable voice activity detection (manual stop with Ctrl+C)
ovstt once --no-vad

# Specify language hint for better accuracy
ovstt once --language en
```

The transcription is automatically copied to your clipboard!

## 📖 Commands

### Recording

- `ovstt once` - Record and transcribe (stops automatically when you stop talking)
- `ovstt once --no-vad` - Disable voice activity detection (stop with Ctrl+C)
- `ovstt once --language <code>` - Specify language hint

### Configuration

- `ovstt config show` - Display current configuration
- `ovstt config path` - Show config file location
- `ovstt config edit` - Open config in your editor
- `ovstt config set <key> <value>` - Update a config value

### Diagnostics

- `ovstt doctor` - Run system health checks
- `ovstt test-api` - Test Chutes API connectivity
- `ovstt status` - Show current status

## ⚙️ Configuration

Configuration file location: `~/.config/omnivocal/config.toml`

See `config.example.toml` for a complete example configuration.

### Quick Configuration

```bash
# Set your API key
ovstt config set chutes.api_key "your-api-key"

# Enable voice activity detection
ovstt config set vad.enabled true

# Adjust max recording duration
ovstt config set recording.max_seconds 300
```

### Environment Variables

Override any config value with environment variables:

```bash
export OMNIVOCAL_CHUTES_API_KEY="your-api-key"
export OMNIVOCAL_RECORDING_MAX_SECONDS=300
export OMNIVOCAL_VAD_ENABLED=true
```

## 🧪 Development

```bash
# Clone the repository
git clone https://github.com/SmokySkyline/chutes-omnivocal-public
cd chutes-omnivocal-public

# Create virtual environment with uv (recommended)
uv venv
source .venv/bin/activate

# Install in development mode
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Type checking
uv run mypy src/
```

## 📋 Requirements

### System Dependencies

- Python 3.10+
- `wl-clipboard` (Wayland clipboard)
- `libnotify-bin` (desktop notifications)
- `portaudio` (audio capture)

### Python Dependencies

- `requests` - HTTP client
- `sounddevice` - Audio recording
- `numpy` - Audio processing
- `webrtcvad` - Voice activity detection
- `toml` - Configuration parsing
- `rich` - Terminal UI

## 🔒 Privacy & Security

- **No Big Tech**: Only uses the decentralized Chutes platform
- **Local Processing**: Audio capture and formatting done locally
- **Temporary Files**: Auto-cleanup after transcription
- **HTTPS Encryption**: All API communications are encrypted
- **Local Config**: API keys stored locally with proper permissions

## 🐛 Troubleshooting

### Microphone not working

```bash
# Check audio devices
arecord -l

# Test recording
arecord -d 3 test.wav && aplay test.wav
```

### API connection issues

```bash
# Verify configuration
ovstt config show

# Test API
ovstt test-api
```

### Missing dependencies

```bash
# Run diagnostics
ovstt doctor
```

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Powered by [Chutes](https://chutes.ai) - Decentralized AI platform
- Uses OpenAI Whisper Large V3 model
- Built for the Wayland ecosystem

## 📚 Documentation

For detailed documentation, see:

- `INSTALL.md` - Complete installation guide
- `chutes-omnivocal-prd.md` - Product requirements document
- `config.example.toml` - Configuration examples
