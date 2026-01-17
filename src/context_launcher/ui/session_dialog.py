"""Session editor dialog with tabbed interface for different app types."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QMessageBox, QLabel, QWidget, QFileDialog, QCheckBox
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

        # Common fields (top section) - all in one row
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(10)

        # Name field
        name_container = QVBoxLayout()
        name_container.setSpacing(2)
        name_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        name_label = QLabel("Name:")
        name_container.addWidget(name_label)
        self.name_edit = QLineEdit()
        name_container.addWidget(self.name_edit)
        fields_layout.addLayout(name_container, stretch=1)

        # Icon field
        icon_container = QVBoxLayout()
        icon_container.setSpacing(2)
        icon_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        icon_label = QLabel("Icon:")
        icon_container.addWidget(icon_label)

        # Icon input with checkbox for auto app icon
        icon_input_layout = QVBoxLayout()
        icon_input_layout.setSpacing(2)

        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("🌐 or emoji")
        icon_input_layout.addWidget(self.icon_edit)

        self.use_app_icon_checkbox = QCheckBox("Use app icon")
        self.use_app_icon_checkbox.setToolTip("Automatically use the application's icon instead of emoji")
        self.use_app_icon_checkbox.stateChanged.connect(self._on_use_app_icon_changed)
        icon_input_layout.addWidget(self.use_app_icon_checkbox)

        icon_container.addLayout(icon_input_layout)
        fields_layout.addLayout(icon_container, stretch=1)

        # Category field
        category_container = QVBoxLayout()
        category_container.setSpacing(2)
        category_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        category_label = QLabel("Category:")
        category_container.addWidget(category_label)
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
        category_container.addWidget(self.tab_combo)

        # Match the height of text fields to the combobox
        combo_height = self.tab_combo.sizeHint().height()
        self.name_edit.setMinimumHeight(combo_height)
        self.icon_edit.setMinimumHeight(combo_height)

        fields_layout.addLayout(category_container, stretch=1)

        layout.addLayout(fields_layout)

        # Tabbed interface for different app types
        self.tabs = QTabWidget()

        # Browser tab
        self.browser_tab = self._create_browser_tab()
        self.tabs.addTab(self.browser_tab, "🌐 Browser")

        # Custom Apps tab (combines Editor, Apps + Custom)
        self.custom_apps_tab = self._create_custom_apps_tab()
        self.tabs.addTab(self.custom_apps_tab, "📦 Custom Apps")

        layout.addWidget(self.tabs)

        # Dialog buttons
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _create_browser_tab(self) -> QWidget:
        """Create browser configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Browser and Profile in the same row
        browser_layout = QHBoxLayout()
        browser_layout.setSpacing(10)

        # Browser field
        browser_container = QVBoxLayout()
        browser_container.setSpacing(2)
        browser_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        browser_label = QLabel("Browser:")
        browser_container.addWidget(browser_label)
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["chrome", "firefox", "edge"])
        self.browser_combo.setSizePolicy(
            self.browser_combo.sizePolicy().horizontalPolicy(),
            self.browser_combo.sizePolicy().verticalPolicy()
        )
        browser_container.addWidget(self.browser_combo)
        browser_layout.addLayout(browser_container, stretch=1)

        # Profile field
        profile_container = QVBoxLayout()
        profile_container.setSpacing(2)
        profile_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        profile_label = QLabel("Profile:")
        profile_container.addWidget(profile_label)
        self.browser_profile_edit = QLineEdit()
        self.browser_profile_edit.setPlaceholderText("Leave empty for default profile")
        # Match the height of the combobox
        self.browser_profile_edit.setMinimumHeight(self.browser_combo.sizeHint().height())
        profile_container.addWidget(self.browser_profile_edit)
        browser_layout.addLayout(profile_container, stretch=1)

        layout.addLayout(browser_layout)

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

    def _create_custom_apps_tab(self) -> QWidget:
        """Create custom apps configuration tab (combines Apps + Custom)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Top section: Choose between known apps or custom executable
        choice_label = QLabel("Select a known application or specify a custom executable:")
        choice_label.setWordWrap(True)
        layout.addWidget(choice_label)

        # Horizontal layout for the two mutually exclusive options
        main_layout = QHBoxLayout()

        # LEFT SIDE: Known apps dropdown
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        known_apps_label = QLabel("<b>Known Applications</b>")
        left_layout.addWidget(known_apps_label)

        self.app_combo = QComboBox()
        self.app_combo.addItem("Select an app...", "")  # Default empty option
        self.app_combo.addItem("VS Code", "vscode")
        self.app_combo.addItem("Slack", "slack")
        self.app_combo.addItem("Spotify", "spotify")
        self.app_combo.currentIndexChanged.connect(self._on_app_combo_changed)
        left_layout.addWidget(self.app_combo)

        # Workspace field (shown only for VS Code)
        workspace_container = QHBoxLayout()
        self.workspace_edit = QLineEdit()
        self.workspace_edit.setPlaceholderText("Workspace or folder path")
        self.workspace_edit.setVisible(False)
        workspace_container.addWidget(self.workspace_edit)

        self.browse_workspace_btn = QPushButton("Browse...")
        self.browse_workspace_btn.clicked.connect(self._browse_workspace)
        self.browse_workspace_btn.setVisible(False)
        workspace_container.addWidget(self.browse_workspace_btn)

        left_layout.addLayout(workspace_container)

        info_label = QLabel("Selected app will be auto-detected and launched.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10pt;")
        left_layout.addWidget(info_label)

        left_layout.addStretch()

        main_layout.addWidget(left_widget, stretch=1)

        # CENTER: OR separator
        separator_widget = QWidget()
        separator_layout = QVBoxLayout(separator_widget)
        separator_layout.setContentsMargins(10, 0, 10, 0)
        or_label = QLabel("<b>OR</b>")
        or_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator_layout.addWidget(or_label)
        separator_layout.addStretch()
        main_layout.addWidget(separator_widget)

        # RIGHT SIDE: Custom executable fields
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        custom_label = QLabel("<b>Custom Executable</b>")
        right_layout.addWidget(custom_label)

        # Executable path
        exe_layout = QHBoxLayout()
        self.executable_edit = QLineEdit()
        self.executable_edit.setPlaceholderText("Path to executable")
        self.executable_edit.textChanged.connect(self._on_executable_changed)
        exe_layout.addWidget(self.executable_edit)

        self.browse_exe_btn = QPushButton("Browse...")
        self.browse_exe_btn.clicked.connect(self._browse_executable)
        exe_layout.addWidget(self.browse_exe_btn)

        right_layout.addLayout(exe_layout)

        right_layout.addStretch()

        main_layout.addWidget(right_widget, stretch=1)

        layout.addLayout(main_layout)

        # BOTTOM SECTION: Shared fields for both known apps and custom executables
        layout.addSpacing(15)

        # Separator line
        separator_line = QLabel()
        separator_line.setFrameStyle(QLabel.Shape.HLine | QLabel.Shadow.Sunken)
        layout.addWidget(separator_line)

        shared_label = QLabel("<b>Optional Configuration (applies to both known apps and custom executables)</b>")
        shared_label.setWordWrap(True)
        layout.addWidget(shared_label)

        shared_form = QFormLayout()

        # Arguments
        self.arguments_edit = QLineEdit()
        self.arguments_edit.setPlaceholderText("Optional command-line arguments")
        shared_form.addRow("Arguments:", self.arguments_edit)

        # Working directory
        workdir_layout = QHBoxLayout()
        self.workdir_edit = QLineEdit()
        self.workdir_edit.setPlaceholderText("Optional working directory")
        workdir_layout.addWidget(self.workdir_edit)

        self.browse_workdir_btn = QPushButton("Browse...")
        self.browse_workdir_btn.clicked.connect(self._browse_workdir)
        workdir_layout.addWidget(self.browse_workdir_btn)

        shared_form.addRow("Working Dir:", workdir_layout)

        layout.addLayout(shared_form)
        layout.addStretch()

        return widget

    def _on_app_combo_changed(self, index: int):
        """Handle app combo selection - clear custom executable if app is selected."""
        selected_app = self.app_combo.currentData()

        if selected_app:  # If a known app is selected
            self.executable_edit.clear()
            # Don't clear arguments_edit and workdir_edit - they can be used for known apps too

            # Show workspace field only for VS Code
            is_vscode = selected_app == "vscode"
            self.workspace_edit.setVisible(is_vscode)
            self.browse_workspace_btn.setVisible(is_vscode)
        else:
            # No app selected, hide workspace field
            self.workspace_edit.setVisible(False)
            self.browse_workspace_btn.setVisible(False)

    def _on_executable_changed(self, text: str):
        """Handle executable path change - clear app combo if custom path is entered."""
        if text.strip():  # If custom path is entered
            self.app_combo.setCurrentIndex(0)  # Reset to "Select an app..."

    def _on_use_app_icon_changed(self, state: int):
        """Handle use app icon checkbox change."""
        if state:  # Checked
            self.icon_edit.setEnabled(False)
            self.icon_edit.setPlaceholderText("(Using app icon)")
        else:  # Unchecked
            self.icon_edit.setEnabled(True)
            self.icon_edit.setPlaceholderText("🌐 or emoji")

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

        # Handle icon field - check if it's an app icon
        if self.session.icon.startswith("app:"):
            self.use_app_icon_checkbox.setChecked(True)
            self.icon_edit.clear()
        else:
            self.use_app_icon_checkbox.setChecked(False)
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

        elif app_type == "editor" or app_name in ["vscode", "slack", "spotify"]:
            self.tabs.setCurrentIndex(1)  # Custom Apps tab

            # Find and select the app in combo
            for i in range(self.app_combo.count()):
                if self.app_combo.itemData(i) == app_name:
                    self.app_combo.setCurrentIndex(i)
                    break

            # Load workspace for VS Code
            if app_name == "vscode":
                self.workspace_edit.setText(params.get('workspace', '') or params.get('folder', ''))

            # Load arguments and working directory (shared fields)
            args = params.get('arguments', [])
            if isinstance(args, list):
                self.arguments_edit.setText(' '.join(args))
            else:
                self.arguments_edit.setText(str(args))

            self.workdir_edit.setText(params.get('working_directory', ''))

        else:  # Generic
            self.tabs.setCurrentIndex(1)  # Custom Apps tab

            self.executable_edit.setText(params.get('executable_path', ''))

            args = params.get('arguments', [])
            if isinstance(args, list):
                self.arguments_edit.setText(' '.join(args))
            else:
                self.arguments_edit.setText(str(args))

            self.workdir_edit.setText(params.get('working_directory', ''))

    def _get_icon_value(self) -> str:
        """Get the icon value based on user selection.

        Returns:
            Icon string - either "app:appname" or an emoji
        """
        if self.use_app_icon_checkbox.isChecked():
            # Determine which app to use for icon
            current_tab_index = self.tabs.currentIndex()

            if current_tab_index == 0:  # Browser
                browser = self.browser_combo.currentText()
                return f"app:{browser}"
            elif current_tab_index == 1:  # Custom Apps
                selected_app = self.app_combo.currentData()
                if selected_app:
                    return f"app:{selected_app}"
                else:
                    # For custom executables, use "app:generic" (will fall back to emoji)
                    return f"app:generic"

        # Not using app icon, return emoji
        return self.icon_edit.text().strip() or "🌐"

    def get_session(self) -> Optional[Session]:
        """Get the session from dialog inputs based on active tab.

        Returns:
            Session instance or None if validation fails
        """
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Invalid Input", "Session name is required.")
            return None

        icon = self._get_icon_value()

        # Determine session type based on active tab
        current_tab_index = self.tabs.currentIndex()

        if current_tab_index == 0:  # Browser
            return self._create_browser_session(name, icon)
        elif current_tab_index == 1:  # Custom Apps
            return self._create_custom_app_session(name, icon)
        else:
            return None

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

    def _create_custom_app_session(self, name: str, icon: str) -> Optional[Session]:
        """Create custom app session from inputs (known app or custom executable)."""
        # Get selected tab_id
        tab_id = self.tab_combo.currentData() or "uncategorized"

        # Check if a known app is selected
        selected_app_data = self.app_combo.currentData()
        executable = self.executable_edit.text().strip()

        if selected_app_data:
            # Known app selected (vscode, slack, spotify)
            app = selected_app_data

            # Get arguments and working directory (shared fields)
            args_text = self.arguments_edit.text().strip()
            arguments = args_text.split() if args_text else []
            workdir = self.workdir_edit.text().strip() or None

            # VS Code requires workspace
            if app == "vscode":
                workspace = self.workspace_edit.text().strip()
                if not workspace:
                    QMessageBox.warning(self, "Invalid Input", "Workspace/Folder path is required for VS Code.")
                    return None

                if self.editing and self.session:
                    # Update existing session
                    self.session.name = name
                    self.session.icon = icon
                    self.session.tab_id = tab_id
                    self.session.launch_config.app_name = app
                    self.session.launch_config.parameters['workspace'] = workspace
                    if arguments:
                        self.session.launch_config.parameters['arguments'] = arguments
                    if workdir:
                        self.session.launch_config.parameters['working_directory'] = workdir
                    return self.session
                else:
                    session = create_vscode_session(
                        name=name,
                        workspace_path=workspace,
                        icon=icon,
                        tab_id=tab_id
                    )
                    if arguments:
                        session.launch_config.parameters['arguments'] = arguments
                    if workdir:
                        session.launch_config.parameters['working_directory'] = workdir
                    return session
            else:
                # Slack, Spotify, etc.
                if self.editing and self.session:
                    # Update existing session
                    self.session.name = name
                    self.session.icon = icon
                    self.session.tab_id = tab_id
                    self.session.launch_config.app_name = app
                    if arguments:
                        self.session.launch_config.parameters['arguments'] = arguments
                    if workdir:
                        self.session.launch_config.parameters['working_directory'] = workdir
                    return self.session
                else:
                    session = create_generic_app_session(
                        name=name,
                        app_name=app,
                        executable_path="",  # Will be auto-detected
                        icon=icon,
                        tab_id=tab_id
                    )
                    if arguments:
                        session.launch_config.parameters['arguments'] = arguments
                    if workdir:
                        session.launch_config.parameters['working_directory'] = workdir
                    return session

        elif executable:
            # Custom executable path provided
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

        else:
            # Neither known app nor custom executable provided
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please select a known application or provide a custom executable path."
            )
            return None
