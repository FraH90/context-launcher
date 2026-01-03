# Context Launcher

**Version 3.0** - A powerful, ADHD-friendly workflow launcher for managing and launching multiple applications with custom configurations.

## Overview

Context Launcher helps you organize your digital workspace by creating "sessions" - pre-configured application launches grouped into user-defined categories. Perfect for managing context switching, morning routines, work setups, or any recurring workflow.

### Key Features

- 🗂️ **User-Defined Categories** - Create custom tabs (Work, Entertainment, Morning Routine, etc.)
- 🌐 **Browser Sessions** - Launch Chrome/Firefox/Edge with multiple tabs
- 💻 **IDE Integration** - Open VS Code workspaces
- ⚙️ **Generic Apps** - Launch any application with custom arguments
- 📁 **Template-Based Defaults** - Easily customize initial configuration
- 🎯 **ADHD-Friendly** - Visual organization, minimal clutter, context-focused design

## Installation

### Prerequisites

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/context-launcher.git
cd context-launcher

# Install dependencies with UV
uv sync

# Run the application
uv run python -m context_launcher
```

## Quick Start

1. **Launch the app** - You'll see default tabs: Work, Entertainment, Personal, Uncategorized
2. **Create a category** - Click "+ New Tab", enter a name (e.g., "Morning Routine") and emoji icon (e.g., "☀️")
3. **Add a session** - Click "+ New Session", choose a category, configure your app
4. **Launch** - Double-click a session or select it and click "▶ Launch"

## Supported Application Types

### 1. Browser Sessions

Launch browsers with multiple tabs:

- **Supported browsers:** Chrome, Firefox, Edge
- **Tab types:** Regular URLs, YouTube channels
- **Profile support:** Use specific browser profiles
- **Example:** Morning news routine with multiple news sites

```json
{
  "app_type": "browser",
  "app_name": "chrome",
  "parameters": {
    "tabs": [
      {"type": "url", "url": "https://news.google.com"},
      {"type": "youtube", "channelHandle": "@mkbhd"}
    ],
    "profile": "Work Profile"
  }
}
```

### 2. Code Editors

Open IDE workspaces:

- **Supported editors:** VS Code (more coming soon)
- **Features:** Auto-detect installation, workspace/folder support
- **Example:** Open your project instantly

```json
{
  "app_type": "editor",
  "app_name": "vscode",
  "parameters": {
    "workspace": "C:\\Projects\\my-app"
  }
}
```

### 3. Generic Applications

Launch any application:

- **Pre-configured apps:** Slack, Spotify (auto-detected)
- **Custom executables:** Any .exe with arguments
- **Working directory:** Set custom working directory
- **Example:** Launch custom scripts or tools

```json
{
  "app_type": "generic",
  "app_name": "generic",
  "parameters": {
    "executable_path": "C:\\Tools\\mytool.exe",
    "arguments": ["--config", "dev.json"],
    "working_directory": "C:\\Projects"
  }
}
```

## Architecture

### Project Structure

```
context-launcher/
├── src/
│   └── context_launcher/
│       ├── core/               # Core data models and config
│       │   ├── config.py       # Configuration management
│       │   ├── session.py      # Session data models
│       │   ├── tab.py          # Tab/category models
│       │   └── platform_utils.py
│       ├── launchers/          # Application launchers
│       │   ├── base.py         # Base launcher interface
│       │   ├── browsers/       # Browser launchers
│       │   ├── editors/        # IDE launchers
│       │   └── apps/           # Generic app launchers
│       ├── ui/                 # PySide6 GUI
│       │   ├── main_window.py  # Main application window
│       │   └── session_dialog.py
│       ├── templates/          # Default configuration templates
│       │   ├── default_tabs.json
│       │   ├── default_sessions.json
│       │   └── README.md
│       └── utils/              # Logging and utilities
├── pyproject.toml
└── README.md
```

### Data Storage

User data is stored in platform-specific directories:

- **Windows:** `%LOCALAPPDATA%\FraH\ContextLauncher\`
- **macOS:** `~/Library/Application Support/ContextLauncher/`
- **Linux:** `~/.local/share/ContextLauncher/`

**Directory structure:**
```
ContextLauncher/
├── tabs.json              # User-defined categories
├── sessions/              # Individual session files
│   ├── {uuid1}.json
│   └── {uuid2}.json
├── app_settings.json      # Application settings
└── user_preferences.json  # UI preferences
```

## Default Configuration

### How Defaults are Loaded

On first run, Context Launcher creates default tabs and sessions from **template files** located in:

```
src/context_launcher/templates/
├── default_tabs.json      # Default category tabs
└── default_sessions.json  # Default example sessions
```

**Loading Process:**

1. App starts and checks if `tabs.json` exists in user data directory
2. If not found, loads from `templates/default_tabs.json`
3. Checks if `sessions/` directory is empty
4. If empty, loads from `templates/default_sessions.json`
5. Creates files in user data directory with auto-generated IDs and timestamps

### Customizing Defaults

To customize the default configuration for new installations:

1. **Edit template files** in `src/context_launcher/templates/`:
   - `default_tabs.json` - Add/remove/modify default categories
   - `default_sessions.json` - Add/remove/modify default sessions

2. **Delete existing user data** (to reset):
   ```bash
   # Windows
   del %LOCALAPPDATA%\FraH\ContextLauncher\tabs.json
   rmdir /s %LOCALAPPDATA%\FraH\ContextLauncher\sessions

   # macOS/Linux
   rm ~/Library/Application\ Support/ContextLauncher/tabs.json
   rm -rf ~/Library/Application\ Support/ContextLauncher/sessions/
   ```

3. **Restart the app** - It will recreate from your custom templates

See [templates/README.md](src/context_launcher/templates/README.md) for detailed template format documentation.

## Usage Examples

### Example 1: Morning Routine

Create a "Morning" tab with sessions:

1. **News & Email** - Chrome with Gmail, Google News, Calendar
2. **Standup Prep** - VS Code with project + Slack
3. **Music** - Spotify

### Example 2: Focus Work

Create a "Deep Work" tab:

1. **Project** - VS Code workspace
2. **Documentation** - Browser with API docs, Stack Overflow
3. **Communication Muted** - Slack with DND enabled

### Example 3: Content Creation

Create a "Content" tab:

1. **Recording Setup** - OBS Studio, Discord
2. **Research** - Browser with YouTube, Reddit, Twitter
3. **Editing** - DaVinci Resolve with project folder

## Development

### Tech Stack

- **Python 3.11+** - Core language
- **PySide6** - Qt6 GUI framework
- **Pydantic** - Data validation and models
- **UV** - Fast, modern package manager
- **Platformdirs** - Cross-platform path detection

### Running from Source

```bash
# Activate virtual environment (if using traditional venv)
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Or run directly with UV
uv run python -m context_launcher

