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
        self.tabs_path = self.data_dir / "tabs.json"  # New: user-defined tabs

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

    def list_workflows(self) -> List[Path]:
        """List all workflow files.

        Returns:
            List of workflow file paths
        """
        return list(self.workflows_dir.glob('*.json'))

    def load_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load a workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow dictionary or None if not found
        """
        workflow_path = self.workflows_dir / f"{workflow_id}.json"

        if not workflow_path.exists():
            return None

        with open(workflow_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]):
        """Save a workflow.

        Args:
            workflow_id: Workflow ID
            workflow_data: Workflow data dictionary
        """
        workflow_path = self.workflows_dir / f"{workflow_id}.json"

        with open(workflow_path, 'w', encoding='utf-8') as f:
            json.dump(workflow_data, f, indent=2, ensure_ascii=False)

    def delete_workflow(self, workflow_id: str):
        """Delete a workflow.

        Args:
            workflow_id: Workflow ID to delete
        """
        workflow_path = self.workflows_dir / f"{workflow_id}.json"

        if workflow_path.exists():
            workflow_path.unlink()

    def load_tabs(self) -> Dict[str, Any]:
        """Load user-defined tabs.

        Returns:
            Tabs dictionary
        """
        if not self.tabs_path.exists():
            tabs = self._create_default_tabs()
            self.save_tabs(tabs)
            return tabs

        with open(self.tabs_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_tabs(self, tabs_data: Dict[str, Any]):
        """Save user-defined tabs.

        Args:
            tabs_data: Tabs data dictionary
        """
        with open(self.tabs_path, 'w', encoding='utf-8') as f:
            json.dump(tabs_data, f, indent=2, ensure_ascii=False)

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
                "window_width": 500,
                "window_height": 600,
                "window_x": 100,
                "window_y": 100,
                "remember_window_size": True,
                "remember_window_position": True,
                "show_favorites": True,
                "default_category_expanded": True,
                "view_mode": "tree"  # "tree" or "tabs"
            },
            "behavior": {
                "confirm_delete": True,
                "close_to_tray": False,
                "launch_on_startup": False,
                "use_app_icons_by_default": True
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

    def _get_platform_template_name(self) -> str:
        """Get the platform-specific template suffix.

        Returns:
            Platform suffix (e.g., 'darwin', 'windows')
        """
        if sys.platform == 'darwin':
            return 'darwin'
        elif sys.platform == 'win32':
            return 'windows'
        else:
            return 'linux'

    def _create_default_tabs(self) -> Dict[str, Any]:
        """Create default tabs from platform-specific template file.

        Returns:
            Default tabs dictionary
        """
        templates_dir = Path(__file__).parent.parent / "templates"
        platform_name = self._get_platform_template_name()
        
        # Try platform-specific template first
        platform_template = templates_dir / f"default_tabs_{platform_name}.json"
        generic_template = templates_dir / "default_tabs.json"
        
        template_path = platform_template if platform_template.exists() else generic_template

        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Fallback to hardcoded defaults if template not found
            from .tab import create_default_tabs
            tabs_collection = create_default_tabs()
            return tabs_collection.to_dict()

    def load_default_sessions_template(self) -> List[Dict[str, Any]]:
        """Load default sessions from platform-specific template file.

        Returns:
            List of session dictionaries
        """
        templates_dir = Path(__file__).parent.parent / "templates"
        platform_name = self._get_platform_template_name()
        
        # Try platform-specific template first
        platform_template = templates_dir / f"default_sessions_{platform_name}.json"
        generic_template = templates_dir / "default_sessions.json"
        
        template_path = platform_template if platform_template.exists() else generic_template

        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('sessions', [])
        else:
            # Return empty list if no template
            return []

    def reset_to_defaults(self, backup_first: bool = True) -> Optional[Path]:
        """Reset all user data to defaults.
        
        Args:
            backup_first: Whether to create a backup before resetting
            
        Returns:
            Path to backup file if created, None otherwise
        """
        import shutil
        from datetime import datetime
        
        backup_path = None
        
        if backup_first:
            # Create backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.data_dir / f"backup_before_reset_{timestamp}.zip"
            
            try:
                # Create ZIP backup of data directory
                import zipfile
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Backup tabs.json
                    if self.tabs_path.exists():
                        zipf.write(self.tabs_path, "tabs.json")
                    
                    # Backup sessions
                    for session_file in self.sessions_dir.glob('*.json'):
                        zipf.write(session_file, f"sessions/{session_file.name}")
                    
                    # Backup workflows
                    for workflow_file in self.workflows_dir.glob('*.json'):
                        zipf.write(workflow_file, f"workflows/{workflow_file.name}")
                    
                    # Backup user preferences
                    if self.user_prefs_path.exists():
                        zipf.write(self.user_prefs_path, "user_preferences.json")
            except Exception as e:
                # If backup fails, don't proceed with reset
                raise RuntimeError(f"Failed to create backup: {e}")
        
        # Delete existing data
        if self.tabs_path.exists():
            self.tabs_path.unlink()
        
        # Delete all sessions
        for session_file in self.sessions_dir.glob('*.json'):
            session_file.unlink()
        
        # Delete all workflows
        for workflow_file in self.workflows_dir.glob('*.json'):
            workflow_file.unlink()
        
        # Clear caches
        self._app_settings = None
        self._user_prefs = None
        
        return backup_path

    def get_backup_files(self) -> List[Path]:
        """Get list of backup files in data directory.
        
        Returns:
            List of backup file paths
        """
        return sorted(self.data_dir.glob('backup_*.zip'), reverse=True)
