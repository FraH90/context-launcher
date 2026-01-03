"""Main application window with dynamic tabbed interface."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QLabel, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QMenu
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush, QAction
from pathlib import Path
from typing import Dict, List

from ..core.config import ConfigManager
from ..core.session import Session, Workflow, SessionType
from ..core.tab import Tab, TabsCollection
from ..core.workflow_executor import WorkflowExecutor, WorkflowExecutionResult, StepStatus
from ..launchers import LaunchConfig, AppType, LauncherFactory
from ..utils.logger import get_logger
from .session_dialog import SessionDialog
from .workflow_dialog import WorkflowDialog
from .category_dialog import CategoryDialog


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

        # Tree widget for hierarchical category view
        self.tree_widget: QTreeWidget = None
        self.search_text = ""

        self.setWindowTitle("Context Launcher v3.0")
        self.setGeometry(100, 100, 700, 750)

        self._init_ui()
        self._load_tabs()
        self._load_sessions()
        self._load_workflows()

    def _init_ui(self):
        """Initialize UI components."""
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

        self.new_category_btn = QPushButton("+ Category")
        self.new_category_btn.clicked.connect(self._on_new_category_clicked)
        header_layout.addWidget(self.new_category_btn)

        self.add_session_btn = QPushButton("+ Session")
        self.add_session_btn.clicked.connect(self._on_add_session_clicked)
        header_layout.addWidget(self.add_session_btn)

        self.add_workflow_btn = QPushButton("+ Workflow")
        self.add_workflow_btn.clicked.connect(self._on_add_workflow_clicked)
        header_layout.addWidget(self.add_workflow_btn)

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

        # Tree widget for hierarchical categories
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Categories & Sessions")
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree_widget.itemSelectionChanged.connect(self._update_button_states)
        self.tree_widget.itemExpanded.connect(self._on_item_expanded)
        self.tree_widget.itemCollapsed.connect(self._on_item_collapsed)

        # Enable drag and drop
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDropIndicatorShown(True)
        self.tree_widget.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)

        layout.addWidget(self.tree_widget)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.launch_btn = QPushButton("▶ Launch")
        self.launch_btn.clicked.connect(self._on_launch_clicked)
        button_layout.addWidget(self.launch_btn)

        self.edit_btn = QPushButton("✏ Edit")
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        button_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        button_layout.addWidget(self.delete_btn)

        layout.addLayout(button_layout)

        # Initially disable buttons
        self.launch_btn.setEnabled(False)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)

    def _load_tabs(self):
        """Load user-defined tabs/categories from JSON."""
        tabs_data = self.config_manager.load_tabs()
        self.tabs_collection = TabsCollection.from_dict(tabs_data)
        self._refresh_tree()

    def _update_button_states(self):
        """Update button enabled states based on selection."""
        current_item = self.tree_widget.currentItem()
        if not current_item:
            self.launch_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return

        # Check if it's a session/workflow (has data) or just a category
        item_type = current_item.data(0, Qt.ItemDataRole.UserRole + 1)

        # Can launch sessions and workflows
        self.launch_btn.setEnabled(item_type in ['session', 'workflow'])

        # Can edit anything
        self.edit_btn.setEnabled(True)

        # Can delete anything
        self.delete_btn.setEnabled(True)

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
        if not item:
            return

        menu = QMenu(self)
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
            launch_action = QAction("▶ Launch", self)
            launch_action.triggered.connect(self._on_launch_clicked)
            menu.addAction(launch_action)

            menu.addSeparator()

            edit_action = QAction("✏ Edit", self)
            edit_action.triggered.connect(self._on_edit_clicked)
            menu.addAction(edit_action)

            delete_action = QAction("🗑 Delete", self)
            delete_action.triggered.connect(self._on_delete_clicked)
            menu.addAction(delete_action)

        menu.exec(self.tree_widget.viewport().mapToGlobal(position))

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
                self._refresh_tree()

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
                self._refresh_tree()

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

    def _on_launch_clicked(self):
        """Handle launch button click."""
        current_item = self.tree_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a session or workflow to launch.")
            return

        item_obj = current_item.data(0, Qt.ItemDataRole.UserRole)
        item_type = current_item.data(0, Qt.ItemDataRole.UserRole + 1)

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

                QMessageBox.information(self, "Workflow Complete", message)

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

    def _on_add_session_clicked(self):
        """Handle add session button click."""
        # Get current category to pre-select in dialog
        current_tab_id = None
        current_item = self.tree_widget.currentItem()
        if current_item:
            item_type = current_item.data(0, Qt.ItemDataRole.UserRole + 1)
            if item_type == 'category':
                # Use selected category
                tab_obj = current_item.data(0, Qt.ItemDataRole.UserRole)
                current_tab_id = tab_obj.id

        dialog = SessionDialog(self, tabs_collection=self.tabs_collection, default_tab_id=current_tab_id)

        if dialog.exec():
            session = dialog.get_session()
            if session:
                self.sessions.append(session)
                self.config_manager.save_session(session.id, session.to_dict())
                self._refresh_tree()

    def _on_add_workflow_clicked(self):
        """Handle add workflow button click."""
        # Get current category to pre-select in dialog
        current_tab_id = None
        current_item = self.tree_widget.currentItem()
        if current_item:
            item_type = current_item.data(0, Qt.ItemDataRole.UserRole + 1)
            if item_type == 'category':
                # Use selected category
                tab_obj = current_item.data(0, Qt.ItemDataRole.UserRole)
                current_tab_id = tab_obj.id

        dialog = WorkflowDialog(
            self,
            sessions=self.sessions,
            tabs_collection=self.tabs_collection,
            default_tab_id=current_tab_id
        )

        if dialog.exec():
            workflow = dialog.get_workflow()
            if workflow:
                self.workflows.append(workflow)
                self.config_manager.save_workflow(workflow.id, workflow.to_dict())
                self._refresh_tree()

    def _on_edit_clicked(self):
        """Handle edit button click."""
        current_item = self.tree_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select something to edit.")
            return

        item_obj = current_item.data(0, Qt.ItemDataRole.UserRole)
        item_type = current_item.data(0, Qt.ItemDataRole.UserRole + 1)

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
        current_item = self.tree_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select something to delete.")
            return

        item_obj = current_item.data(0, Qt.ItemDataRole.UserRole)
        item_type = current_item.data(0, Qt.ItemDataRole.UserRole + 1)

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

    def _on_new_category_clicked(self):
        """Handle new category button click."""
        dialog = CategoryDialog(self, tabs_collection=self.tabs_collection)

        if dialog.exec():
            category = dialog.get_category()
            self.tabs_collection.add_tab(category)
            self.config_manager.save_tabs(self.tabs_collection.to_dict())
            self._refresh_tree()
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
