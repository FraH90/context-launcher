"""Generic application launcher for any executable."""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from ..base import BaseLauncher, LaunchResult, ExecutableNotFoundError, ConfigurationError
from ...core.app_registry import get_app_launch_command, find_app_executable, is_app_available


class GenericAppLauncher(BaseLauncher):
    """Launcher for generic applications.
    
    This launcher can work in two modes:
    1. With app_name from registry - Uses the app_registry to find the executable
    2. With explicit executable_path - Uses the provided path directly
    """

    def __init__(self, config):
        """Initialize generic app launcher.

        Args:
            config: Launch configuration with:
                - app_name: Name of app in registry (e.g., 'spotify', 'discord')
                - executable_path: Optional explicit path to executable
                - arguments: Optional list of command-line arguments
                - working_directory: Optional working directory
        """
        super().__init__(config)
        self.app_name = config.app_name
        self.executable_path = config.parameters.get('executable_path', '')
        self.arguments = config.parameters.get('arguments', [])
        self.working_directory = config.parameters.get('working_directory')

    def launch(self) -> LaunchResult:
        """Launch the application.

        Returns:
            LaunchResult with launch status
        """
        try:
            # Build command - either from registry or explicit path
            args, method = self._build_launch_command()
            
            if not args:
                return LaunchResult.error_result(f"Could not find executable for '{self.app_name}'")

            self._log_launch(f"Launching {self.app_name} via {method}: {' '.join(args[:3])}...")

            # Launch
            process = subprocess.Popen(
                args,
                cwd=self.working_directory,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            app_display_name = self.app_name or Path(self.executable_path).stem
            message = f"Successfully launched {app_display_name}"

            return LaunchResult.success_result(message, process.pid)

        except FileNotFoundError as e:
            raise ExecutableNotFoundError(
                f"Executable not found for '{self.app_name}'"
            ) from e
        except Exception as e:
            self._log_error(f"Launch failed: {e}", e)
            return LaunchResult.error_result(f"Launch failed: {e}", e)

    def _build_launch_command(self) -> tuple:
        """Build the launch command.
        
        Returns:
            Tuple of (command_args, method) or (None, None) if not found
        """
        # If explicit path provided, use it
        if self.executable_path:
            args = [self.executable_path]
            if self.arguments:
                if isinstance(self.arguments, str):
                    args.extend(self.arguments.split())
                else:
                    args.extend(self.arguments)
            return (args, "explicit_path")
        
        # Otherwise, use app registry
        if self.app_name and self.app_name.lower() != 'generic':
            result = get_app_launch_command(self.app_name, self.arguments if self.arguments else None)
            if result:
                return result
        
        return (None, None)

    def validate_config(self) -> bool:
        """Validate launch configuration.

        Returns:
            True if valid

        Raises:
            ConfigurationError: If invalid
        """
        # If explicit path, check it exists
        if self.executable_path:
            if not Path(self.executable_path).exists():
                raise ExecutableNotFoundError(f"Executable not found: {self.executable_path}")
            return True
        
        # If app_name provided (and not 'generic'), check registry
        if self.app_name and self.app_name.lower() != 'generic':
            # On macOS, we can try to launch via 'open -a' even if not in registry
            if sys.platform == 'darwin':
                return True  # Let it try
            
            # On Windows/Linux, check if we can find it
            if find_app_executable(self.app_name):
                return True
            
            raise ExecutableNotFoundError(
                f"App '{self.app_name}' not found. "
                "Either install it or provide an explicit executable_path."
            )
        
        raise ConfigurationError("Either app_name or executable_path is required")

    def get_executable_path(self) -> str:
        """Get executable path.

        Returns:
            Path to executable
        """
        if self.executable_path:
            return self.executable_path
        return find_app_executable(self.app_name) or ""


class SlackLauncher(GenericAppLauncher):
    """Launcher for Slack - uses app registry."""

    def __init__(self, config):
        """Initialize Slack launcher."""
        # Override app_name to use registry
        config.app_name = 'slack'
        super().__init__(config)


class SpotifyLauncher(GenericAppLauncher):
    """Launcher for Spotify - uses app registry."""

    def __init__(self, config):
        """Initialize Spotify launcher."""
        # Override app_name to use registry
        config.app_name = 'spotify'
        super().__init__(config)
