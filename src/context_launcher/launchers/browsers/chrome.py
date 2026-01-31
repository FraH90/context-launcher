"""Chrome browser launcher."""

import sys
from pathlib import Path
from typing import List
from .base_browser import BrowserLauncher
from ..base import ExecutableNotFoundError


class ChromeLauncher(BrowserLauncher):
    """Launcher for Google Chrome browser."""

    def get_executable_path(self) -> str:
        """Get Chrome executable path for current platform.

        Returns:
            Path to Chrome executable

        Raises:
            ExecutableNotFoundError: If Chrome is not found
        """
        # First check if we have an override from the session config (with env var expansion)
        if hasattr(self, 'executable_path_override') and self.executable_path_override:
            return self.executable_path_override
        
        # Try to get from config manager
        from ...core.config import ConfigManager
        config_manager = ConfigManager()
        config_path = config_manager.get_app_path('chrome')

        if config_path and Path(config_path).exists():
            return config_path

        # Auto-detect based on platform
        paths = self._get_default_chrome_paths()

        for path in paths:
            if path.exists():
                return str(path)

        raise ExecutableNotFoundError(
            f"Chrome executable not found. Searched: {', '.join(str(p) for p in paths)}"
        )

    def _get_default_chrome_paths(self) -> List[Path]:
        """Get default Chrome installation paths for current platform.

        Returns:
            List of possible Chrome paths
        """
        if sys.platform == 'win32':
            return [
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
                Path.home() / r"AppData\Local\Google\Chrome\Application\chrome.exe",
            ]
        elif sys.platform == 'darwin':
            return [
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            ]
        else:  # Linux
            return [
                Path("/usr/bin/google-chrome"),
                Path("/usr/bin/google-chrome-stable"),
                Path("/usr/bin/chromium"),
                Path("/usr/bin/chromium-browser"),
                Path("/snap/bin/chromium"),
            ]

    def _get_profile_args(self) -> List[str]:
        """Get Chrome-specific profile arguments.

        Returns:
            List of profile arguments
        """
        if not self.profile:
            return []

        # Chrome uses --profile-directory for named profiles
        # and --user-data-dir for custom profile paths
        if Path(self.profile).exists():
            # Custom profile path
            return [f"--user-data-dir={self.profile}"]
        else:
            # Named profile (e.g., "Profile 1", "Default")
            return [f"--profile-directory={self.profile}"]

    def _get_new_window_args(self) -> List[str]:
        """Get Chrome-specific new window arguments.

        Returns:
            List of arguments
        """
        return ["--new-window"]

    def _build_command_args(self) -> List[str]:
        """Build Chrome-specific command arguments.

        Returns:
            List of command arguments
        """
        exe_path = self.get_executable_path()

        # On macOS, if we have a .app bundle, use 'open' command
        if sys.platform == 'darwin' and exe_path.endswith('.app'):
            args = ['open', '-a', exe_path]
            # Collect browser arguments
            browser_args = []
            if self.profile:
                browser_args.extend(self._get_profile_args())
            browser_args.extend([
                "--disable-blink-features=AutomationControlled",
                "--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching,OptimizationTargetPrediction,OptimizationHints"
            ])
            browser_args.extend(self._get_new_window_args())
            urls = [tab['url'] for tab in self.tabs if tab.get('type') == 'url']
            browser_args.extend(urls)
            if browser_args:
                args.append('--args')
                args.extend(browser_args)
            return args

        # Direct executable (Windows, Linux)
        args = [exe_path]

        # Add profile if specified
        if self.profile:
            args.extend(self._get_profile_args())

        # Disable automation detection (useful for some sites)
        args.extend([
            "--disable-blink-features=AutomationControlled",
            "--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching,OptimizationTargetPrediction,OptimizationHints"
        ])

        # Add new window flag
        args.extend(self._get_new_window_args())

        # Add URLs
        urls = [tab['url'] for tab in self.tabs if tab.get('type') == 'url']
        args.extend(urls)

        return args