# Run tests (Phase 2 launchers)
uv run python test_phase2.py
```

### Adding New Launchers

To add support for a new application:

1. **Create launcher class** in `src/context_launcher/launchers/apps/`:
   ```python
   from ..base import BaseLauncher, LaunchResult, LaunchConfig

   class MyAppLauncher(BaseLauncher):
       def launch(self) -> LaunchResult:
           # Implementation
           pass
   ```

2. **Register in factory** (`launchers/factory.py`):
   ```python
   _registry = {
       'myapp': MyAppLauncher,
   }
   ```

3. **Add to session dialog** (optional) - Update UI to support the new app type

## Roadmap

### ✅ Completed (Phase 1-2)

- [x] Browser launchers (Chrome, Firefox, Edge)
- [x] VS Code launcher
- [x] Generic app launcher
- [x] User-defined tabs/categories
- [x] Template-based configuration
- [x] Session CRUD operations

### 🚧 In Progress (Phase 3)

- [ ] Composite workflows (launch multiple apps in sequence)
- [ ] Delay between launches
- [ ] Workflow execution status

### 📋 Planned (Phase 4-6)

- [ ] State capture (save current browser tabs, VS Code workspaces)
- [ ] Hierarchical categories (nested folders)
- [ ] Favorites and search
- [ ] Keyboard shortcuts
- [ ] Dark theme
- [ ] System tray integration
- [ ] Launch on startup

## Troubleshooting

### Application won't launch

**Browser not found:**
- Ensure browser is installed in default location
- Check logs in user data directory: `Logs/context_launcher.log`

**VS Code not found:**
- Install VS Code from official site
- Verify `code` command is in PATH

### Data corruption

**Reset to defaults:**
```bash
# Backup your data first!
# Then delete user data directory and restart app
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]

## Acknowledgments

Built to help manage ADHD context switching and improve focus through organized workflows.

---

**Need help?** Check the [templates README](src/context_launcher/templates/README.md) for configuration examples or open an issue on GitHub.
