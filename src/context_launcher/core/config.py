"""Configuration management for the application."""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from .platform_utils import PlatformManager


class ConfigManager:
    """Manages application configuration and data persistence."""

    def __init__(self, config_dir: Optional[Path] = None, data_dir: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Optional custom config directory
            data_dir: Optional custom data directory
        """
        # Use provided paths or defaults
        self.config_dir = config_dir or PlatformManager.get_default_config_dir()
        self.data_dir = data_dir or PlatformManager.get_default_data_dir()

        # Create directories if they don't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Define file paths
        self.app_settings_path = self.config_dir / "app_settings.json"
        self.user_prefs_path = self.config_dir / "user_preferences.json"
        self.categories_path = self.data_dir / "categories.json"

        self.sessions_dir = self.data_dir / "sessions"
        self.workflows_dir = self.data_dir / "workflows"

        # Create sub-directories
        self.sessions_dir.mkdir(exist_ok=True)
        self.workflows_dir.mkdir(exist_ok=True)

        # Cache for loaded config
        self._app_settings: Optional[Dict[str, Any]] = None
        self._user_prefs: Optional[Dict[str, Any]] = None

    def load_app_settings(self) -> Dict[str, Any]:
        """Load application settings.

        Returns:
            Application settings dictionary
        """
        if self._app_settings is not None:
            return self._app_settings

        if not self.app_settings_path.exists():
            # Create default settings
            self._app_settings = self._create_default_app_settings()
            self.save_app_settings(self._app_settings)
        else:
            with open(self.app_settings_path, 'r', encoding='utf-8') as f:
                self._app_settings = json.load(f)

        return self._app_settings

    def save_app_settings(self, settings: Dict[str, Any]):
        """Save application settings.

        Args:
            settings: Settings dictionary to save
        """
        with open(self.app_settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)

        self._app_settings = settings

    def get_app_path(self, app_name: str) -> Optional[str]:
        """Get configured executable path for an application.

        Args:
            app_name: Name of the application

        Returns:
            Configured path or None
        """
        settings = self.load_app_settings()
        app_config = settings.get('applications', {}).get(app_name, {})

        if not app_config:
            return None

        # Get path for current platform
        executable_paths = app_config.get('executable_path', {})

        if isinstance(executable_paths, str):
            # Old format compatibility
            return executable_paths

        return executable_paths.get(sys.platform)

    def set_app_path(self, app_name: str, path: str):
        """Set executable path for an application.

        Args:
            app_name: Name of the application
            path: Path to executable
        """
        settings = self.load_app_settings()

        if 'applications' not in settings:
            settings['applications'] = {}

        if app_name not in settings['applications']:
            settings['applications'][app_name] = {
                'executable_path': {}
            }

        settings['applications'][app_name]['executable_path'][sys.platform] = path

        self.save_app_settings(settings)

    def load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences.

        Returns:
            User preferences dictionary
        """
        if self._user_prefs is not None:
            return self._user_prefs

        if not self.user_prefs_path.exists():
            self._user_prefs = self._create_default_user_prefs()
            self.save_user_preferences(self._user_prefs)
        else:
            with open(self.user_prefs_path, 'r', encoding='utf-8') as f:
                self._user_prefs = json.load(f)

        return self._user_prefs

    def save_user_preferences(self, prefs: Dict[str, Any]):
        """Save user preferences.

        Args:
            prefs: Preferences dictionary to save
        """
        with open(self.user_prefs_path, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)

        self._user_prefs = prefs

    def load_categories(self) -> Dict[str, Any]:
        """Load category configuration.

        Returns:
            Categories dictionary
        """
        if not self.categories_path.exists():
            categories = self._create_default_categories()
            self.save_categories(categories)
            return categories

        with open(self.categories_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_categories(self, categories: Dict[str, Any]):
        """Save category configuration.

        Args:
            categories: Categories dictionary to save
        """
        with open(self.categories_path, 'w', encoding='utf-8') as f:
            json.dump(categories, f, indent=2, ensure_ascii=False)

    def list_sessions(self) -> List[Path]:
        """List all session files.

        Returns:
            List of session file paths
        """
        return list(self.sessions_dir.glob('*.json'))

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session dictionary or None if not found
        """
        session_path = self.sessions_dir / f"{session_id}.json"

        if not session_path.exists():
            return None

        with open(session_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """Save a session.

        Args:
            session_id: Session ID
            session_data: Session data dictionary
        """
        session_path = self.sessions_dir / f"{session_id}.json"

        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

    def delete_session(self, session_id: str):
        """Delete a session.

        Args:
            session_id: Session ID to delete
        """
        session_path = self.sessions_dir / f"{session_id}.json"

        if session_path.exists():
            session_path.unlink()

    def _create_default_app_settings(self) -> Dict[str, Any]:
        """Create default application settings.

        Returns:
            Default settings dictionary
        """
        return {
            "version": "3.0",
            "platform": sys.platform,
            "applications": {
                "chrome": {
                    "executable_path": {},
                    "default_profile": None,
                    "use_selenium": False,
                    "selenium_driver_path": None
                },
                "firefox": {
                    "executable_path": {},
                    "default_profile": None
                },
                "edge": {
                    "executable_path": {},
                    "default_profile": None
                }
            },
            "capture_settings": {
                "browser_capture_method": "native",
                "auto_detect_vscode_workspaces": True
            }
        }

    def _create_default_user_prefs(self) -> Dict[str, Any]:
        """Create default user preferences.

        Returns:
            Default preferences dictionary
        """
        return {
            "version": "3.0",
            "ui": {
                "theme": "system",
                "window_width": 600,
                "window_height": 700,
                "show_favorites": True,
                "default_category_expanded": True
            },
            "behavior": {
                "confirm_delete": True,
                "close_to_tray": False,
                "launch_on_startup": False
            }
        }

    def _create_default_categories(self) -> Dict[str, Any]:
        """Create default categories.

        Returns:
            Default categories dictionary
        """
        return {
            "version": "3.0",
            "categories": [
                {
                    "id": "uncategorized",
                    "name": "Uncategorized",
                    "icon": "📁",
                    "color": "#808080",
                    "parent_id": None,
                    "expanded": True,
                    "order": 999
                }
            ]
        }
