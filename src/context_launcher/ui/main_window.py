"""Main application window."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from pathlib import Path
import json

from ..core.config import ConfigManager
from ..core.session import Session, create_browser_session
from ..launchers import LaunchConfig, AppType, LauncherFactory
from ..utils.logger import get_logger
from .session_dialog import SessionDialog


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()

        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.sessions = []

        self.setWindowTitle("Context Launcher v3.0")
        self.setGeometry(100, 100, 600, 700)

        self._init_ui()
        self._load_sessions()

    def _init_ui(self):
        """Initialize UI components."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Context Launcher")
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Sessions label
        sessions_label = QLabel("Sessions:")
        layout.addWidget(sessions_label)

        # Session list
        self.session_list = QListWidget()
        self.session_list.itemDoubleClicked.connect(self._on_launch_clicked)
        layout.addWidget(self.session_list)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.launch_btn = QPushButton("Launch")
        self.launch_btn.clicked.connect(self._on_launch_clicked)
        button_layout.addWidget(self.launch_btn)

        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        button_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        button_layout.addWidget(self.delete_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        button_layout.addWidget(self.settings_btn)

        layout.addLayout(button_layout)

    def _load_sessions(self):
        """Load sessions from disk."""
        self.sessions.clear()
        session_files = self.config_manager.list_sessions()

        if not session_files:
            # Create some default sessions
            self._create_default_sessions()
            session_files = self.config_manager.list_sessions()

        for session_file in session_files:
            try:
                session_data = self.config_manager.load_session(session_file.stem)
                session = Session.from_dict(session_data)
                self.sessions.append(session)
            except Exception as e:
                self.logger.error(f"Failed to load session {session_file}: {e}")

        self._refresh_list()

    def _refresh_list(self):
        """Refresh the session list display."""
        self.session_list.clear()

        # Sort by name
        sorted_sessions = sorted(self.sessions, key=lambda s: s.name)

        for session in sorted_sessions:
            # Get tab count for display
            tabs = session.launch_config.parameters.get('tabs', [])
            tab_count = len(tabs)

            # Format display text
            display_text = f"{session.icon} {session.name} ({tab_count} tabs)"

            # Create list item
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, session)

            self.session_list.addItem(item)

    def _on_launch_clicked(self):
        """Handle launch button click."""
        current_item = self.session_list.currentItem()

        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a session to launch.")
            return

        session = current_item.data(Qt.ItemDataRole.UserRole)

        try:
            # Create launch config
            launch_config = LaunchConfig(
                app_type=AppType(session.launch_config.app_type),
                app_name=session.launch_config.app_name,
                parameters=session.launch_config.parameters,
                platform='win32'  # Will be auto-detected in future
            )

            # Create launcher
            launcher = LauncherFactory.create_launcher(launch_config)

            # Launch
            self.logger.info(f"Launching session: {session.name}")
            result = launcher.launch()

            if result.success:
                # Update stats
                session.update_launch_stats()
                self.config_manager.save_session(session.id, session.to_dict())

                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully launched {session.name}!\n\nProcess ID: {result.process_id}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Launch Failed",
                    f"Failed to launch {session.name}:\n\n{result.message}"
                )

        except Exception as e:
            self.logger.error(f"Launch error: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while launching:\n\n{str(e)}"
            )

    def _on_add_clicked(self):
        """Handle add button click."""
        dialog = SessionDialog(self)

        if dialog.exec():
            session = dialog.get_session()

            if session:
                self.sessions.append(session)
                self.config_manager.save_session(session.id, session.to_dict())
                self._refresh_list()

    def _on_edit_clicked(self):
        """Handle edit button click."""
        current_item = self.session_list.currentItem()

        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a session to edit.")
            return

        session = current_item.data(Qt.ItemDataRole.UserRole)
        dialog = SessionDialog(self, session)

        if dialog.exec():
            edited_session = dialog.get_session()

            if edited_session:
                # Replace in list
                idx = self.sessions.index(session)
                self.sessions[idx] = edited_session

                # Save
                self.config_manager.save_session(edited_session.id, edited_session.to_dict())
                self._refresh_list()

    def _on_delete_clicked(self):
        """Handle delete button click."""
        current_item = self.session_list.currentItem()

        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a session to delete.")
            return

        session = current_item.data(Qt.ItemDataRole.UserRole)

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{session.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.sessions.remove(session)
            self.config_manager.delete_session(session.id)
            self._refresh_list()

    def _on_settings_clicked(self):
        """Handle settings button click."""
        QMessageBox.information(
            self,
            "Settings",
            "Settings dialog will be implemented in Phase 2!"
        )

    def _create_default_sessions(self):
        """Create default example sessions."""
        # Example Chrome session
        example_session = create_browser_session(
            name="Example Browser Session",
            browser="chrome",
            tabs=[
                {"type": "url", "url": "https://www.google.com"},
                {"type": "url", "url": "https://www.github.com"},
            ],
            icon="🌐"
        )

        self.config_manager.save_session(example_session.id, example_session.to_dict())
