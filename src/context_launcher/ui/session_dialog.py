"""Session editor dialog with tabbed interface for different app types."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QMessageBox, QLabel, QWidget, QFileDialog
)
from PySide6.QtCore import Qt
from typing import Optional
from pathlib import Path

from ..core.session import (
    Session, create_browser_session, create_vscode_session,
    create_generic_app_session
)
from ..core.tab import TabsCollection


class SessionDialog(QDialog):
    """Dialog for creating/editing sessions with tabbed interface."""

    def __init__(self, parent=None, session: Optional[Session] = None,
                 tabs_collection: Optional[TabsCollection] = None,
                 default_tab_id: Optional[str] = None):
        """Initialize session dialog.

        Args:
            parent: Parent widget
            session: Optional session to edit (None for new session)
            tabs_collection: Collection of user-defined tabs
            default_tab_id: Default tab to select
        """
        super().__init__(parent)

        self.session = session
        self.editing = session is not None
        self.tabs_collection = tabs_collection
        self.default_tab_id = default_tab_id

        title = "Edit Session" if self.editing else "New Session"
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._init_ui()

        if self.editing:
            self._load_session_data()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Common fields (top section)
        common_layout = QFormLayout()

        self.name_edit = QLineEdit()
        common_layout.addRow("Name:", self.name_edit)

        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("🌐")
        common_layout.addRow("Icon (emoji):", self.icon_edit)

        # Tab/Category selection
        self.tab_combo = QComboBox()
        if self.tabs_collection:
            sorted_tabs = sorted(self.tabs_collection.tabs, key=lambda t: t.order)
            for tab in sorted_tabs:
                self.tab_combo.addItem(f"{tab.icon} {tab.name}", tab.id)

            # Set default selection
            if self.default_tab_id:
                for i in range(self.tab_combo.count()):
                    if self.tab_combo.itemData(i) == self.default_tab_id:
                        self.tab_combo.setCurrentIndex(i)
                        break

        common_layout.addRow("Category:", self.tab_combo)

        layout.addLayout(common_layout)

        # Tabbed interface for different app types
        self.tabs = QTabWidget()

        # Browser tab
        self.browser_tab = self._create_browser_tab()
        self.tabs.addTab(self.browser_tab, "🌐 Browser")

        # Editor tab
        self.editor_tab = self._create_editor_tab()
        self.tabs.addTab(self.editor_tab, "💻 Editor")

        # Apps tab
        self.apps_tab = self._create_apps_tab()
        self.tabs.addTab(self.apps_tab, "⚙️ Apps")

        # Generic tab
        self.generic_tab = self._create_generic_tab()
        self.tabs.addTab(self.generic_tab, "📦 Custom")

        layout.addWidget(self.tabs)

        # Dialog buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _create_browser_tab(self) -> QWidget:
        """Create browser configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Browser selection
        form_layout = QFormLayout()

        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["chrome", "firefox", "edge"])
        form_layout.addRow("Browser:", self.browser_combo)

        self.browser_profile_edit = QLineEdit()
        self.browser_profile_edit.setPlaceholderText("Leave empty for default profile")
        form_layout.addRow("Profile:", self.browser_profile_edit)

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

        self.add_tab_btn = QPushButton("Add")
        self.add_tab_btn.clicked.connect(self._add_browser_tab)
        tab_input_layout.addWidget(self.add_tab_btn)

        self.remove_tab_btn = QPushButton("Remove")
        self.remove_tab_btn.clicked.connect(self._remove_browser_tab)
        tab_input_layout.addWidget(self.remove_tab_btn)

        layout.addLayout(tab_input_layout)

        return widget

    def _create_editor_tab(self) -> QWidget:
        """Create editor configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form_layout = QFormLayout()

        # Editor selection
        self.editor_combo = QComboBox()
        self.editor_combo.addItems(["vscode"])  # Can add pycharm later
        form_layout.addRow("Editor:", self.editor_combo)

        # Workspace/Folder path
        workspace_layout = QHBoxLayout()
        self.workspace_edit = QLineEdit()
        self.workspace_edit.setPlaceholderText("Path to workspace or folder")
        workspace_layout.addWidget(self.workspace_edit)

        self.browse_workspace_btn = QPushButton("Browse...")
        self.browse_workspace_btn.clicked.connect(self._browse_workspace)
        workspace_layout.addWidget(self.browse_workspace_btn)

        form_layout.addRow("Workspace/Folder:", workspace_layout)

        layout.addLayout(form_layout)
        layout.addStretch()

        return widget

    def _create_apps_tab(self) -> QWidget:
        """Create apps configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form_layout = QFormLayout()

        # App selection
        self.app_combo = QComboBox()
        self.app_combo.addItems(["slack", "spotify"])
        form_layout.addRow("Application:", self.app_combo)

        layout.addLayout(form_layout)

        info_label = QLabel("Selected app will be auto-detected and launched.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addStretch()

        return widget

    def _create_generic_tab(self) -> QWidget:
        """Create generic/custom app configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form_layout = QFormLayout()

        # Executable path
        exe_layout = QHBoxLayout()
        self.executable_edit = QLineEdit()
        self.executable_edit.setPlaceholderText("Path to executable")
        exe_layout.addWidget(self.executable_edit)

        self.browse_exe_btn = QPushButton("Browse...")
        self.browse_exe_btn.clicked.connect(self._browse_executable)
        exe_layout.addWidget(self.browse_exe_btn)

        form_layout.addRow("Executable:", exe_layout)

        # Arguments
        self.arguments_edit = QLineEdit()
        self.arguments_edit.setPlaceholderText("Optional command-line arguments")
        form_layout.addRow("Arguments:", self.arguments_edit)

        # Working directory
        workdir_layout = QHBoxLayout()
        self.workdir_edit = QLineEdit()
        self.workdir_edit.setPlaceholderText("Optional working directory")
        workdir_layout.addWidget(self.workdir_edit)

        self.browse_workdir_btn = QPushButton("Browse...")
        self.browse_workdir_btn.clicked.connect(self._browse_workdir)
        workdir_layout.addWidget(self.browse_workdir_btn)

        form_layout.addRow("Working Dir:", workdir_layout)

        layout.addLayout(form_layout)
        layout.addStretch()

        return widget

    def _browse_workspace(self):
        """Browse for workspace/folder."""
        path = QFileDialog.getExistingDirectory(self, "Select Workspace or Folder")
        if path:
            self.workspace_edit.setText(path)

    def _browse_executable(self):
        """Browse for executable."""
        path, _ = QFileDialog.getOpenFileName(self, "Select Executable")
        if path:
            self.executable_edit.setText(path)

    def _browse_workdir(self):
        """Browse for working directory."""
        path = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if path:
            self.workdir_edit.setText(path)

    def _add_browser_tab(self):
        """Add a browser tab to the list."""
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

    def _remove_browser_tab(self):
        """Remove selected tab from list."""
        current_item = self.tabs_list.currentItem()
        if current_item:
            row = self.tabs_list.row(current_item)
            self.tabs_list.takeItem(row)

    def _load_session_data(self):
        """Load existing session data into UI."""
        if not self.session:
            return

        # Load common fields
        self.name_edit.setText(self.session.name)
        self.icon_edit.setText(self.session.icon)

        # Load category/tab selection
        session_tab_id = self.session.tab_id
        for i in range(self.tab_combo.count()):
            if self.tab_combo.itemData(i) == session_tab_id:
                self.tab_combo.setCurrentIndex(i)
                break

        # Determine which tab to show based on app type
        app_type = self.session.launch_config.app_type
        app_name = self.session.launch_config.app_name
        params = self.session.launch_config.parameters

        if app_type == "browser":
            self.tabs.setCurrentIndex(0)  # Browser tab

            # Load browser
            index = self.browser_combo.findText(app_name)
            if index >= 0:
                self.browser_combo.setCurrentIndex(index)

            # Load profile
            self.browser_profile_edit.setText(params.get('profile', ''))

            # Load tabs
            for tab_data in params.get('tabs', []):
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

        elif app_type == "editor":
            self.tabs.setCurrentIndex(1)  # Editor tab

            index = self.editor_combo.findText(app_name)
            if index >= 0:
                self.editor_combo.setCurrentIndex(index)

            self.workspace_edit.setText(params.get('workspace', '') or params.get('folder', ''))

        elif app_name in ["slack", "spotify"]:
            self.tabs.setCurrentIndex(2)  # Apps tab

            index = self.app_combo.findText(app_name)
            if index >= 0:
                self.app_combo.setCurrentIndex(index)

        else:  # Generic
            self.tabs.setCurrentIndex(3)  # Generic tab

            self.executable_edit.setText(params.get('executable_path', ''))

            args = params.get('arguments', [])
            if isinstance(args, list):
                self.arguments_edit.setText(' '.join(args))
            else:
                self.arguments_edit.setText(str(args))

            self.workdir_edit.setText(params.get('working_directory', ''))

    def get_session(self) -> Optional[Session]:
        """Get the session from dialog inputs based on active tab.

        Returns:
            Session instance or None if validation fails
        """
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Session name is required.")
            return None

        icon = self.icon_edit.text().strip() or "🌐"

        # Determine session type based on active tab
        current_tab_index = self.tabs.currentIndex()

        if current_tab_index == 0:  # Browser
            return self._create_browser_session(name, icon)
        elif current_tab_index == 1:  # Editor
            return self._create_editor_session(name, icon)
        elif current_tab_index == 2:  # Apps
            return self._create_app_session(name, icon)
        else:  # Generic
            return self._create_generic_session(name, icon)

    def _create_browser_session(self, name: str, icon: str) -> Optional[Session]:
        """Create browser session from inputs."""
        browser = self.browser_combo.currentText()
        profile = self.browser_profile_edit.text().strip()

        # Get selected tab_id
        tab_id = self.tab_combo.currentData() or "uncategorized"

        # Get tabs
        tabs = []
        for i in range(self.tabs_list.count()):
            item = self.tabs_list.item(i)
            tab_data = item.data(Qt.ItemDataRole.UserRole)
            tabs.append(tab_data)

        if self.editing and self.session:
            # Update existing session
            self.session.name = name
            self.session.icon = icon
            self.session.tab_id = tab_id
            self.session.launch_config.app_name = browser
            self.session.launch_config.parameters['profile'] = profile
            self.session.launch_config.parameters['tabs'] = tabs
            return self.session
        else:
            return create_browser_session(
                name=name,
                browser=browser,
                tabs=tabs,
                icon=icon,
                profile=profile,
                tab_id=tab_id
            )

    def _create_editor_session(self, name: str, icon: str) -> Optional[Session]:
        """Create editor session from inputs."""
        editor = self.editor_combo.currentText()
        workspace = self.workspace_edit.text().strip()

        # Get selected tab_id
        tab_id = self.tab_combo.currentData() or "uncategorized"

        if not workspace:
            QMessageBox.warning(self, "Invalid Input", "Workspace/Folder path is required.")
            return None

        if self.editing and self.session:
            # Update existing session
            self.session.name = name
            self.session.icon = icon
            self.session.tab_id = tab_id
            self.session.launch_config.app_name = editor
            self.session.launch_config.parameters['workspace'] = workspace
            return self.session
        else:
            return create_vscode_session(
                name=name,
                workspace_path=workspace,
                icon=icon,
                tab_id=tab_id
            )

    def _create_app_session(self, name: str, icon: str) -> Optional[Session]:
        """Create app session from inputs."""
        app = self.app_combo.currentText()

        # Get selected tab_id
        tab_id = self.tab_combo.currentData() or "uncategorized"

        if self.editing and self.session:
            # Update existing session
            self.session.name = name
            self.session.icon = icon
            self.session.tab_id = tab_id
            self.session.launch_config.app_name = app
            return self.session
        else:
            return create_generic_app_session(
                name=name,
                app_name=app,
                executable_path="",  # Will be auto-detected
                icon=icon,
                tab_id=tab_id
            )

    def _create_generic_session(self, name: str, icon: str) -> Optional[Session]:
        """Create generic session from inputs."""
        executable = self.executable_edit.text().strip()

        # Get selected tab_id
        tab_id = self.tab_combo.currentData() or "uncategorized"

        if not executable:
            QMessageBox.warning(self, "Invalid Input", "Executable path is required.")
            return None

        args_text = self.arguments_edit.text().strip()
        arguments = args_text.split() if args_text else []

        workdir = self.workdir_edit.text().strip() or None

        if self.editing and self.session:
            # Update existing session
            self.session.name = name
            self.session.icon = icon
            self.session.tab_id = tab_id
            self.session.launch_config.parameters['executable_path'] = executable
            self.session.launch_config.parameters['arguments'] = arguments
            self.session.launch_config.parameters['working_directory'] = workdir
            return self.session
        else:
            session = create_generic_app_session(
                name=name,
                app_name="generic",
                executable_path=executable,
                arguments=arguments,
                icon=icon,
                tab_id=tab_id
            )
            if workdir:
                session.launch_config.parameters['working_directory'] = workdir
            return session
