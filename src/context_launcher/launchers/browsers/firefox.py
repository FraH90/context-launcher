"""Firefox browser launcher."""

import sys
from pathlib import Path
from typing import List
from .base_browser import BrowserLauncher
from ..base import ExecutableNotFoundError


class FirefoxLauncher(BrowserLauncher):
    """Launcher for Mozilla Firefox browser."""

    def get_executable_path(self) -> str:
        """Get Firefox executable path for current platform.

        Returns:
            Path to Firefox executable

        Raises:
            ExecutableNotFoundError: If Firefox is not found
        """
        # First check if we have an override from the session config (with env var expansion)
        if hasattr(self, 'executable_path_override') and self.executable_path_override:
            return self.executable_path_override
        
        # Try to get from config manager
        from ...core.config import ConfigManager
        config_manager = ConfigManager()
        config_path = config_manager.get_app_path('firefox')

        if config_path and Path(config_path).exists():
            return config_path

        # Auto-detect based on platform
        paths = self._get_default_firefox_paths()

        for path in paths:
            if path.exists():
                return str(path)

        raise ExecutableNotFoundError(
            f"Firefox executable not found. Searched: {', '.join(str(p) for p in paths)}"
        )

    def _get_default_firefox_paths(self) -> List[Path]:
        """Get default Firefox installation paths for current platform.

        Returns:
            List of possible Firefox paths
        """
        if sys.platform == 'win32':
            return [
                Path(r"C:\Program Files\Mozilla Firefox\firefox.exe"),
                Path(r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"),
                Path.home() / r"AppData\Local\Mozilla Firefox\firefox.exe",
            ]
        elif sys.platform == 'darwin':
            return [
                Path("/Applications/Firefox.app/Contents/MacOS/firefox"),
                Path.home() / "Applications/Firefox.app/Contents/MacOS/firefox",
            ]
        else:  # Linux
            return [
                Path("/usr/bin/firefox"),
                Path("/usr/bin/firefox-esr"),
                Path("/snap/bin/firefox"),
            ]

    def _get_profile_args(self) -> List[str]:
        """Get Firefox-specific profile arguments.

        Returns:
            List of profile arguments
        """
        if not self.profile:
            return []

        # Firefox uses -P for named profiles and -profile for paths
        if Path(self.profile).exists():
            return ["-profile", self.profile]
        else:
            return ["-P", self.profile]

    def _get_new_window_args(self) -> List[str]:
        """Get Firefox-specific new window arguments.

        Returns:
            List of arguments
        """
        return ["-new-window"]
