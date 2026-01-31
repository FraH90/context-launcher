"""VS Code launcher."""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Union
from ..base import BaseLauncher, LaunchResult, ExecutableNotFoundError, ConfigurationError


class VSCodeLauncher(BaseLauncher):
    """Launcher for Visual Studio Code."""

    def __init__(self, config):
        """Initialize VS Code launcher.

        Args:
            config: Launch configuration
        """
        super().__init__(config)
        self.workspace = config.parameters.get('workspace', '')
        self.folder = config.parameters.get('folder', '')
        self.new_window = config.parameters.get('new_window', False)
        self.add_folder = config.parameters.get('add_folder', False)
        
        # Handle executable_path with environment variable expansion and path arrays
        raw_path = config.parameters.get('executable_path', '')
        self.executable_path_override = self._resolve_executable_path(raw_path)
    
    def _resolve_executable_path(self, path_config: Union[str, List[str]]) -> str:
        """Resolve executable path from config.
        
        Handles environment variable expansion and path arrays.
        
        Args:
            path_config: Path string or list of path strings
            
        Returns:
            Resolved path, or empty string if none found
        """
        if not path_config:
            return ''
        
        paths = [path_config] if isinstance(path_config, str) else path_config
        
        for path in paths:
            if not path:
                continue
            
            expanded_path = os.path.expandvars(path)
            
            if Path(expanded_path).exists():
                return expanded_path
        
        if paths:
            expanded = os.path.expandvars(paths[0])
            return expanded
        
        return ''

    def launch(self) -> LaunchResult:
        """Launch VS Code with workspace or folder.

        Returns:
            LaunchResult with launch status
        """
        try:
            # Validate configuration
            if not self.validate_config():
                return LaunchResult.error_result("Invalid configuration")

            # Build command
            args = self._build_command_args()

            self._log_launch(f"Launching VS Code: {' '.join(args)}")

            # Launch
            process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            target = self.workspace or self.folder or "VS Code"
            message = f"Successfully launched VS Code with {target}"

            return LaunchResult.success_result(message, process.pid)

        except FileNotFoundError as e:
            raise ExecutableNotFoundError(f"VS Code executable not found") from e
        except Exception as e:
            self._log_error(f"Launch failed: {e}", e)
            return LaunchResult.error_result(f"Launch failed: {e}", e)

    def validate_config(self) -> bool:
        """Validate VS Code launch configuration.

        Returns:
            True if valid

        Raises:
            ConfigurationError: If invalid
        """
        # Check if executable exists
        exe_path = self.get_executable_path()
        if not exe_path:
            raise ExecutableNotFoundError("VS Code not found")

        # At least one of workspace or folder should be specified
        if not self.workspace and not self.folder:
            # Allow launching without a workspace (opens last workspace)
            pass

        return True

    def get_executable_path(self) -> str:
        """Get VS Code executable path.

        Returns:
            Path to VS Code executable

        Raises:
            ExecutableNotFoundError: If not found
        """
        # First check if we have an override from the session config (with env var expansion)
        if hasattr(self, 'executable_path_override') and self.executable_path_override:
            return self.executable_path_override
        
        # Try to get from config manager
        from ...core.config import ConfigManager
        config_manager = ConfigManager()
        config_path = config_manager.get_app_path('vscode')

        if config_path and Path(config_path).exists():
            return config_path

        # Try CLI command first (most reliable)
        try:
            result = subprocess.run(
                ['code', '--version'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return 'code'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Auto-detect based on platform
        paths = self._get_default_vscode_paths()

        for path in paths:
            if path.exists():
                return str(path)

        raise ExecutableNotFoundError(
            f"VS Code executable not found. Searched: {', '.join(str(p) for p in paths)}"
        )

    def _get_default_vscode_paths(self) -> List[Path]:
        """Get default VS Code installation paths.

        Returns:
            List of possible paths
        """
        if sys.platform == 'win32':
            return [
                Path.home() / r"AppData\Local\Programs\Microsoft VS Code\Code.exe",
                Path(r"C:\Program Files\Microsoft VS Code\Code.exe"),
                Path(r"C:\Program Files (x86)\Microsoft VS Code\Code.exe"),
            ]
        elif sys.platform == 'darwin':
            return [
                Path("/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"),
                Path.home() / "Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
            ]
        else:  # Linux
            return [
                Path("/usr/bin/code"),
                Path("/usr/local/bin/code"),
                Path("/snap/bin/code"),
            ]

    def _build_command_args(self) -> List[str]:
        """Build command arguments for VS Code.

        Returns:
            List of command arguments
        """
        exe_path = self.get_executable_path()

        # On macOS, if we have a .app bundle, use 'open' command
        if sys.platform == 'darwin' and exe_path.endswith('.app'):
            args = ['open', '-a', exe_path]
            # Collect VS Code arguments
            vscode_args = []
            if self.new_window:
                vscode_args.append('--new-window')
            elif self.add_folder:
                vscode_args.append('--add')
            if self.workspace:
                vscode_args.append(self.workspace)
            elif self.folder:
                vscode_args.append(self.folder)
            # Pass args to VS Code via --args
            if vscode_args:
                args.append('--args')
                args.extend(vscode_args)
            return args

        # Direct executable (code CLI, Windows, Linux)
        args = [exe_path]

        # Add window options
        if self.new_window:
            args.append('--new-window')
        elif self.add_folder:
            args.append('--add')

        # Add workspace or folder
        if self.workspace:
            args.append(self.workspace)
        elif self.folder:
            args.append(self.folder)

        return args

    def supports_state_capture(self) -> bool:
        """VS Code supports state capture.

        Returns:
            True
        """
        return True
