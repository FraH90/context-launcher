"""Microsoft Edge browser launcher."""

import sys
from pathlib import Path
from typing import List
from .base_browser import BrowserLauncher
from ..base import ExecutableNotFoundError


class EdgeLauncher(BrowserLauncher):
    """Launcher for Microsoft Edge browser."""

    def get_executable_path(self) -> str:
        """Get Edge executable path for current platform.

        Returns:
            Path to Edge executable

        Raises:
            ExecutableNotFoundError: If Edge is not found
        """
        # First check if we have an override from the session config (with env var expansion)
        if hasattr(self, 'executable_path_override') and self.executable_path_override:
            return self.executable_path_override
        
        # Try to get from config manager
        from ...core.config import ConfigManager
        config_manager = ConfigManager()
        config_path = config_manager.get_app_path('edge')

        if config_path and Path(config_path).exists():
            return config_path

        # Auto-detect based on platform
        paths = self._get_default_edge_paths()

        for path in paths:
            if path.exists():
                return str(path)

        raise ExecutableNotFoundError(
            f"Edge executable not found. Searched: {', '.join(str(p) for p in paths)}"
        )

    def _get_default_edge_paths(self) -> List[Path]:
        """Get default Edge installation paths for current platform.

        Returns:
            List of possible Edge paths
        """
        if sys.platform == 'win32':
            return [
                Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            ]
        elif sys.platform == 'darwin':
            return [
                Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            ]
        else:  # Linux
            return [
                Path("/usr/bin/microsoft-edge"),
                Path("/usr/bin/microsoft-edge-stable"),
                Path("/usr/bin/microsoft-edge-beta"),
                Path("/usr/bin/microsoft-edge-dev"),
            ]

    def _get_profile_args(self) -> List[str]:
        """Get Edge-specific profile arguments.

        Returns:
            List of profile arguments
        """
        if not self.profile:
            return []

        # Edge uses same args as Chrome (Chromium-based)
        if Path(self.profile).exists():
            return [f"--user-data-dir={self.profile}"]
        else:
            return [f"--profile-directory={self.profile}"]

    def _get_new_window_args(self) -> List[str]:
        """Get Edge-specific new window arguments.

        Returns:
            List of arguments
        """
        return ["--new-window"]
