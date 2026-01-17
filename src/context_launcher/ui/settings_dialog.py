"""Settings dialog for managing global application preferences."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QCheckBox, QComboBox, QGroupBox, QLabel,
    QMessageBox
)
from PySide6.QtCore import Qt

from ..core.config import ConfigManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """Dialog for managing global application settings."""

    def __init__(self, parent=None, config_manager: ConfigManager = None):
        """Initialize settings dialog.

        Args:
            parent: Parent widget
            config_manager: Configuration manager instance
        """
        super().__init__(parent)
        self.config_manager = config_manager or ConfigManager()
        self.prefs = self.config_manager.load_user_preferences()

        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        self.setMinimumHeight(350)

        self._init_ui()
        self._load_current_settings()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Window settings group
        window_group = QGroupBox("Window")
        window_layout = QFormLayout(window_group)

        self.remember_size_checkbox = QCheckBox("Remember window size")
        self.remember_size_checkbox.setToolTip(
            "Save the window size when closing and restore it on next launch"
        )
        window_layout.addRow(self.remember_size_checkbox)

        self.remember_position_checkbox = QCheckBox("Remember window position")
        self.remember_position_checkbox.setToolTip(
            "Save the window position when closing and restore it on next launch"
        )
        window_layout.addRow(self.remember_position_checkbox)

        layout.addWidget(window_group)

        # Appearance settings group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("System Default", "system")
        self.theme_combo.addItem("Dark", "dark")
        appearance_layout.addRow("Theme:", self.theme_combo)

        self.show_favorites_checkbox = QCheckBox("Show favorites section")
        self.show_favorites_checkbox.setToolTip(
            "Display a special section for favorite sessions and workflows"
        )
        appearance_layout.addRow(self.show_favorites_checkbox)

        self.default_expanded_checkbox = QCheckBox("Expand categories by default")
        self.default_expanded_checkbox.setToolTip(
            "New categories will be expanded by default in tree view"
        )
        appearance_layout.addRow(self.default_expanded_checkbox)

        layout.addWidget(appearance_group)

        # Behavior settings group
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QFormLayout(behavior_group)

        self.confirm_delete_checkbox = QCheckBox("Confirm before deleting")
        self.confirm_delete_checkbox.setToolTip(
            "Show a confirmation dialog before deleting sessions, workflows, or categories"
        )
        behavior_layout.addRow(self.confirm_delete_checkbox)

        self.use_app_icons_checkbox = QCheckBox("Use application icons by default")
        self.use_app_icons_checkbox.setToolTip(
            "When creating new sessions, use the application's icon instead of emoji"
        )
        behavior_layout.addRow(self.use_app_icons_checkbox)

        layout.addWidget(behavior_group)

        # Data Management group
        data_group = QGroupBox("Data Management")
        data_layout = QVBoxLayout(data_group)

        # Reset to defaults button
        reset_layout = QHBoxLayout()
        reset_label = QLabel("Reset all categories and sessions to platform defaults:")
        reset_label.setWordWrap(True)
        reset_layout.addWidget(reset_label)
        reset_layout.addStretch()
        
        self.reset_btn = QPushButton("🔄 Reset to Defaults")
        self.reset_btn.setToolTip(
            "Delete all user data and restore default categories and sessions.\n"
            "A backup will be created automatically before reset."
        )
        self.reset_btn.clicked.connect(self._on_reset_to_defaults)
        self.reset_btn.setStyleSheet("QPushButton { color: #cc0000; }")
        reset_layout.addWidget(self.reset_btn)
        
        data_layout.addLayout(reset_layout)

        # Show data location
        data_path_label = QLabel(f"Data location: {self.config_manager.data_dir}")
        data_path_label.setStyleSheet("color: gray; font-size: 10px;")
        data_path_label.setWordWrap(True)
        data_layout.addWidget(data_path_label)

        layout.addWidget(data_group)

        # Spacer
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _load_current_settings(self):
        """Load current settings into the UI."""
        ui_prefs = self.prefs.get('ui', {})
        behavior_prefs = self.prefs.get('behavior', {})

        # Window settings
        self.remember_size_checkbox.setChecked(ui_prefs.get('remember_window_size', True))
        self.remember_position_checkbox.setChecked(ui_prefs.get('remember_window_position', True))

        # Appearance settings
        theme = ui_prefs.get('theme', 'system')
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        self.show_favorites_checkbox.setChecked(ui_prefs.get('show_favorites', True))
        self.default_expanded_checkbox.setChecked(ui_prefs.get('default_category_expanded', True))

        # Behavior settings
        self.confirm_delete_checkbox.setChecked(behavior_prefs.get('confirm_delete', True))
        self.use_app_icons_checkbox.setChecked(behavior_prefs.get('use_app_icons_by_default', True))

    def _save_settings(self):
        """Save settings to configuration."""
        # Ensure structure exists
        if 'ui' not in self.prefs:
            self.prefs['ui'] = {}
        if 'behavior' not in self.prefs:
            self.prefs['behavior'] = {}

        # Window settings
        self.prefs['ui']['remember_window_size'] = self.remember_size_checkbox.isChecked()
        self.prefs['ui']['remember_window_position'] = self.remember_position_checkbox.isChecked()

        # Appearance settings
        self.prefs['ui']['theme'] = self.theme_combo.currentData()
        self.prefs['ui']['show_favorites'] = self.show_favorites_checkbox.isChecked()
        self.prefs['ui']['default_category_expanded'] = self.default_expanded_checkbox.isChecked()

        # Behavior settings
        self.prefs['behavior']['confirm_delete'] = self.confirm_delete_checkbox.isChecked()
        self.prefs['behavior']['use_app_icons_by_default'] = self.use_app_icons_checkbox.isChecked()

        # Save to disk
        self.config_manager.save_user_preferences(self.prefs)

        self.accept()

    def _on_reset_to_defaults(self):
        """Handle reset to defaults button click."""
        # First confirmation
        reply = QMessageBox.warning(
            self,
            "⚠️ Reset to Defaults",
            "This will DELETE all your categories, sessions, and workflows!\n\n"
            "A backup will be created automatically before reset.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Second confirmation (because this is destructive)
        reply2 = QMessageBox.critical(
            self,
            "🚨 Final Confirmation",
            "This action cannot be undone (except by restoring from backup).\n\n"
            "ALL your data will be replaced with platform defaults.\n\n"
            "Are you ABSOLUTELY sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply2 != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Perform reset with backup
            backup_path = self.config_manager.reset_to_defaults(backup_first=True)
            
            logger.info(f"Reset to defaults completed. Backup created at: {backup_path}")
            
            QMessageBox.information(
                self,
                "Reset Complete",
                f"Successfully reset to defaults!\n\n"
                f"📦 Backup created at:\n{backup_path}\n\n"
                "Please restart the application to see the changes.",
            )
            
            # Close the settings dialog
            self.accept()
            
            # Signal that app needs restart (parent window should handle this)
            # We mark in prefs that a restart is needed
            self.prefs['_needs_restart'] = True
            
        except Exception as e:
            logger.error(f"Reset to defaults failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Reset Failed",
                f"Failed to reset to defaults:\n\n{str(e)}\n\n"
                "Your data has NOT been modified."
            )

    def get_preferences(self):
        """Get the current preferences dict.

        Returns:
            Preferences dictionary
        """
        return self.prefs
