"""App registry for mapping app names to executable paths across platforms.

This module provides a centralized registry of known applications and their
executable paths on different platforms (macOS, Windows, Linux).
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..utils.logger import get_logger

logger = get_logger(__name__)


# App registry: maps app_name -> {platform: [possible_paths]}
# For macOS, we can use 'open -a "App Name"' which is more reliable
# For Windows, we list known installation paths

APP_REGISTRY: Dict[str, Dict[str, List[str]]] = {
    # === BROWSERS ===
    "chrome": {
        "darwin": ["/Applications/Google Chrome.app"],
        "win32": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "linux": ["/usr/bin/google-chrome", "/usr/bin/chromium-browser"],
    },
    "firefox": {
        "darwin": ["/Applications/Firefox.app"],
        "win32": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ],
        "linux": ["/usr/bin/firefox"],
    },
    "edge": {
        "darwin": ["/Applications/Microsoft Edge.app"],
        "win32": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
        "linux": ["/usr/bin/microsoft-edge"],
    },

    # === CODE EDITORS ===
    "vscode": {
        "darwin": ["/Applications/Visual Studio Code.app"],
        "win32": [
            r"C:\Users\{USER}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            r"C:\Program Files\Microsoft VS Code\Code.exe",
        ],
        "linux": ["/usr/bin/code", "/snap/bin/code"],
    },
    "sublime": {
        "darwin": ["/Applications/Sublime Text.app"],
        "win32": [
            r"C:\Program Files\Sublime Text\sublime_text.exe",
            r"C:\Program Files\Sublime Text 3\sublime_text.exe",
        ],
        "linux": ["/usr/bin/subl", "/snap/bin/subl"],
    },

    # === TERMINALS ===
    "iterm": {
        "darwin": ["/Applications/iTerm.app"],
        "win32": [],  # Not available on Windows
        "linux": [],
    },
    "terminal": {
        "darwin": ["/System/Applications/Utilities/Terminal.app"],
        "win32": [r"C:\Windows\System32\cmd.exe"],
        "linux": ["/usr/bin/gnome-terminal", "/usr/bin/xterm"],
    },

    # === PRODUCTIVITY ===
    "obsidian": {
        "darwin": ["/Applications/Obsidian.app"],
        "win32": [r"C:\Users\{USER}\AppData\Local\Obsidian\Obsidian.exe"],
        "linux": ["/usr/bin/obsidian", "/snap/bin/obsidian"],
    },
    "notability": {
        "darwin": ["/Applications/Notability.app"],
        "win32": [],  # macOS/iOS only
        "linux": [],
    },
    "freeform": {
        "darwin": ["/Applications/Freeform.app", "/System/Applications/Freeform.app"],
        "win32": [],  # Apple only
        "linux": [],
    },
    "bitwarden": {
        "darwin": ["/Applications/Bitwarden.app"],
        "win32": [
            r"C:\Users\{USER}\AppData\Local\Programs\Bitwarden\Bitwarden.exe",
            r"C:\Program Files\Bitwarden\Bitwarden.exe",
        ],
        "linux": ["/usr/bin/bitwarden", "/snap/bin/bitwarden"],
    },
    "raindrop": {
        "darwin": ["/Applications/Raindrop.io.app"],
        "win32": [r"C:\Users\{USER}\AppData\Local\Programs\Raindrop.io\Raindrop.io.exe"],
        "linux": [],
    },

    # === COMMUNICATION ===
    "slack": {
        "darwin": ["/Applications/Slack.app"],
        "win32": [r"C:\Users\{USER}\AppData\Local\slack\slack.exe"],
        "linux": ["/usr/bin/slack", "/snap/bin/slack"],
    },
    "discord": {
        "darwin": ["/Applications/Discord.app"],
        "win32": [r"C:\Users\{USER}\AppData\Local\Discord\Update.exe --processStart Discord.exe"],
        "linux": ["/usr/bin/discord", "/snap/bin/discord"],
    },
    "whatsapp": {
        "darwin": ["/Applications/WhatsApp.app"],
        "win32": [r"C:\Users\{USER}\AppData\Local\WhatsApp\WhatsApp.exe"],
        "linux": [],
    },
    "telegram": {
        "darwin": ["/Applications/Telegram.app"],
        "win32": [
            r"C:\Users\{USER}\AppData\Roaming\Telegram Desktop\Telegram.exe",
        ],
        "linux": ["/usr/bin/telegram-desktop", "/snap/bin/telegram-desktop"],
    },
    "teams": {
        "darwin": ["/Applications/Microsoft Teams.app", "/Applications/Microsoft Teams (work or school).app"],
        "win32": [
            r"C:\Users\{USER}\AppData\Local\Microsoft\Teams\Update.exe --processStart Teams.exe",
            r"C:\Program Files\WindowsApps\MSTeams_*\ms-teams.exe",
        ],
        "linux": ["/usr/bin/teams"],
    },
    "messages": {
        "darwin": ["/System/Applications/Messages.app"],
        "win32": [],  # Apple only
        "linux": [],
    },

    # === AI ===
    "chatgpt": {
        "darwin": ["/Applications/ChatGPT.app"],
        "win32": [r"C:\Users\{USER}\AppData\Local\Programs\ChatGPT\ChatGPT.exe"],
        "linux": [],
    },
    "perplexity": {
        "darwin": ["/Applications/Perplexity.app"],
        "win32": [],
        "linux": [],
    },

    # === MEDIA & ENTERTAINMENT ===
    "spotify": {
        "darwin": ["/Applications/Spotify.app"],
        "win32": [r"C:\Users\{USER}\AppData\Roaming\Spotify\Spotify.exe"],
        "linux": ["/usr/bin/spotify", "/snap/bin/spotify"],
    },
    "vlc": {
        "darwin": ["/Applications/VLC.app"],
        "win32": [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
        ],
        "linux": ["/usr/bin/vlc", "/snap/bin/vlc"],
    },
    "primevideo": {
        "darwin": ["/Applications/Prime Video.app", "/Applications/Amazon Prime Video.app"],
        "win32": [],  # Usually via browser or Windows Store
        "linux": [],
    },
    "steam": {
        "darwin": ["/Applications/Steam.app"],
        "win32": [
            r"C:\Program Files (x86)\Steam\steam.exe",
            r"C:\Program Files\Steam\steam.exe",
        ],
        "linux": ["/usr/bin/steam", "/snap/bin/steam"],
    },
    "photos": {
        "darwin": ["/System/Applications/Photos.app"],
        "win32": [],  # Windows Photos is a UWP app
        "linux": [],
    },
    "tv": {
        "darwin": ["/System/Applications/TV.app"],
        "win32": [],  # Apple only
        "linux": [],
    },
    "podcasts": {
        "darwin": ["/System/Applications/Podcasts.app"],
        "win32": [],
        "linux": [],
    },

    # === MUSIC PRODUCTION ===
    "ableton": {
        "darwin": [
            "/Applications/Ableton Live 12 Suite.app",
            "/Applications/Ableton Live 11 Suite.app",
            "/Applications/Ableton Live 12 Standard.app",
            "/Applications/Ableton Live 11 Standard.app",
        ],
        "win32": [
            r"C:\ProgramData\Ableton\Live 12 Suite\Program\Ableton Live 12 Suite.exe",
            r"C:\ProgramData\Ableton\Live 11 Suite\Program\Ableton Live 11 Suite.exe",
        ],
        "linux": [],
    },
    "logic": {
        "darwin": ["/Applications/Logic Pro.app", "/Applications/Logic Pro X.app"],
        "win32": [],  # Apple only
        "linux": [],
    },
    "modeld": {
        "darwin": ["/Applications/Model D.app"],
        "win32": [],
        "linux": [],
    },
    "ilok": {
        "darwin": ["/Applications/iLok License Manager.app"],
        "win32": [r"C:\Program Files\PACE\iLok License Manager\iLok License Manager.exe"],
        "linux": [],
    },

    # === DEVELOPMENT ===
    "docker": {
        "darwin": ["/Applications/Docker.app"],
        "win32": [
            r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
        ],
        "linux": ["/usr/bin/docker"],
    },

    # === CLOUD & SYNC ===
    "googledrive": {
        "darwin": ["/Applications/Google Drive.app"],
        "win32": [r"C:\Program Files\Google\Drive File Stream\launch.bat"],
        "linux": [],
    },
    "syncthing": {
        "darwin": ["/Applications/Syncthing.app"],
        "win32": [r"C:\Program Files\Syncthing\syncthing.exe"],
        "linux": ["/usr/bin/syncthing"],
    },

    # === UTILITIES ===
    "vncviewer": {
        "darwin": ["/Applications/VNC Viewer.app"],
        "win32": [r"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"],
        "linux": ["/usr/bin/vncviewer"],
    },
    "heatmap": {
        "darwin": ["/Applications/HeatMap.app"],
        "win32": [],
        "linux": [],
    },
    "tradingview": {
        "darwin": ["/Applications/TradingView.app"],
        "win32": [r"C:\Users\{USER}\AppData\Local\Programs\TradingView\TradingView.exe"],
        "linux": [],
    },

    # === WELLBEING ===
    "calm": {
        "darwin": ["/Applications/Calm.app"],
        "win32": [],
        "linux": [],
    },
    "journal": {
        "darwin": ["/Applications/Journal.app", "/System/Applications/Journal.app"],
        "win32": [],
        "linux": [],
    },

    # === APPLE UTILITIES (macOS only) ===
    "appstore": {
        "darwin": ["/System/Applications/App Store.app"],
        "win32": [],
        "linux": [],
    },
    "findmy": {
        "darwin": ["/System/Applications/Find My.app"],
        "win32": [],
        "linux": [],
    },
    "books": {
        "darwin": ["/System/Applications/Books.app"],
        "win32": [],
        "linux": [],
    },
    "contacts": {
        "darwin": ["/System/Applications/Contacts.app"],
        "win32": [],
        "linux": [],
    },
    "maps": {
        "darwin": ["/System/Applications/Maps.app"],
        "win32": [],
        "linux": [],
    },
    "passwords": {
        "darwin": ["/System/Applications/Passwords.app", "/Applications/Passwords.app"],
        "win32": [],
        "linux": [],
    },
    "reminders": {
        "darwin": ["/System/Applications/Reminders.app"],
        "win32": [],
        "linux": [],
    },
    "shortcuts": {
        "darwin": ["/System/Applications/Shortcuts.app"],
        "win32": [],
        "linux": [],
    },
    "siri": {
        "darwin": ["/System/Applications/Siri.app"],
        "win32": [],
        "linux": [],
    },
    "stocks": {
        "darwin": ["/System/Applications/Stocks.app"],
        "win32": [],
        "linux": [],
    },
    "systemsettings": {
        "darwin": ["/System/Applications/System Settings.app", "/System/Applications/System Preferences.app"],
        "win32": [],
        "linux": [],
    },
    "tips": {
        "darwin": ["/System/Applications/Tips.app"],
        "win32": [],
        "linux": [],
    },
    "voicememos": {
        "darwin": ["/System/Applications/Voice Memos.app"],
        "win32": [],
        "linux": [],
    },
}


def get_user_home() -> str:
    """Get user home directory."""
    return str(Path.home())


def expand_path(path: str) -> str:
    """Expand {USER} placeholder in path."""
    if "{USER}" in path:
        import os
        username = os.getenv("USERNAME") or os.getenv("USER") or "user"
        path = path.replace("{USER}", username)
    return path


def find_app_executable(app_name: str, platform: str = None) -> Optional[str]:
    """Find executable path for an app on the current platform.
    
    Args:
        app_name: Name of the app (key in APP_REGISTRY)
        platform: Platform to search for (defaults to current)
        
    Returns:
        Path to executable if found, None otherwise
    """
    if platform is None:
        platform = sys.platform
    
    app_name_lower = app_name.lower()
    
    if app_name_lower not in APP_REGISTRY:
        logger.warning(f"App '{app_name}' not in registry")
        return None
    
    paths = APP_REGISTRY[app_name_lower].get(platform, [])
    
    for path in paths:
        expanded_path = expand_path(path)
        if Path(expanded_path).exists():
            return expanded_path
    
    return None


# Mapping from short app_name to macOS display name for 'open -a'
MACOS_APP_NAMES: Dict[str, str] = {
    # Apple apps (use actual names for open -a)
    "tv": "TV",
    "appstore": "App Store",
    "findmy": "Find My",
    "books": "Books",
    "contacts": "Contacts",
    "maps": "Maps",
    "messages": "Messages",
    "passwords": "Passwords",
    "podcasts": "Podcasts",
    "reminders": "Reminders",
    "shortcuts": "Shortcuts",
    "siri": "Siri",
    "stocks": "Stocks",
    "systemsettings": "System Settings",
    "tips": "Tips",
    "voicememos": "Voice Memos",
    "photos": "Photos",
    "journal": "Journal",
    "freeform": "Freeform",
    # Third-party apps
    "chrome": "Google Chrome",
    "firefox": "Firefox",
    "edge": "Microsoft Edge",
    "vscode": "Visual Studio Code",
    "sublime": "Sublime Text",
    "obsidian": "Obsidian",
    "iterm": "iTerm",
    "spotify": "Spotify",
    "notability": "Notability",
    "chatgpt": "ChatGPT",
    "whatsapp": "WhatsApp",
    "teams": "Microsoft Teams",
    "vlc": "VLC",
    "perplexity": "Perplexity",
    "docker": "Docker",
    "ableton": "Ableton Live 12 Suite",
    "ilok": "iLok License Manager",
    "logic": "Logic Pro",
    "modeld": "Model D",
    "primevideo": "Prime Video",
    "steam": "Steam",
    "discord": "Discord",
    "telegram": "Telegram",
    "bitwarden": "Bitwarden",
    "googledrive": "Google Drive",
    "heatmap": "HeatMap",
    "raindrop": "Raindrop.io",
    "syncthing": "Syncthing",
    "tradingview": "TradingView",
    "vncviewer": "VNC Viewer",
    "calm": "Calm",
    "slack": "Slack",
}


# Mapping from short app_name to Windows display name for finding apps
WINDOWS_APP_NAMES: Dict[str, str] = {
    "chrome": "Google Chrome",
    "firefox": "Mozilla Firefox",
    "edge": "Microsoft Edge",
    "vscode": "Visual Studio Code",
    "sublime": "Sublime Text",
    "obsidian": "Obsidian",
    "spotify": "Spotify",
    "chatgpt": "ChatGPT",
    "discord": "Discord",
    "telegram": "Telegram Desktop",
    "teams": "Microsoft Teams",
    "vlc": "VideoLAN\\VLC",
    "docker": "Docker",
    "steam": "Steam",
    "slack": "Slack",
    "bitwarden": "Bitwarden",
    "syncthing": "Syncthing",
    "tradingview": "TradingView",
    "vncviewer": "RealVNC\\VNC Viewer",
    "ableton": "Ableton\\Live 12 Suite",
    "ilok": "PACE\\iLok License Manager",
}


def get_app_launch_command(app_name: str, arguments: List[str] = None) -> Optional[Tuple[List[str], str]]:
    """Get the command to launch an app.
    
    On macOS, uses 'open -a' which is more reliable for .app bundles.
    On Windows/Linux, uses the direct executable path.
    
    Args:
        app_name: Name of the app
        arguments: Optional arguments to pass
        
    Returns:
        Tuple of (command_list, method) where method is 'open' or 'direct'
        None if app not found
    """
    platform = sys.platform
    app_name_lower = app_name.lower()
    
    if arguments is None:
        arguments = []
    
    if platform == "darwin":
        # On macOS, prefer using 'open -a' for .app bundles
        exe_path = find_app_executable(app_name_lower)
        
        if exe_path and exe_path.endswith(".app"):
            # Use 'open -a' for app bundles
            cmd = ["open", "-a", exe_path]
            if arguments:
                cmd.append("--args")
                cmd.extend(arguments)
            return (cmd, "open")
        elif exe_path:
            # Direct executable
            return ([exe_path] + arguments, "direct")
        else:
            # Try 'open -a' with the macOS app name
            # Use the display name mapping, or fall back to the app_name as-is
            macos_name = MACOS_APP_NAMES.get(app_name_lower, app_name)
            cmd = ["open", "-a", macos_name]
            if arguments:
                cmd.append("--args")
                cmd.extend(arguments)
            return (cmd, "open")
    
    else:
        # Windows/Linux - use direct executable
        exe_path = find_app_executable(app_name_lower)
        if exe_path:
            return ([exe_path] + arguments, "direct")
    
    return None


def is_app_available(app_name: str) -> bool:
    """Check if an app is available on the current platform.
    
    Args:
        app_name: Name of the app
        
    Returns:
        True if app executable exists
    """
    return find_app_executable(app_name) is not None


def get_available_apps() -> List[str]:
    """Get list of apps available on the current platform.
    
    Returns:
        List of app names that have executables found
    """
    available = []
    for app_name in APP_REGISTRY:
        if is_app_available(app_name):
            available.append(app_name)
    return sorted(available)


def get_all_registered_apps() -> List[str]:
    """Get list of all registered app names.
    
    Returns:
        List of all app names in registry
    """
    return sorted(APP_REGISTRY.keys())


def register_app(app_name: str, paths: Dict[str, List[str]]):
    """Register a new app or update existing registration.
    
    Args:
        app_name: Name of the app
        paths: Dict mapping platform -> list of possible paths
    """
    APP_REGISTRY[app_name.lower()] = paths
    logger.info(f"Registered app: {app_name}")
