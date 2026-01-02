"""Session editor dialog."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from typing import Optional

from ..core.session import Session, Tab, TabType, create_browser_session


class SessionDialog(QDialog):
    """Dialog for creating/editing sessions."""

    def __init__(self, parent=None, session: Optional[Session] = None):
        """Initialize session dialog.

        Args:
            parent: Parent widget
            session: Optional session to edit (None for new session)
        """
        super().__init__(parent)

        self.session = session
        self.editing = session is not None

        title = "Edit Session" if self.editing else "New Session"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        self._init_ui()

        if self.editing:
            self._load_session_data()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form for basic info
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)

        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("🌐")
        form_layout.addRow("Icon (emoji):", self.icon_edit)

        # Browser selection
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["chrome", "firefox", "edge"])
        form_layout.addRow("Browser:", self.browser_combo)

        # Profile
        self.profile_edit = QLineEdit()
        self.profile_edit.setPlaceholderText("Leave empty for default profile")
        form_layout.addRow("Profile:", self.profile_edit)

        layout.addLayout(form_layout)

        # Tabs section
        tabs_label = QLabel("Tabs:")
        layout.addWidget(tabs_label)

        self.tabs_list = QListWidget()
        layout.addWidget(self.tabs_list)

        # Tab input
        tab_input_layout = QHBoxLayout()

        self.tab_type_combo = QComboBox()
        self.tab_type_combo.addItems(["URL", "YouTube Channel"])
        tab_input_layout.addWidget(self.tab_type_combo)

        self.tab_input = QLineEdit()
        self.tab_input.setPlaceholderText("Enter URL or @channel_handle")
        tab_input_layout.addWidget(self.tab_input, stretch=1)

        self.add_tab_btn = QPushButton("Add Tab")
        self.add_tab_btn.clicked.connect(self._add_tab)
        tab_input_layout.addWidget(self.add_tab_btn)

        self.remove_tab_btn = QPushButton("Remove")
        self.remove_tab_btn.clicked.connect(self._remove_tab)
        tab_input_layout.addWidget(self.remove_tab_btn)

        layout.addLayout(tab_input_layout)

        # Dialog buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _load_session_data(self):
        """Load existing session data into UI."""
        if not self.session:
            return

        self.name_edit.setText(self.session.name)
        self.icon_edit.setText(self.session.icon)

        # Load browser
        browser = self.session.launch_config.app_name
        index = self.browser_combo.findText(browser)
        if index >= 0:
            self.browser_combo.setCurrentIndex(index)

        # Load profile
        profile = self.session.launch_config.parameters.get('profile', '')
        self.profile_edit.setText(profile)

        # Load tabs
        tabs = self.session.launch_config.parameters.get('tabs', [])
        for tab_data in tabs:
            tab_type = tab_data.get('type', 'url')
            if tab_type == 'url':
                url = tab_data.get('url', '')
                item = QListWidgetItem(f"🔗 {url}")
                item.setData(Qt.ItemDataRole.UserRole, tab_data)
                self.tabs_list.addItem(item)
            elif tab_type == 'youtube':
                handle = tab_data.get('channelHandle', '')
                item = QListWidgetItem(f"📺 {handle}")
                item.setData(Qt.ItemDataRole.UserRole, tab_data)
                self.tabs_list.addItem(item)

    def _add_tab(self):
        """Add a tab to the list."""
        tab_value = self.tab_input.text().strip()

        if not tab_value:
            QMessageBox.warning(self, "Empty Input", "Please enter a URL or channel handle.")
            return

        tab_type_text = self.tab_type_combo.currentText()

        if tab_type_text == "URL":
            # Auto-prefix with https:// if needed
            if not tab_value.startswith(('http://', 'https://')):
                tab_value = 'https://' + tab_value

            tab_data = {
                'type': 'url',
                'url': tab_value
            }

            item = QListWidgetItem(f"🔗 {tab_value}")
            item.setData(Qt.ItemDataRole.UserRole, tab_data)
            self.tabs_list.addItem(item)

        else:  # YouTube Channel
            # Auto-prefix with @ if needed
            if not tab_value.startswith('@'):
                tab_value = '@' + tab_value

            tab_data = {
                'type': 'youtube',
                'channelHandle': tab_value
            }

            item = QListWidgetItem(f"📺 {tab_value}")
            item.setData(Qt.ItemDataRole.UserRole, tab_data)
            self.tabs_list.addItem(item)

        # Clear input
        self.tab_input.clear()

    def _remove_tab(self):
        """Remove selected tab from list."""
        current_item = self.tabs_list.currentItem()

        if current_item:
            row = self.tabs_list.row(current_item)
            self.tabs_list.takeItem(row)

    def get_session(self) -> Optional[Session]:
        """Get the session from dialog inputs.

        Returns:
            Session instance or None if validation fails
        """
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Session name is required.")
            return None

        icon = self.icon_edit.text().strip() or "🌐"
        browser = self.browser_combo.currentText()
        profile = self.profile_edit.text().strip()

        # Get tabs
        tabs = []
        for i in range(self.tabs_list.count()):
            item = self.tabs_list.item(i)
            tab_data = item.data(Qt.ItemDataRole.UserRole)
            tabs.append(tab_data)

        # Create or update session
        if self.editing and self.session:
            # Update existing session
            self.session.name = name
            self.session.icon = icon
            self.session.launch_config.app_name = browser
            self.session.launch_config.parameters['profile'] = profile
            self.session.launch_config.parameters['tabs'] = tabs
            return self.session
        else:
            # Create new session
            return create_browser_session(
                name=name,
                browser=browser,
                tabs=tabs,
                icon=icon,
                profile=profile
            )
