"""Base class for browser launchers."""

import subprocess
from typing import List, Dict, Any
from ..base import BaseLauncher, LaunchConfig, LaunchResult, ExecutableNotFoundError
from pathlib import Path


class BrowserLauncher(BaseLauncher):
    """Base class for all browser launchers."""

    def __init__(self, config: LaunchConfig):
        """Initialize browser launcher.

        Args:
            config: Launch configuration with browser-specific parameters
        """
        super().__init__(config)
        self.tabs: List[Dict[str, Any]] = config.parameters.get('tabs', [])
        self.profile: str = config.parameters.get('profile', '')
        self.use_selenium: bool = config.parameters.get('use_selenium', False)

    def launch(self) -> LaunchResult:
        """Launch browser with configured tabs.

        Returns:
            LaunchResult with launch status
        """
        try:
            # Validate configuration
            if not self.validate_config():
                return LaunchResult.error_result("Invalid configuration")

            # Choose launch method
            if self.use_selenium:
                return self._launch_with_selenium()
            else:
                return self._launch_native()

        except ExecutableNotFoundError as e:
            self._log_error(f"Executable not found: {e}", e)
            return LaunchResult.error_result(str(e), e)
        except Exception as e:
            self._log_error(f"Launch failed: {e}", e)
            return LaunchResult.error_result(f"Launch failed: {e}", e)

    def validate_config(self) -> bool:
        """Validate browser launch configuration.

        Returns:
            True if valid

        Raises:
            ConfigurationError: If invalid
        """
        # Check if executable exists
        exe_path = self.get_executable_path()
        if not Path(exe_path).exists():
            raise ExecutableNotFoundError(f"Browser executable not found: {exe_path}")

        # Validate tabs
        if not isinstance(self.tabs, list):
            return False

        return True

    def _launch_native(self) -> LaunchResult:
        """Launch browser using native subprocess (fast, no dependencies).

        Returns:
            LaunchResult with process information
        """
        args = self._build_command_args()

        self._log_launch(f"Launching {self.config.app_name} with {len(self.tabs)} tabs")

        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            message = f"Successfully launched {self.config.app_name} with {len(self.tabs)} tab(s)"
            return LaunchResult.success_result(message, process.pid)

        except FileNotFoundError as e:
            raise ExecutableNotFoundError(f"Executable not found: {args[0]}") from e

    def _launch_with_selenium(self) -> LaunchResult:
        """Launch browser using Selenium WebDriver (advanced control).

        Returns:
            LaunchResult with process information
        """
        # This is optional and can be implemented if selenium is installed
        raise NotImplementedError(
            "Selenium support is optional. "
            "Install with: pip install selenium"
        )

    def _build_command_args(self) -> List[str]:
        """Build command-line arguments for browser launch.

        Returns:
            List of command arguments

        Note:
            Override this in subclasses for browser-specific args
        """
        args = [self.get_executable_path()]

        # Add profile if specified
        if self.profile:
            args.extend(self._get_profile_args())

        # Add new window flag
        args.extend(self._get_new_window_args())

        # Add URLs
        urls = [tab['url'] for tab in self.tabs if tab.get('type') == 'url']
        args.extend(urls)

        return args

    def _get_profile_args(self) -> List[str]:
        """Get profile-specific arguments.

        Returns:
            List of arguments for profile

        Note:
            Override in subclasses for browser-specific profile handling
        """
        return []

    def _get_new_window_args(self) -> List[str]:
        """Get arguments for opening in new window.

        Returns:
            List of arguments

        Note:
            Override in subclasses for browser-specific behavior
        """
        return ["--new-window"]

    def supports_state_capture(self) -> bool:
        """Browser launchers support state capture.

        Returns:
            True
        """
        return True
