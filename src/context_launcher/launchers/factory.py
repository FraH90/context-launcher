"""Launcher factory for creating launcher instances."""

from typing import Dict, Type, Optional
from .base import BaseLauncher, LaunchConfig
from .browsers.chrome import ChromeLauncher
from .browsers.firefox import FirefoxLauncher
from .browsers.edge import EdgeLauncher


class LauncherFactory:
    """Factory for creating launcher instances based on app name."""

    # Registry of available launchers
    _registry: Dict[str, Type[BaseLauncher]] = {
        'chrome': ChromeLauncher,
        'firefox': FirefoxLauncher,
        'edge': EdgeLauncher,
        # More launchers will be added in Phase 2:
        # 'vscode': VSCodeLauncher,
        # 'pycharm': PyCharmLauncher,
        # 'slack': SlackLauncher,
        # 'generic': GenericAppLauncher,
    }

    @classmethod
    def register_launcher(cls, app_name: str, launcher_class: Type[BaseLauncher]):
        """Register a new launcher type (for plugins/extensions).

        Args:
            app_name: Name of the application (e.g., 'chrome', 'vscode')
            launcher_class: Launcher class to register
        """
        cls._registry[app_name.lower()] = launcher_class

    @classmethod
    def unregister_launcher(cls, app_name: str):
        """Unregister a launcher type.

        Args:
            app_name: Name of the application to unregister
        """
        cls._registry.pop(app_name.lower(), None)

    @classmethod
    def create_launcher(cls, launch_config: LaunchConfig) -> BaseLauncher:
        """Create appropriate launcher instance based on configuration.

        Args:
            launch_config: Launch configuration

        Returns:
            Launcher instance for the specified app

        Raises:
            ValueError: If launcher for app_name is not registered
        """
        app_name = launch_config.app_name.lower()

        launcher_class = cls._registry.get(app_name)

        if not launcher_class:
            raise ValueError(
                f"No launcher registered for app '{app_name}'. "
                f"Available launchers: {', '.join(cls._registry.keys())}"
            )

        return launcher_class(launch_config)

    @classmethod
    def get_available_launchers(cls) -> Dict[str, Type[BaseLauncher]]:
        """Get all registered launchers.

        Returns:
            Dictionary mapping app names to launcher classes
        """
        return cls._registry.copy()

    @classmethod
    def is_launcher_available(cls, app_name: str) -> bool:
        """Check if a launcher is available for an app.

        Args:
            app_name: Name of the application

        Returns:
            True if launcher is registered
        """
        return app_name.lower() in cls._registry
