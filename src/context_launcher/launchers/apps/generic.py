"""Generic application launcher for any executable."""

import subprocess
from pathlib import Path
from typing import List, Optional
from ..base import BaseLauncher, LaunchResult, ExecutableNotFoundError, ConfigurationError


class GenericAppLauncher(BaseLauncher):
    """Launcher for generic applications."""

    def __init__(self, config):
        """Initialize generic app launcher.

        Args:
            config: Launch configuration with:
                - executable_path: Path to executable
                - arguments: Optional list of command-line arguments
                - working_directory: Optional working directory
        """
        super().__init__(config)
        self.executable_path = config.parameters.get('executable_path', '')
        self.arguments = config.parameters.get('arguments', [])
        self.working_directory = config.parameters.get('working_directory')

    def launch(self) -> LaunchResult:
        """Launch the application.

        Returns:
            LaunchResult with launch status
        """
        try:
            # Validate configuration
            if not self.validate_config():
                return LaunchResult.error_result("Invalid configuration")

            # Build command
            args = self._build_command_args()

            self._log_launch(f"Launching {self.executable_path}")

            # Launch
            process = subprocess.Popen(
                args,
                cwd=self.working_directory,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            app_name = Path(self.executable_path).stem
            message = f"Successfully launched {app_name}"

            return LaunchResult.success_result(message, process.pid)

        except FileNotFoundError as e:
            raise ExecutableNotFoundError(
                f"Executable not found: {self.executable_path}"
            ) from e
        except Exception as e:
            self._log_error(f"Launch failed: {e}", e)
            return LaunchResult.error_result(f"Launch failed: {e}", e)

    def validate_config(self) -> bool:
        """Validate launch configuration.

        Returns:
            True if valid

        Raises:
            ConfigurationError: If invalid
        """
        if not self.executable_path:
            raise ConfigurationError("Executable path is required")

        exe_path = self.get_executable_path()
        if not Path(exe_path).exists():
            raise ExecutableNotFoundError(f"Executable not found: {exe_path}")

        # Validate working directory if specified
        if self.working_directory:
            if not Path(self.working_directory).exists():
                raise ConfigurationError(
                    f"Working directory does not exist: {self.working_directory}"
                )

        return True

    def get_executable_path(self) -> str:
        """Get executable path.

        Returns:
            Path to executable
        """
        return self.executable_path

    def _build_command_args(self) -> List[str]:
        """Build command arguments.

        Returns:
            List of command arguments
        """
        args = [self.executable_path]

        # Add any additional arguments
        if self.arguments:
            if isinstance(self.arguments, str):
                # Split string arguments
                args.extend(self.arguments.split())
            elif isinstance(self.arguments, list):
                args.extend(self.arguments)

        return args


class SlackLauncher(GenericAppLauncher):
    """Launcher for Slack."""

    def __init__(self, config):
        """Initialize Slack launcher."""
        super().__init__(config)

        # Auto-detect Slack if path not provided
        if not self.executable_path:
            self.executable_path = self._find_slack_executable()

    def _find_slack_executable(self) -> str:
        """Find Slack executable.

        Returns:
            Path to Slack executable
        """
        import sys

        if sys.platform == 'win32':
            paths = [
                Path.home() / r"AppData\Local\slack\slack.exe",
            ]
        elif sys.platform == 'darwin':
            paths = [
                Path("/Applications/Slack.app/Contents/MacOS/Slack"),
            ]
        else:  # Linux
            paths = [
                Path("/usr/bin/slack"),
                Path("/snap/bin/slack"),
            ]

        for path in paths:
            if path.exists():
                return str(path)

        raise ExecutableNotFoundError("Slack not found")


class SpotifyLauncher(GenericAppLauncher):
    """Launcher for Spotify."""

    def __init__(self, config):
        """Initialize Spotify launcher."""
        super().__init__(config)

        # Auto-detect Spotify if path not provided
        if not self.executable_path:
            self.executable_path = self._find_spotify_executable()

    def _find_spotify_executable(self) -> str:
        """Find Spotify executable.

        Returns:
            Path to Spotify executable
        """
        import sys

        if sys.platform == 'win32':
            paths = [
                Path.home() / r"AppData\Roaming\Spotify\Spotify.exe",
            ]
        elif sys.platform == 'darwin':
            paths = [
                Path("/Applications/Spotify.app/Contents/MacOS/Spotify"),
            ]
        else:  # Linux
            paths = [
                Path("/usr/bin/spotify"),
                Path("/snap/bin/spotify"),
            ]

        for path in paths:
            if path.exists():
                return str(path)

        raise ExecutableNotFoundError("Spotify not found")
