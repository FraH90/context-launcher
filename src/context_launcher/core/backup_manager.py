"""Backup and restore functionality for sessions, workflows, and settings."""

import json
import zipfile
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime


class BackupManager:
    """Manages import/export and backup/restore of application data."""

    def __init__(self, config_manager):
        """Initialize backup manager.

        Args:
            config_manager: ConfigManager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger("context_launcher.BackupManager")

    def create_backup(self, backup_path: Path) -> bool:
        """Create a complete backup ZIP of all data.

        Args:
            backup_path: Path to save the backup ZIP file

        Returns:
            True if successful, False otherwise
        """
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add metadata
                metadata = {
                    "version": "3.0",
                    "created_at": datetime.now().isoformat(),
                    "backup_type": "complete"
                }
                zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

                # Add app settings
                if self.config_manager.app_settings_path.exists():
                    zipf.write(
                        self.config_manager.app_settings_path,
                        "config/app_settings.json"
                    )

                # Add user preferences
                if self.config_manager.user_prefs_path.exists():
                    zipf.write(
                        self.config_manager.user_prefs_path,
                        "config/user_preferences.json"
                    )

                # Add categories/tabs
                if self.config_manager.tabs_path.exists():
                    zipf.write(
                        self.config_manager.tabs_path,
                        "data/tabs.json"
                    )

                # Add all sessions
                for session_file in self.config_manager.list_sessions():
                    zipf.write(
                        session_file,
                        f"sessions/{session_file.name}"
                    )

                # Add all workflows
                for workflow_file in self.config_manager.list_workflows():
                    zipf.write(
                        workflow_file,
                        f"workflows/{workflow_file.name}"
                    )

            self.logger.info(f"Backup created successfully: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}", exc_info=e)
            return False

    def restore_backup(self, backup_path: Path, merge: bool = False) -> bool:
        """Restore from a backup ZIP file.

        Args:
            backup_path: Path to the backup ZIP file
            merge: If True, merge with existing data; if False, replace

        Returns:
            True if successful, False otherwise
        """
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False

            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Read metadata
                try:
                    metadata_str = zipf.read("metadata.json").decode('utf-8')
                    metadata = json.loads(metadata_str)
                    self.logger.info(f"Restoring backup from {metadata.get('created_at')}")
                except KeyError:
                    self.logger.warning("No metadata found in backup")

                # If not merging, clear existing data
                if not merge:
                    self._clear_all_data()

                # Restore app settings
                try:
                    settings_data = zipf.read("config/app_settings.json").decode('utf-8')
                    settings = json.loads(settings_data)
                    self.config_manager.save_app_settings(settings)
                except KeyError:
                    self.logger.warning("No app settings in backup")

                # Restore user preferences
                try:
                    prefs_data = zipf.read("config/user_preferences.json").decode('utf-8')
                    prefs = json.loads(prefs_data)
                    self.config_manager.save_user_preferences(prefs)
                except KeyError:
                    self.logger.warning("No user preferences in backup")

                # Restore tabs
                try:
                    tabs_data = zipf.read("data/tabs.json").decode('utf-8')
                    tabs = json.loads(tabs_data)
                    self.config_manager.save_tabs(tabs)
                except KeyError:
                    self.logger.warning("No tabs in backup")

                # Restore sessions
                session_files = [f for f in zipf.namelist() if f.startswith('sessions/')]
                for session_file in session_files:
                    session_data = zipf.read(session_file).decode('utf-8')
                    session = json.loads(session_data)
                    session_id = Path(session_file).stem
                    self.config_manager.save_session(session_id, session)

                # Restore workflows
                workflow_files = [f for f in zipf.namelist() if f.startswith('workflows/')]
                for workflow_file in workflow_files:
                    workflow_data = zipf.read(workflow_file).decode('utf-8')
                    workflow = json.loads(workflow_data)
                    workflow_id = Path(workflow_file).stem
                    self.config_manager.save_workflow(workflow_id, workflow)

            self.logger.info(f"Backup restored successfully from: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}", exc_info=e)
            return False

    def export_sessions(self, session_ids: List[str], export_path: Path) -> bool:
        """Export specific sessions to a ZIP file.

        Args:
            session_ids: List of session IDs to export
            export_path: Path to save the export ZIP file

        Returns:
            True if successful, False otherwise
        """
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add metadata
                metadata = {
                    "version": "3.0",
                    "created_at": datetime.now().isoformat(),
                    "backup_type": "sessions_export",
                    "session_count": len(session_ids)
                }
                zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

                # Add sessions
                for session_id in session_ids:
                    session_data = self.config_manager.load_session(session_id)
                    if session_data:
                        zipf.writestr(
                            f"sessions/{session_id}.json",
                            json.dumps(session_data, indent=2, ensure_ascii=False)
                        )

            self.logger.info(f"Exported {len(session_ids)} sessions to: {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export sessions: {e}", exc_info=e)
            return False

    def export_workflows(self, workflow_ids: List[str], export_path: Path) -> bool:
        """Export specific workflows to a ZIP file.

        Args:
            workflow_ids: List of workflow IDs to export
            export_path: Path to save the export ZIP file

        Returns:
            True if successful, False otherwise
        """
        try:
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add metadata
                metadata = {
                    "version": "3.0",
                    "created_at": datetime.now().isoformat(),
                    "backup_type": "workflows_export",
                    "workflow_count": len(workflow_ids)
                }
                zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

                # Add workflows
                for workflow_id in workflow_ids:
                    workflow_data = self.config_manager.load_workflow(workflow_id)
                    if workflow_data:
                        zipf.writestr(
                            f"workflows/{workflow_id}.json",
                            json.dumps(workflow_data, indent=2, ensure_ascii=False)
                        )

            self.logger.info(f"Exported {len(workflow_ids)} workflows to: {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export workflows: {e}", exc_info=e)
            return False

    def import_from_zip(self, import_path: Path) -> bool:
        """Import sessions/workflows from a ZIP file (merge with existing).

        Args:
            import_path: Path to the import ZIP file

        Returns:
            True if successful, False otherwise
        """
        # Use restore_backup with merge=True
        return self.restore_backup(import_path, merge=True)

    def _clear_all_data(self):
        """Clear all existing sessions and workflows."""
        # Delete all sessions
        for session_file in self.config_manager.list_sessions():
            session_file.unlink()

        # Delete all workflows
        for workflow_file in self.config_manager.list_workflows():
            workflow_file.unlink()

        self.logger.info("Cleared all existing data")
