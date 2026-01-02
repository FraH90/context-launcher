"""Platform-specific utilities for cross-platform support."""

import sys
import os
from pathlib import Path
from typing import List, Optional


class PlatformManager:
    """Utilities for platform detection and path resolution."""

    @staticmethod
    def get_platform() -> str:
        """Get current platform identifier.

        Returns:
            Platform string: 'win32', 'darwin', or 'linux'
        """
        return sys.platform

    @staticmethod
    def is_windows() -> bool:
        """Check if running on Windows."""
        return sys.platform == 'win32'

    @staticmethod
    def is_macos() -> bool:
        """Check if running on macOS."""
        return sys.platform == 'darwin'

    @staticmethod
    def is_linux() -> bool:
        """Check if running on Linux."""
        return sys.platform.startswith('linux')

    @staticmethod
    def get_chrome_paths() -> List[Path]:
        """Get possible Chrome installation paths for current platform.

        Returns:
            List of possible Chrome executable paths
        """
        if PlatformManager.is_windows():
            return [
                Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'Google/Chrome/Application/chrome.exe',
                Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / 'Google/Chrome/Application/chrome.exe',
                Path(os.environ.get('LOCALAPPDATA', '')) / 'Google/Chrome/Application/chrome.exe',
            ]
        elif PlatformManager.is_macos():
            return [
                Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
                Path.home() / 'Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            ]
        else:  # Linux
            return [
                Path('/usr/bin/google-chrome'),
                Path('/usr/bin/google-chrome-stable'),
                Path('/usr/bin/chromium'),
                Path('/usr/bin/chromium-browser'),
                Path('/snap/bin/chromium'),
            ]

    @staticmethod
    def get_firefox_paths() -> List[Path]:
        """Get possible Firefox installation paths for current platform.

        Returns:
            List of possible Firefox executable paths
        """
        if PlatformManager.is_windows():
            return [
                Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'Mozilla Firefox/firefox.exe',
                Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / 'Mozilla Firefox/firefox.exe',
                Path.home() / 'AppData/Local/Mozilla Firefox/firefox.exe',
            ]
        elif PlatformManager.is_macos():
            return [
                Path('/Applications/Firefox.app/Contents/MacOS/firefox'),
                Path.home() / 'Applications/Firefox.app/Contents/MacOS/firefox',
            ]
        else:  # Linux
            return [
                Path('/usr/bin/firefox'),
                Path('/usr/bin/firefox-esr'),
                Path('/snap/bin/firefox'),
            ]

    @staticmethod
    def get_edge_paths() -> List[Path]:
        """Get possible Edge installation paths for current platform.

        Returns:
            List of possible Edge executable paths
        """
        if PlatformManager.is_windows():
            return [
                Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe',
                Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'Microsoft/Edge/Application/msedge.exe',
            ]
        elif PlatformManager.is_macos():
            return [
                Path('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),
            ]
        else:  # Linux
            return [
                Path('/usr/bin/microsoft-edge'),
                Path('/usr/bin/microsoft-edge-stable'),
                Path('/usr/bin/microsoft-edge-beta'),
                Path('/usr/bin/microsoft-edge-dev'),
            ]

    @staticmethod
    def get_vscode_paths() -> List[Path]:
        """Get possible VS Code installation paths for current platform.

        Returns:
            List of possible VS Code executable paths
        """
        if PlatformManager.is_windows():
            return [
                Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Microsoft VS Code/Code.exe',
                Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')) / 'Microsoft VS Code/Code.exe',
            ]
        elif PlatformManager.is_macos():
            return [
                Path('/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code'),
                Path.home() / 'Applications/Visual Studio Code.app/Contents/Resources/app/bin/code',
            ]
        else:  # Linux
            return [
                Path('/usr/bin/code'),
                Path('/snap/bin/code'),
            ]

    @staticmethod
    def find_executable(app_name: str) -> Optional[Path]:
        """Find executable for given application name.

        Args:
            app_name: Name of the application (chrome, firefox, edge, vscode)

        Returns:
            Path to executable if found, None otherwise
        """
        search_func = getattr(PlatformManager, f'get_{app_name}_paths', None)

        if not search_func:
            return None

        for path in search_func():
            if path.exists():
                return path

        return None

    @staticmethod
    def get_default_config_dir() -> Path:
        """Get default configuration directory for the app.

        Returns:
            Path to config directory
        """
        from platformdirs import user_config_dir
        return Path(user_config_dir("ContextLauncher", "FraH"))

    @staticmethod
    def get_default_data_dir() -> Path:
        """Get default data directory for the app.

        Returns:
            Path to data directory
        """
        from platformdirs import user_data_dir
        return Path(user_data_dir("ContextLauncher", "FraH"))

    @staticmethod
    def get_default_log_dir() -> Path:
        """Get default log directory for the app.

        Returns:
            Path to log directory
        """
        from platformdirs import user_log_dir
        return Path(user_log_dir("ContextLauncher", "FraH"))
