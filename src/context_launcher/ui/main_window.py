"""Main application window with dynamic tabbed interface."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QLabel, QLineEdit,
    QTreeWidgetItem, QMenu, QTabWidget,
    QListWidget, QListWidgetItem, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush, QAction, QShortcut, QKeySequence
from pathlib import Path
from typing import Dict, List

from ..core.config import ConfigManager
from ..core.session import Session, Workflow, SessionType
from ..core.tab import Tab, TabsCollection
from ..core.workflow_executor import WorkflowExecutor, WorkflowExecutionResult, StepStatus
from ..core.window_manager import WindowManager, WindowState
from ..core.backup_manager import BackupManager
from ..core.debug_config import DebugConfig
from ..launchers import LaunchConfig, AppType, LauncherFactory
from ..utils.logger import get_logger
from .session_dialog import SessionDialog
from .workflow_dialog import WorkflowDialog
from .category_dialog import CategoryDialog
from .tree_widget import SmartTreeWidget


class MainWindow(QMainWindow):
    """Main application window with hierarchical tree view."""

    def __init__(self):
        """Initialize main window."""
        super().__init__()

        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.sessions: List[Session] = []
        self.workflows: List[Workflow] = []
        self.tabs_collection: TabsCollection = None
        self.workflow_executor = WorkflowExecutor(self.config_manager)
        self.window_manager = WindowManager()
        self.backup_manager = BackupManager(self.config_manager)

        # View mode widgets
        self.view_stack: QStackedWidget = None
        self.tree_widget: SmartTreeWidget = None
        self.tab_widget: QTabWidget = None
        self.tab_list_widgets: Dict[str, QListWidget] = {}  # Map tab_id -> QListWidget
        self.search_text = ""
        self.current_view_mode = "tree"  # Default to tree view

        self.setWindowTitle("Context Launcher v3.0")
        self.setGeometry(100, 100, 700, 750)

        self._init_ui()
        self._setup_keyboard_shortcuts()
        self._load_user_preferences()
        self._load_tabs()
        self._load_sessions()
        self._load_workflows()

    def _show_info_message(self, title: str, message: str):
        """Show informational message (only in debug mode).

        Args:
            title: Message box title
            message: Message content
        """
        if DebugConfig.is_debug_mode():
            QMessageBox.information(self, title, message)
        else:
            # Log instead of showing popup
            self.logger.info(f"{title}: {message}")

    def _show_success_message(self, title: str, message: str):
        """Show success message (only in debug mode).

        Args:
            title: Message box title
            message: Message content
        """
        if DebugConfig.is_debug_mode():
            QMessageBox.information(self, title, message)
        else:
            # Log instead of showing popup
            self.logger.info(f"SUCCESS - {title}: {message}")

    def _create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Backup
        backup_action = QAction("💾 Create Backup...", self)
        backup_action.triggered.connect(self._on_create_backup)
        file_menu.addAction(backup_action)

        # Restore
        restore_action = QAction("📦 Restore from Backup...", self)
        restore_action.triggered.connect(self._on_restore_backup)
        file_menu.addAction(restore_action)

        file_menu.addSeparator()

        # Import
        import_action = QAction("📥 Import...", self)
        import_action.triggered.connect(self._on_import)
        file_menu.addAction(import_action)

        # Export
        export_action = QAction("📤 Export...", self)
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # Exit
        exit_action = QAction("❌ Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Dark theme toggle
        self.dark_theme_action = QAction("🌙 Dark Theme", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.dark_theme_action)

    def _init_ui(self):
        """Initialize UI components."""
        # Create menu bar
        self._create_menu_bar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header with title and top buttons
        header_layout = QHBoxLayout()

        title_label = QLabel("Context Launcher")
        title_font = QFont("Arial", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # View mode toggle button
        self.toggle_view_btn = QPushButton("🔄 Switch to Tab View")
        self.toggle_view_btn.clicked.connect(self._toggle_view_mode)
        header_layout.addWidget(self.toggle_view_btn)

        layout.addLayout(header_layout)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Type to search sessions and workflows...")
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_edit)

        self.clear_search_btn = QPushButton("Clear")
        self.clear_search_btn.clicked.connect(self._clear_search)
        search_layout.addWidget(self.clear_search_btn)

        layout.addLayout(search_layout)

        # Stacked widget to switch between Tree and Tab views
        self.view_stack = QStackedWidget()

        # Create Tree View (index 0)
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)

        self.tree_widget = SmartTreeWidget()
        self.tree_widget.setHeaderLabel("Categories & Sessions")
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree_widget.itemExpanded.connect(self._on_item_expanded)
        self.tree_widget.itemCollapsed.connect(self._on_item_collapsed)
        self.tree_widget.item_dropped.connect(self._on_tree_item_dropped)

        # Enable drag and drop with smart validation
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDropIndicatorShown(True)
        self.tree_widget.setDragDropMode(SmartTreeWidget.DragDropMode.InternalMove)

        tree_layout.addWidget(self.tree_widget)
        self.view_stack.addWidget(tree_container)

        # Create Tab View (index 1)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)  # Don't allow closing tabs in this mode
        self.tab_widget.currentChanged.connect(self._on_tab_changed)  # Handle tab changes
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self._show_tab_context_menu)
        self.view_stack.addWidget(self.tab_widget)

        layout.addWidget(self.view_stack)

    def _load_tabs(self):
        """Load user-defined tabs/categories from JSON."""
        tabs_data = self.config_manager.load_tabs()
        self.tabs_collection = TabsCollection.from_dict(tabs_data)

        # Set initial view mode based on preferences
        if self.current_view_mode == "tree":
            self._switch_to_tree_view()
        else:
            self._switch_to_tab_view()

    def _load_sessions(self):
        """Load sessions from disk."""
        self.sessions.clear()
        session_files = self.config_manager.list_sessions()

        # Create default session if none exist
        if not session_files:
            self._create_default_sessions()
            session_files = self.config_manager.list_sessions()

        for session_file in session_files:
            try:
                session_data = self.config_manager.load_session(session_file.stem)
                session = Session.from_dict(session_data)
                self.sessions.append(session)
            except Exception as e:
                self.logger.error(f"Failed to load session {session_file}: {e}")

        self._refresh_tree()

    def _refresh_tree(self):
        """Refresh the tree widget with categories, sessions, and workflows."""
        # Save expanded state before clearing
        expanded_categories = set()
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            self._save_expanded_state(root.child(i), expanded_categories)

        # Clear tree
        self.tree_widget.clear()

        # Build tree recursively
        root_tabs = self.tabs_collection.get_root_tabs()
        for tab in root_tabs:
            self._add_category_to_tree(tab, None, expanded_categories)

    def _save_expanded_state(self, item: QTreeWidgetItem, expanded_set: set):
        """Recursively save expanded state of tree items.

        Args:
            item: Tree item to check
            expanded_set: Set to store IDs of expanded categories
        """
        category_id = item.data(0, Qt.ItemDataRole.UserRole + 2)
        if category_id and item.isExpanded():
            expanded_set.add(category_id)

        for i in range(item.childCount()):
            self._save_expanded_state(item.child(i), expanded_set)

    def _add_category_to_tree(self, tab: Tab, parent_item: QTreeWidgetItem, expanded_set: set):
        """Add a category and its contents to the tree.

        Args:
            tab: Tab/category to add
            parent_item: Parent tree item (None for root)
            expanded_set: Set of category IDs that should be expanded
        """
        # Create category item
        category_item = QTreeWidgetItem()
        category_item.setText(0, f"{tab.icon} {tab.name}")
        category_item.setData(0, Qt.ItemDataRole.UserRole, tab)  # Store tab object
        category_item.setData(0, Qt.ItemDataRole.UserRole + 1, 'category')  # Store type
        category_item.setData(0, Qt.ItemDataRole.UserRole + 2, tab.id)  # Store ID for expansion state

        # Apply color if set
        if tab.color:
            color = QColor(tab.color)
            category_item.setForeground(0, QBrush(color))
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)

        # Add to parent or root
        if parent_item:
            parent_item.addChild(category_item)
        else:
            self.tree_widget.addTopLevelItem(category_item)

        # Restore or apply expanded state
        should_expand = tab.id in expanded_set if expanded_set else tab.expanded
        category_item.setExpanded(should_expand)

        # Add sessions and workflows for this category
        for item_obj, item_type in self._get_items_for_category(tab.id):
            self._add_item_to_tree(item_obj, item_type, category_item)

        # Add child categories recursively
        children = self.tabs_collection.get_children(tab.id)
        for child_tab in children:
            self._add_category_to_tree(child_tab, category_item, expanded_set)

    def _get_items_for_category(self, tab_id: str) -> list:
        """Get sessions and workflows for a specific category.

        Args:
            tab_id: Category ID

        Returns:
            List of tuples (item_object, item_type)
        """
        items = []

        # Filter by search text if present
        search_lower = self.search_text.lower()

        # Add sessions
        for session in self.sessions:
            if session.tab_id == tab_id:
                if not search_lower or search_lower in session.name.lower():
                    items.append((session, 'session'))

        # Add workflows
        for workflow in self.workflows:
            if workflow.tab_id == tab_id:
                if not search_lower or search_lower in workflow.name.lower():
                    items.append((workflow, 'workflow'))

        # Sort by name
        items.sort(key=lambda x: x[0].name)
        return items

    def _add_item_to_tree(self, item_obj, item_type: str, parent_item: QTreeWidgetItem):
        """Add a session or workflow to the tree.

        Args:
            item_obj: Session or Workflow object
            item_type: 'session' or 'workflow'
            parent_item: Parent category item
        """
        tree_item = QTreeWidgetItem()

        # Format display text
        if item_type == 'session':
            display_text = self._format_session_text(item_obj)
        else:
            display_text = self._format_workflow_text(item_obj)

        tree_item.setText(0, display_text)
        tree_item.setData(0, Qt.ItemDataRole.UserRole, item_obj)
        tree_item.setData(0, Qt.ItemDataRole.UserRole + 1, item_type)

        # Style workflows differently (bold)
        if item_type == 'workflow':
            font = tree_item.font(0)
            font.setBold(True)
            tree_item.setFont(0, font)

        parent_item.addChild(tree_item)

    def _format_session_text(self, session: Session) -> str:
        """Format display text for a session.

        Args:
            session: Session object

        Returns:
            Formatted display text
        """
        app_type = session.launch_config.app_type
        app_name = session.launch_config.app_name

        if app_type == "browser":
            tabs = session.launch_config.parameters.get('tabs', [])
            tab_count = len(tabs)
            return f"{session.icon} {session.name} ({tab_count} tabs)"
        elif app_type == "editor":
            workspace = session.launch_config.parameters.get('workspace', 'workspace')
            workspace_name = Path(workspace).name if workspace else "workspace"
            return f"{session.icon} {session.name} ({workspace_name})"
        else:
            return f"{session.icon} {session.name} ({app_name})"

    def _format_workflow_text(self, workflow: Workflow) -> str:
        """Format display text for a workflow.

        Args:
            workflow: Workflow object

        Returns:
            Formatted display text
        """
        step_count = len(workflow.launch_sequence)
        return f"⚡ {workflow.icon} {workflow.name} ({step_count} steps)"

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click on tree item.

        Args:
            item: Clicked item
            column: Column index
        """
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)

        # Only launch sessions and workflows
        if item_type in ['session', 'workflow']:
            self._on_launch_clicked()

    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle item expansion - save state.

        Args:
            item: Expanded item
        """
        category_id = item.data(0, Qt.ItemDataRole.UserRole + 2)
        if category_id:
            self.tabs_collection.update_expanded_state(category_id, True)
            self.config_manager.save_tabs(self.tabs_collection.to_dict())

    def _on_item_collapsed(self, item: QTreeWidgetItem):
        """Handle item collapse - save state.

        Args:
            item: Collapsed item
        """
        category_id = item.data(0, Qt.ItemDataRole.UserRole + 2)
        if category_id:
            self.tabs_collection.update_expanded_state(category_id, False)
            self.config_manager.save_tabs(self.tabs_collection.to_dict())

    def _on_tree_item_dropped(self, source_item: QTreeWidgetItem, target_item: QTreeWidgetItem,
                              source_type: str, target_type: str):
        """Handle item dropped in tree - update data model.

        Args:
            source_item: Item that was dropped
            target_item: Item it was dropped onto
            source_type: Type of source ('category', 'session', 'workflow')
            target_type: Type of target
        """
        source_obj = source_item.data(0, Qt.ItemDataRole.UserRole)
        target_obj = target_item.data(0, Qt.ItemDataRole.UserRole)

        if source_type == 'category' and target_type == 'category':
            # Moving category to be child of another category
            source_obj.parent_id = target_obj.id
            self.config_manager.save_tabs(self.tabs_collection.to_dict())
            self.logger.info(f"Moved category '{source_obj.name}' under '{target_obj.name}'")

        elif source_type == 'session' and target_type == 'category':
            # Moving session to a category
            source_obj.tab_id = target_obj.id
            self.config_manager.save_session(source_obj.id, source_obj.to_dict())
            self.logger.info(f"Moved session '{source_obj.name}' to category '{target_obj.name}'")

        elif source_type == 'workflow' and target_type == 'category':
            # Moving workflow to a category
            source_obj.tab_id = target_obj.id
            self.config_manager.save_workflow(source_obj.id, source_obj.to_dict())
            self.logger.info(f"Moved workflow '{source_obj.name}' to category '{target_obj.name}'")

    def _on_search_text_changed(self, text: str):
        """Handle search text change.

        Args:
            text: New search text
        """
        self.search_text = text
        self._refresh_tree()

    def _clear_search(self):
        """Clear search text."""
        self.search_edit.clear()
        self.search_text = ""
        self._refresh_tree()

    def _show_context_menu(self, position):
        """Show context menu for tree items.

        Args:
            position: Menu position
        """
        item = self.tree_widget.itemAt(position)
        menu = QMenu(self)

        # If no item clicked (empty space), show "Add New Category" option
        if not item:
            new_category_action = QAction("📁 Add New Category", self)
            new_category_action.triggered.connect(self._on_new_category_clicked)
            menu.addAction(new_category_action)
            menu.exec(self.tree_widget.viewport().mapToGlobal(position))
            return

        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)

        if item_type == 'category':
            # Category context menu
            tab = item.data(0, Qt.ItemDataRole.UserRole)

            new_session_action = QAction("📄 New Session in Category", self)
            new_session_action.triggered.connect(lambda: self._on_new_session_in_category(tab.id))
            menu.addAction(new_session_action)

            new_workflow_action = QAction("⚡ New Workflow in Category", self)
            new_workflow_action.triggered.connect(lambda: self._on_new_workflow_in_category(tab.id))
            menu.addAction(new_workflow_action)

            new_subcategory_action = QAction("📁 New Subcategory", self)
            new_subcategory_action.triggered.connect(lambda: self._on_new_subcategory(tab.id))
            menu.addAction(new_subcategory_action)

            menu.addSeparator()

            edit_action = QAction("✏ Edit Category", self)
            edit_action.triggered.connect(self._on_edit_clicked)
            menu.addAction(edit_action)

            delete_action = QAction("🗑 Delete Category", self)
            delete_action.triggered.connect(self._on_delete_clicked)
            menu.addAction(delete_action)

        elif item_type in ['session', 'workflow']:
            # Session/Workflow context menu
            item_obj = item.data(0, Qt.ItemDataRole.UserRole)

            launch_action = QAction("▶ Launch", self)
            launch_action.triggered.connect(self._on_launch_clicked)
            menu.addAction(launch_action)

            menu.addSeparator()

            # Favorites toggle
            if item_obj.metadata.favorite:
                fav_action = QAction("⭐ Remove from Favorites", self)
            else:
                fav_action = QAction("☆ Add to Favorites", self)
            fav_action.triggered.connect(lambda: self._toggle_favorite(item_obj, item_type))
            menu.addAction(fav_action)

            # Configure window position (only for sessions, not workflows)
            if item_type == 'session':
                config_window_action = QAction("🪟 Configure Window Position", self)
                config_window_action.triggered.connect(lambda: self._configure_window_position(item_obj))
                menu.addAction(config_window_action)

            menu.addSeparator()

            edit_action = QAction("✏ Edit", self)
            edit_action.triggered.connect(self._on_edit_clicked)
            menu.addAction(edit_action)

            delete_action = QAction("🗑 Delete", self)
            delete_action.triggered.connect(self._on_delete_clicked)
            menu.addAction(delete_action)

        menu.exec(self.tree_widget.viewport().mapToGlobal(position))

    def _show_tab_context_menu(self, position):
        """Show context menu for tab bar.

        Args:
            position: Menu position
        """
        # Get the tab index at the clicked position
        tab_index = self.tab_widget.tabBar().tabAt(position)
        if tab_index < 0:
            return

        # Don't show context menu on the "+" tab
        if self.tab_widget.tabText(tab_index) == "+":
            return

        # Get the category for this tab
        root_tabs = self.tabs_collection.get_root_tabs()
        if tab_index >= len(root_tabs):
            return

        tab = root_tabs[tab_index]

        menu = QMenu(self)

        # Edit category
        edit_action = QAction("✏ Edit Category", self)
        edit_action.triggered.connect(lambda: self._edit_category_from_tab(tab))
        menu.addAction(edit_action)

        menu.addSeparator()

        # Delete category
        delete_action = QAction("🗑 Delete Category", self)
        delete_action.triggered.connect(lambda: self._delete_category_from_tab(tab))
        menu.addAction(delete_action)

        menu.exec(self.tab_widget.tabBar().mapToGlobal(position))

    def _edit_category_from_tab(self, tab: Tab):
        """Edit category from tab view.

        Args:
            tab: Category to edit
        """
        from .category_dialog import CategoryDialog

        dialog = CategoryDialog(self, category=tab, tabs_collection=self.tabs_collection)

        if dialog.exec():
            updated_category = dialog.get_category()
            self.tabs_collection.update_tab(updated_category.id, updated_category.to_dict())
            self.config_manager.save_tabs(self.tabs_collection.to_dict())
            self._refresh_tab_view()
            self.logger.info(f"Updated category: {updated_category.name}")

    def _delete_category_from_tab(self, tab: Tab):
        """Delete category from tab view.

        Args:
            tab: Category to delete
        """
        # Check if category has children or items
        descendants = self.tabs_collection.get_all_descendants(tab.id)
        category_ids = {tab.id} | {d.id for d in descendants}
        has_sessions = any(s.tab_id in category_ids for s in self.sessions)
        has_workflows = any(w.tab_id in category_ids for w in self.workflows)

        if descendants or has_sessions or has_workflows:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                "Cannot delete category that contains subcategories, sessions, or workflows.\n\n"
                "Please move or delete all contents first."
            )
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the category '{tab.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.tabs_collection.remove_tab(tab.id)
            self.config_manager.save_tabs(self.tabs_collection.to_dict())
            self._refresh_tab_view()
            self.logger.info(f"Deleted category: {tab.name}")

    def _show_tab_list_context_menu(self, position, category_id: str, list_widget: QListWidget):
        """Show context menu for tab view list widget.

        Args:
            position: Menu position
            category_id: ID of the category for this tab
            list_widget: The list widget
        """
        # Check if click was on an item or empty space
        item = list_widget.itemAt(position)

        menu = QMenu(self)

        if not item:
            # Clicked on empty space - show "Add New" menu
            new_session_action = QAction("📄 New Session", self)
            new_session_action.triggered.connect(lambda: self._on_new_session_in_category(category_id))
            menu.addAction(new_session_action)

            new_workflow_action = QAction("⚡ New Workflow", self)
            new_workflow_action.triggered.connect(lambda: self._on_new_workflow_in_category(category_id))
            menu.addAction(new_workflow_action)
        else:
            # Clicked on an item - show item actions
            item_data = item.data(Qt.ItemDataRole.UserRole)
            item_type = item.data(Qt.ItemDataRole.UserRole + 1)

            # Launch action
            launch_action = QAction("▶ Launch", self)
            launch_action.triggered.connect(lambda: self._launch_item_from_tab_view(item_data, item_type))
            menu.addAction(launch_action)

            menu.addSeparator()

            # Favorites toggle
            if item_data.metadata.favorite:
                fav_action = QAction("⭐ Remove from Favorites", self)
            else:
                fav_action = QAction("☆ Add to Favorites", self)
            fav_action.triggered.connect(lambda: self._toggle_favorite(item_data, item_type))
            menu.addAction(fav_action)

            # Configure window position (only for sessions)
            if item_type == 'session':
                config_window_action = QAction("🪟 Configure Window Position", self)
                config_window_action.triggered.connect(lambda: self._configure_window_position(item_data))
                menu.addAction(config_window_action)

            menu.addSeparator()

            # Edit action
            edit_action = QAction("✏ Edit", self)
            edit_action.triggered.connect(lambda: self._edit_item_from_tab_view(item_data, item_type))
            menu.addAction(edit_action)

            # Delete action
            delete_action = QAction("🗑 Delete", self)
            delete_action.triggered.connect(lambda: self._delete_item_from_tab_view(item_data, item_type))
            menu.addAction(delete_action)

        menu.exec(list_widget.viewport().mapToGlobal(position))

    def _on_new_session_in_category(self, category_id: str):
        """Create new session in specific category.

        Args:
            category_id: ID of category
        """
        dialog = SessionDialog(self, tabs_collection=self.tabs_collection, default_tab_id=category_id)

        if dialog.exec():
            session = dialog.get_session()
            if session:
                self.sessions.append(session)
                self.config_manager.save_session(session.id, session.to_dict())

                # Refresh based on current view mode
                if self.current_view_mode == "tree":
                    self._refresh_tree()
                else:
                    self._refresh_tab_view()

    def _on_new_workflow_in_category(self, category_id: str):
        """Create new workflow in specific category.

        Args:
            category_id: ID of category
        """
        dialog = WorkflowDialog(
            self,
            sessions=self.sessions,
            tabs_collection=self.tabs_collection,
            default_tab_id=category_id
        )

        if dialog.exec():
            workflow = dialog.get_workflow()
            if workflow:
                self.workflows.append(workflow)
                self.config_manager.save_workflow(workflow.id, workflow.to_dict())

                # Refresh based on current view mode
                if self.current_view_mode == "tree":
                    self._refresh_tree()
                else:
                    self._refresh_tab_view()

    def _on_new_subcategory(self, parent_id: str):
        """Create new subcategory under a parent.

        Args:
            parent_id: ID of parent category
        """
        dialog = CategoryDialog(self, tabs_collection=self.tabs_collection)

        # Pre-set parent
        if dialog.exec():
            category = dialog.get_category()
            category.parent_id = parent_id  # Override to be subcategory
            self.tabs_collection.add_tab(category)
            self.config_manager.save_tabs(self.tabs_collection.to_dict())
            self._refresh_tree()

    def _launch_item_from_tab_view(self, item_obj, item_type: str):
        """Launch item from tab view context menu."""
        if item_type == 'session':
            self._launch_session(item_obj)
        elif item_type == 'workflow':
            self._launch_workflow(item_obj)

    def _edit_item_from_tab_view(self, item_obj, item_type: str):
        """Edit item from tab view context menu."""
        if item_type == 'session':
            dialog = SessionDialog(self, session=item_obj, tabs_collection=self.tabs_collection)
            if dialog.exec():
                updated_session = dialog.get_session()
                if updated_session:
                    # Find and update in list
                    for i, s in enumerate(self.sessions):
                        if s.id == item_obj.id:
                            self.sessions[i] = updated_session
                            break
                    self.config_manager.save_session(updated_session.id, updated_session.to_dict())
                    self._refresh_tab_view()

        elif item_type == 'workflow':
            dialog = WorkflowDialog(
                self,
                workflow=item_obj,
                sessions=self.sessions,
                tabs_collection=self.tabs_collection
            )
            if dialog.exec():
                updated_workflow = dialog.get_workflow()
                if updated_workflow:
                    # Find and update in list
                    for i, w in enumerate(self.workflows):
                        if w.id == item_obj.id:
                            self.workflows[i] = updated_workflow
                            break
                    self.config_manager.save_workflow(updated_workflow.id, updated_workflow.to_dict())
                    self._refresh_tab_view()

    def _delete_item_from_tab_view(self, item_obj, item_type: str):
        """Delete item from tab view context menu."""
        # Confirm deletion
        item_name = item_obj.name
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if item_type == 'session':
                self.sessions.remove(item_obj)
                self.config_manager.delete_session(item_obj.id)
            elif item_type == 'workflow':
                self.workflows.remove(item_obj)
                self.config_manager.delete_workflow(item_obj.id)

            self._refresh_tab_view()

    def _on_launch_clicked(self):
        """Handle launch button click."""
        item_obj, item_type = self._get_current_item()

        if not item_obj:
            QMessageBox.warning(self, "No Selection", "Please select a session or workflow to launch.")
            return

        if item_type == 'session':
            self._launch_session(item_obj)
        elif item_type == 'workflow':
            self._launch_workflow(item_obj)

    def _launch_session(self, session: Session):
        """Launch a single session.

        Args:
            session: Session to launch
        """
        try:
            # Create launch config
            launch_config = LaunchConfig(
                app_type=AppType(session.launch_config.app_type),
                app_name=session.launch_config.app_name,
                parameters=session.launch_config.parameters,
                platform='win32'  # Will be auto-detected
            )

            # Create launcher
            launcher = LauncherFactory.create_launcher(launch_config)

            # Launch
            self.logger.info(f"Launching session: {session.name}")
            result = launcher.launch()

            if result.success:
                # Update stats first
                session.update_launch_stats()
                self.config_manager.save_session(session.id, session.to_dict())

                # Handle window management if supported (non-blocking)
                if result.process_id and session.metadata.window_state:
                    # Position window in background thread to avoid freezing GUI
                    import threading

                    def position_window():
                        try:
                            window_state = WindowState.from_dict(session.metadata.window_state)
                            app_name = session.launch_config.app_name  # Get app name for smarter window finding
                            # Wait up to 10 seconds for window to appear, then position it
                            success = self.window_manager.set_window_state(
                                result.process_id,
                                window_state,
                                timeout=10.0,
                                app_name=app_name
                            )
                            if success:
                                self.logger.info(f"Automatically positioned window for {session.name}")
                            else:
                                self.logger.warning(f"Could not position window for {session.name} (window may not have appeared)")
                        except Exception as e:
                            self.logger.error(f"Window positioning error: {e}")

                    thread = threading.Thread(target=position_window, daemon=True)
                    thread.start()

                self._show_success_message(
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

    def _launch_workflow(self, workflow: Workflow):
        """Launch a workflow with progress tracking.

        Args:
            workflow: Workflow to launch
        """
        try:
            self.logger.info(f"Launching workflow: {workflow.name}")

            # Execute workflow
            result = self.workflow_executor.execute_workflow(workflow, self.sessions)

            # Build result message
            if result.status == StepStatus.SUCCESS:
                message = f"Workflow '{workflow.name}' completed successfully!\n\n"
                message += f"✓ {result.successful_steps} steps succeeded\n"
                message += f"Total time: {result.total_elapsed_ms}ms"

                self._show_success_message("Workflow Complete", message)

                # Update workflow stats
                workflow.update_launch_stats()
                self.config_manager.save_workflow(workflow.id, workflow.to_dict())

            else:
                message = f"Workflow '{workflow.name}' completed with errors:\n\n"
                message += f"✓ {result.successful_steps} steps succeeded\n"
                message += f"✗ {result.failed_steps} steps failed\n"
                message += f"⊘ {result.skipped_steps} steps skipped\n\n"

                # Show failed steps
                failed_steps = [r for r in result.step_results if r.status == StepStatus.FAILED]
                if failed_steps:
                    message += "Failed steps:\n"
                    for step_result in failed_steps:
                        message += f"  - Step {step_result.step_index + 1}: {step_result.error_message}\n"

                QMessageBox.warning(self, "Workflow Completed with Errors", message)

        except Exception as e:
            self.logger.error(f"Workflow launch error: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while launching workflow:\n\n{str(e)}"
            )

    def _on_edit_clicked(self):
        """Handle edit button click."""
        item_obj, item_type = self._get_current_item()

        if not item_obj:
            QMessageBox.warning(self, "No Selection", "Please select something to edit.")
            return

        if item_type == 'category':
            # Edit category
            dialog = CategoryDialog(self, category=item_obj, tabs_collection=self.tabs_collection)

            if dialog.exec():
                edited_category = dialog.get_category()
                # The category is edited in-place, just save
                self.config_manager.save_tabs(self.tabs_collection.to_dict())
                self._refresh_tree()

        elif item_type == 'session':
            dialog = SessionDialog(self, session=item_obj, tabs_collection=self.tabs_collection)

            if dialog.exec():
                edited_session = dialog.get_session()
                if edited_session:
                    idx = self.sessions.index(item_obj)
                    self.sessions[idx] = edited_session
                    self.config_manager.save_session(edited_session.id, edited_session.to_dict())
                    self._refresh_tree()

        elif item_type == 'workflow':
            dialog = WorkflowDialog(
                self,
                workflow=item_obj,
                sessions=self.sessions,
                tabs_collection=self.tabs_collection
            )

            if dialog.exec():
                edited_workflow = dialog.get_workflow()
                if edited_workflow:
                    idx = self.workflows.index(item_obj)
                    self.workflows[idx] = edited_workflow
                    self.config_manager.save_workflow(edited_workflow.id, edited_workflow.to_dict())
                    self._refresh_tree()

    def _on_delete_clicked(self):
        """Handle delete button click."""
        item_obj, item_type = self._get_current_item()

        if not item_obj:
            QMessageBox.warning(self, "No Selection", "Please select something to delete.")
            return

        # Confirm deletion
        item_name = item_obj.name
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if item_type == 'category':
                # Check if category has children
                children = self.tabs_collection.get_children(item_obj.id)
                descendants = self.tabs_collection.get_all_descendants(item_obj.id)

                # Check if any sessions/workflows belong to this category or descendants
                category_ids = {item_obj.id} | {d.id for d in descendants}
                has_sessions = any(s.tab_id in category_ids for s in self.sessions)
                has_workflows = any(w.tab_id in category_ids for w in self.workflows)

                if children or has_sessions or has_workflows:
                    QMessageBox.warning(
                        self,
                        "Cannot Delete",
                        "Cannot delete category that contains subcategories, sessions, or workflows.\n\n"
                        "Please move or delete all contents first."
                    )
                    return

                # Delete category
                self.tabs_collection.remove_tab(item_obj.id)
                self.config_manager.save_tabs(self.tabs_collection.to_dict())

            elif item_type == 'session':
                self.sessions.remove(item_obj)
                self.config_manager.delete_session(item_obj.id)

            elif item_type == 'workflow':
                self.workflows.remove(item_obj)
                self.config_manager.delete_workflow(item_obj.id)

            self._refresh_tree()

    def _setup_keyboard_shortcuts(self):
        """Setup application keyboard shortcuts."""
        # Ctrl+Tab to cycle forward through tabs
        self.next_tab_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        self.next_tab_shortcut.activated.connect(self._cycle_tab_forward)

        # Ctrl+Shift+Tab to cycle backward through tabs
        self.prev_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        self.prev_tab_shortcut.activated.connect(self._cycle_tab_backward)

    def _cycle_tab_forward(self):
        """Cycle to the next tab (Ctrl+Tab)."""
        # Only work in tab view mode
        if self.current_view_mode != "tabs":
            return

        # Get the number of real tabs (excluding the + tab)
        num_real_tabs = self.tab_widget.count() - 1  # Subtract 1 for the + tab

        if num_real_tabs <= 0:
            return

        current_index = self.tab_widget.currentIndex()

        # If somehow we're on the + tab, reset to first tab
        if current_index >= num_real_tabs:
            next_index = 0
        else:
            next_index = (current_index + 1) % num_real_tabs  # Cycle within real tabs only

        self.tab_widget.setCurrentIndex(next_index)

    def _cycle_tab_backward(self):
        """Cycle to the previous tab (Ctrl+Shift+Tab)."""
        # Only work in tab view mode
        if self.current_view_mode != "tabs":
            return

        # Get the number of real tabs (excluding the + tab)
        num_real_tabs = self.tab_widget.count() - 1  # Subtract 1 for the + tab

        if num_real_tabs <= 0:
            return

        current_index = self.tab_widget.currentIndex()

        # If somehow we're on the + tab, reset to last real tab
        if current_index >= num_real_tabs:
            prev_index = num_real_tabs - 1
        else:
            prev_index = (current_index - 1) % num_real_tabs  # Cycle within real tabs only

        self.tab_widget.setCurrentIndex(prev_index)

    def _on_tab_changed(self, index: int):
        """Handle tab change - detect if "+" tab was clicked.

        Args:
            index: New tab index
        """
        # Check if this is the "+" tab (last tab)
        if index == self.tab_widget.count() - 1 and self.tab_widget.tabText(index) == "+":
            # User clicked the "+" tab, create a new category
            self._on_new_category_clicked()
            # Switch back to the previous tab (before the + tab)
            if self.tab_widget.count() > 1:
                self.tab_widget.setCurrentIndex(self.tab_widget.count() - 2)

    def _on_new_category_clicked(self):
        """Handle new category button click."""
        dialog = CategoryDialog(self, tabs_collection=self.tabs_collection)

        if dialog.exec():
            category = dialog.get_category()
            self.tabs_collection.add_tab(category)
            self.config_manager.save_tabs(self.tabs_collection.to_dict())

            # Refresh based on current view mode
            if self.current_view_mode == "tree":
                self._refresh_tree()
            else:
                self._refresh_tab_view()
                # Switch to the newly created tab (before the + tab)
                new_tab_index = self.tab_widget.count() - 2
                if new_tab_index >= 0:
                    self.tab_widget.setCurrentIndex(new_tab_index)

            self.logger.info(f"Created new category: {category.name}")

    def _load_workflows(self):
        """Load workflows from disk."""
        self.workflows.clear()
        workflow_files = self.config_manager.list_workflows()

        for workflow_file in workflow_files:
            try:
                workflow_data = self.config_manager.load_workflow(workflow_file.stem)
                workflow = Workflow.from_dict(workflow_data)
                self.workflows.append(workflow)
            except Exception as e:
                self.logger.error(f"Failed to load workflow {workflow_file}: {e}")

        self._refresh_tree()

    def _create_default_sessions(self):
        """Create default sessions from template file."""
        from ..core.session import Session
        import uuid

        # Load default sessions from template
        default_sessions = self.config_manager.load_default_sessions_template()

        for session_data in default_sessions:
            # Generate new ID and timestamps
            session_data['id'] = str(uuid.uuid4())

            # Create Session from template data (will set created_at/updated_at)
            session = Session.from_dict(session_data)

            # Save to disk
            self.config_manager.save_session(session.id, session.to_dict())

            self.logger.info(f"Created default session: {session.name}")

    def _load_user_preferences(self):
        """Load user preferences and apply view mode and theme."""
        prefs = self.config_manager.load_user_preferences()
        view_mode = prefs.get('ui', {}).get('view_mode', 'tree')
        self.current_view_mode = view_mode

        # Apply theme
        theme = prefs.get('ui', {}).get('theme', 'system')
        if theme == 'dark':
            self.dark_theme_action.setChecked(True)
            self._toggle_theme()

    def _reload_sessions_and_workflows(self):
        """Reload sessions and workflows from disk to pick up any changes."""
        # Reload sessions
        self.sessions.clear()
        session_files = self.config_manager.list_sessions()
        for session_file in session_files:
            try:
                session_data = self.config_manager.load_session(session_file.stem)
                session = Session.from_dict(session_data)
                self.sessions.append(session)
            except Exception as e:
                self.logger.error(f"Failed to load session {session_file}: {e}")

        # Reload workflows
        self.workflows.clear()
        workflow_files = self.config_manager.list_workflows()
        for workflow_file in workflow_files:
            try:
                workflow_data = self.config_manager.load_workflow(workflow_file.stem)
                workflow = Workflow.from_dict(workflow_data)
                self.workflows.append(workflow)
            except Exception as e:
                self.logger.error(f"Failed to load workflow {workflow_file}: {e}")

    def _toggle_view_mode(self):
        """Toggle between tree and tab view modes."""
        if self.current_view_mode == "tree":
            self._switch_to_tab_view()
        else:
            self._switch_to_tree_view()

    def _switch_to_tree_view(self):
        """Switch to tree view mode."""
        self.current_view_mode = "tree"
        self.view_stack.setCurrentIndex(0)
        self.toggle_view_btn.setText("🔄 Switch to Tab View")

        # Save preference
        prefs = self.config_manager.load_user_preferences()
        prefs['ui']['view_mode'] = 'tree'
        self.config_manager.save_user_preferences(prefs)

        self._refresh_tree()

    def _switch_to_tab_view(self):
        """Switch to tab view mode."""
        self.current_view_mode = "tabs"
        self.view_stack.setCurrentIndex(1)
        self.toggle_view_btn.setText("🔄 Switch to Tree View")

        # Save preference
        prefs = self.config_manager.load_user_preferences()
        prefs['ui']['view_mode'] = 'tabs'
        self.config_manager.save_user_preferences(prefs)

        # Reload data to pick up any changes from tree view
        self._reload_sessions_and_workflows()
        self._refresh_tab_view()

    def _refresh_tab_view(self):
        """Refresh tab view with categories as tabs."""
        # Clear existing tabs
        self.tab_widget.clear()
        self.tab_list_widgets.clear()

        # Only show root-level categories as tabs
        root_tabs = self.tabs_collection.get_root_tabs()
        for tab in root_tabs:
            self._create_tab_for_category(tab)

        # Add permanent "+" tab for creating new categories
        plus_widget = QWidget()
        plus_layout = QVBoxLayout(plus_widget)
        plus_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        plus_label = QLabel("Click this tab to add a new category")
        plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plus_label.setStyleSheet("color: gray; font-size: 12pt;")
        plus_layout.addWidget(plus_label)

        self.tab_widget.addTab(plus_widget, "+")

    def _create_tab_for_category(self, tab: Tab):
        """Create a QTabWidget tab for a category.

        Args:
            tab: Tab/category to create
        """
        list_widget = QListWidget()
        list_widget.itemDoubleClicked.connect(self._on_tab_item_double_clicked)

        # Enable context menu for empty space clicks
        list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        list_widget.customContextMenuRequested.connect(
            lambda pos: self._show_tab_list_context_menu(pos, tab.id, list_widget)
        )

        # Store reference
        self.tab_list_widgets[tab.id] = list_widget

        # Add to tabs widget
        self.tab_widget.addTab(list_widget, f"{tab.icon} {tab.name}")

        # Populate with sessions and workflows for this category (and subcategories)
        self._populate_tab_list(tab.id, list_widget)

    def _populate_tab_list(self, tab_id: str, list_widget: QListWidget):
        """Populate a list widget with sessions/workflows from a category and its children.

        Args:
            tab_id: Category ID
            list_widget: List widget to populate
        """
        # Get this category and all descendants
        category_ids = {tab_id}
        descendants = self.tabs_collection.get_all_descendants(tab_id)
        category_ids.update(d.id for d in descendants)

        # Get all items for these categories
        all_items = []
        search_lower = self.search_text.lower()

        for session in self.sessions:
            if session.tab_id in category_ids:
                if not search_lower or search_lower in session.name.lower():
                    all_items.append((session, 'session'))

        for workflow in self.workflows:
            if workflow.tab_id in category_ids:
                if not search_lower or search_lower in workflow.name.lower():
                    all_items.append((workflow, 'workflow'))

        # Sort by name
        all_items.sort(key=lambda x: x[0].name)

        # Add to list
        for item_obj, item_type in all_items:
            list_item = self._create_list_item(item_obj, item_type)
            list_widget.addItem(list_item)

    def _create_list_item(self, item_obj, item_type: str) -> QListWidgetItem:
        """Create a list widget item for session or workflow.

        Args:
            item_obj: Session or Workflow object
            item_type: 'session' or 'workflow'

        Returns:
            QListWidgetItem
        """
        if item_type == 'session':
            display_text = self._format_session_text(item_obj)
        else:
            display_text = self._format_workflow_text(item_obj)

        list_item = QListWidgetItem(display_text)
        list_item.setData(Qt.ItemDataRole.UserRole, item_obj)
        list_item.setData(Qt.ItemDataRole.UserRole + 1, item_type)

        # Make workflows bold
        if item_type == 'workflow':
            font = list_item.font()
            font.setBold(True)
            list_item.setFont(font)

        return list_item

    def _on_tab_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on tab view list item.

        Args:
            item: Clicked item
        """
        self._on_launch_clicked()

    def _get_current_item(self):
        """Get currently selected item from either view mode.

        Returns:
            Tuple of (item_object, item_type) or (None, None)
        """
        if self.current_view_mode == "tree":
            current_item = self.tree_widget.currentItem()
            if current_item:
                return (
                    current_item.data(0, Qt.ItemDataRole.UserRole),
                    current_item.data(0, Qt.ItemDataRole.UserRole + 1)
                )
        else:
            # Tab view
            current_tab_index = self.tab_widget.currentIndex()
            if current_tab_index >= 0:
                # Get the list widget for current tab
                sorted_tabs = self.tabs_collection.get_root_tabs()
                if current_tab_index < len(sorted_tabs):
                    tab_id = sorted_tabs[current_tab_index].id
                    list_widget = self.tab_list_widgets.get(tab_id)
                    if list_widget:
                        current_item = list_widget.currentItem()
                        if current_item:
                            return (
                                current_item.data(Qt.ItemDataRole.UserRole),
                                current_item.data(Qt.ItemDataRole.UserRole + 1)
                            )

        return (None, None)

    def _toggle_favorite(self, item_obj, item_type: str):
        """Toggle favorite status for a session or workflow.

        Args:
            item_obj: Session or Workflow object
            item_type: 'session' or 'workflow'
        """
        item_obj.metadata.favorite = not item_obj.metadata.favorite

        if item_type == 'session':
            self.config_manager.save_session(item_obj.id, item_obj.to_dict())
        else:
            self.config_manager.save_workflow(item_obj.id, item_obj.to_dict())

        # Refresh UI
        if self.current_view_mode == "tree":
            self._refresh_tree()
        else:
            self._refresh_tab_view()

        status = "added to" if item_obj.metadata.favorite else "removed from"
        self._show_info_message(
            "Favorites",
            f"{item_obj.name} {status} favorites."
        )

    def _configure_window_position(self, session: Session):
        """Configure window position for a session using a simple dialog.

        Args:
            session: Session to configure window position for
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QSpinBox, QCheckBox, QDialogButtonBox, QFormLayout, QComboBox

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Configure Window Position - {session.name}")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Info label
        info_label = QLabel(
            "Configure where this session's window should appear when launched.\n"
            "Leave unchecked to use default position."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Enable checkbox
        enable_checkbox = QCheckBox("Position window automatically on launch")
        if session.metadata.window_state:
            enable_checkbox.setChecked(True)
        layout.addWidget(enable_checkbox)

        # Form for position settings
        form_layout = QFormLayout()

        # Monitor selection
        monitor_combo = QComboBox()
        monitors = self.window_manager.get_monitors()
        for i, mon in enumerate(monitors):
            primary = " (Primary)" if mon.get('is_primary') else ""
            monitor_combo.addItem(f"Monitor {i + 1}{primary} - {mon['width']}x{mon['height']}", i)

        current_monitor = 0
        if session.metadata.window_state:
            current_monitor = session.metadata.window_state.get('monitor_index', 0)
        monitor_combo.setCurrentIndex(current_monitor)
        form_layout.addRow("Monitor:", monitor_combo)

        # X position
        x_spin = QSpinBox()
        x_spin.setRange(-10000, 10000)
        x_spin.setValue(session.metadata.window_state.get('x', 100) if session.metadata.window_state else 100)
        form_layout.addRow("X Position:", x_spin)

        # Y position
        y_spin = QSpinBox()
        y_spin.setRange(-10000, 10000)
        y_spin.setValue(session.metadata.window_state.get('y', 100) if session.metadata.window_state else 100)
        form_layout.addRow("Y Position:", y_spin)

        # Width
        width_spin = QSpinBox()
        width_spin.setRange(100, 10000)
        width_spin.setValue(session.metadata.window_state.get('width', 1200) if session.metadata.window_state else 1200)
        form_layout.addRow("Width:", width_spin)

        # Height
        height_spin = QSpinBox()
        height_spin.setRange(100, 10000)
        height_spin.setValue(session.metadata.window_state.get('height', 800) if session.metadata.window_state else 800)
        form_layout.addRow("Height:", height_spin)

        # Maximized checkbox
        maximized_checkbox = QCheckBox("Start maximized")
        if session.metadata.window_state:
            maximized_checkbox.setChecked(session.metadata.window_state.get('is_maximized', False))
        form_layout.addRow("", maximized_checkbox)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Execute dialog
        if dialog.exec():
            if enable_checkbox.isChecked():
                # Save window state
                window_state = {
                    'x': x_spin.value(),
                    'y': y_spin.value(),
                    'width': width_spin.value(),
                    'height': height_spin.value(),
                    'monitor_index': monitor_combo.currentData(),
                    'is_maximized': maximized_checkbox.isChecked(),
                    'is_minimized': False
                }
                session.metadata.window_state = window_state
            else:
                # Disable window positioning
                session.metadata.window_state = None

            # Save session
            self.config_manager.save_session(session.id, session.to_dict())

            self._show_success_message(
                "Success",
                f"Window configuration saved for {session.name}!"
            )

    def _on_create_backup(self):
        """Create a complete backup of all data."""
        from PySide6.QtWidgets import QFileDialog
        from datetime import datetime

        # Suggest filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"context_launcher_backup_{timestamp}.zip"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Create Backup",
            str(Path.home() / default_name),
            "ZIP Files (*.zip)"
        )

        if file_path:
            success = self.backup_manager.create_backup(Path(file_path))

            if success:
                self._show_success_message(
                    "Backup Created",
                    f"Backup successfully created:\n{file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Backup Failed",
                    "Failed to create backup. Check the logs for details."
                )

    def _on_restore_backup(self):
        """Restore from a backup file."""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Restore from Backup",
            str(Path.home()),
            "ZIP Files (*.zip)"
        )

        if file_path:
            # Confirm action
            reply = QMessageBox.question(
                self,
                "Confirm Restore",
                "Restoring from backup will REPLACE all current data.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success = self.backup_manager.restore_backup(Path(file_path), merge=False)

                if success:
                    self._show_success_message(
                        "Restore Complete",
                        "Backup restored successfully!\n\nThe application will now reload."
                    )
                    # Reload data
                    self._load_tabs()
                    self._load_sessions()
                    self._load_workflows()
                    if self.current_view_mode == "tree":
                        self._refresh_tree()
                    else:
                        self._refresh_tab_view()
                else:
                    QMessageBox.critical(
                        self,
                        "Restore Failed",
                        "Failed to restore backup. Check the logs for details."
                    )

    def _on_import(self):
        """Import sessions/workflows from a ZIP file."""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Data",
            str(Path.home()),
            "ZIP Files (*.zip)"
        )

        if file_path:
            success = self.backup_manager.import_from_zip(Path(file_path))

            if success:
                self._show_success_message(
                    "Import Complete",
                    "Data imported successfully!\n\nThe application will now reload."
                )
                # Reload data
                self._load_tabs()
                self._load_sessions()
                self._load_workflows()
                if self.current_view_mode == "tree":
                    self._refresh_tree()
                else:
                    self._refresh_tab_view()
            else:
                QMessageBox.critical(
                    self,
                    "Import Failed",
                    "Failed to import data. Check the logs for details."
                )

    def _on_export(self):
        """Export selected sessions/workflows to a ZIP file."""
        from PySide6.QtWidgets import QFileDialog
        from datetime import datetime

        # For now, export all sessions and workflows
        # TODO: Could add UI to select specific items

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"context_launcher_export_{timestamp}.zip"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            str(Path.home() / default_name),
            "ZIP Files (*.zip)"
        )

        if file_path:
            # Export everything (same as backup)
            success = self.backup_manager.create_backup(Path(file_path))

            if success:
                self._show_success_message(
                    "Export Complete",
                    f"Data exported successfully:\n{file_path}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    "Failed to export data. Check the logs for details."
                )

    def _toggle_theme(self):
        """Toggle between light and dark theme."""
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPalette, QColor

        if self.dark_theme_action.isChecked():
            # Apply dark theme
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(35, 35, 35))
            QApplication.instance().setPalette(dark_palette)

            # Save preference
            prefs = self.config_manager.load_user_preferences()
            prefs['ui']['theme'] = 'dark'
            self.config_manager.save_user_preferences(prefs)
        else:
            # Revert to system theme
            QApplication.instance().setPalette(QApplication.style().standardPalette())

            # Save preference
            prefs = self.config_manager.load_user_preferences()
            prefs['ui']['theme'] = 'system'
            self.config_manager.save_user_preferences(prefs)
