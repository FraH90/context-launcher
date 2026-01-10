"""Workflow editor dialog for creating composite workflows."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QComboBox, QMessageBox, QLabel, QWidget, QSpinBox,
    QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt
from typing import Optional, List
import uuid
from datetime import datetime

from ..core.session import (
    Workflow, WorkflowStep, Session, LaunchConfiguration,
    SessionType
)
from ..core.tab import TabsCollection


class WorkflowDialog(QDialog):
    """Dialog for creating/editing workflows."""

    def __init__(self, parent=None, workflow: Optional[Workflow] = None,
                 sessions: Optional[List[Session]] = None,
                 tabs_collection: Optional[TabsCollection] = None,
                 default_tab_id: Optional[str] = None):
        """Initialize workflow dialog.

        Args:
            parent: Parent widget
            workflow: Optional workflow to edit (None for new workflow)
            sessions: List of available sessions to add to workflow
            tabs_collection: Collection of user-defined tabs
            default_tab_id: Default tab to select
        """
        super().__init__(parent)

        self.workflow = workflow
        self.editing = workflow is not None
        self.sessions = sessions or []
        self.tabs_collection = tabs_collection
        self.default_tab_id = default_tab_id

        # Workflow steps (will be modified by user)
        self.workflow_steps: List[WorkflowStep] = []
        if self.editing and workflow:
            self.workflow_steps = workflow.launch_sequence.copy()

        title = "Edit Workflow" if self.editing else "New Workflow"
        self.setWindowTitle(title)
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)

        self._init_ui()

        if self.editing:
            self._load_workflow_data()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Top section - workflow metadata
        metadata_group = QGroupBox("Workflow Information")
        metadata_layout = QFormLayout()

        self.name_edit = QLineEdit()
        metadata_layout.addRow("Name:", self.name_edit)

        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("🎯")
        metadata_layout.addRow("Icon (emoji):", self.icon_edit)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional description")
        metadata_layout.addRow("Description:", self.description_edit)

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

        metadata_layout.addRow("Category:", self.tab_combo)

        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)

        # Middle section - workflow steps
        steps_group = QGroupBox("Workflow Steps")
        steps_layout = QVBoxLayout()

        # Steps list
        steps_label = QLabel("Launch Sequence:")
        steps_layout.addWidget(steps_label)

        self.steps_list = QListWidget()
        self.steps_list.currentRowChanged.connect(self._on_step_selected)
        steps_layout.addWidget(self.steps_list)

        # Step controls
        step_controls_layout = QHBoxLayout()

        # Add session to workflow
        self.session_combo = QComboBox()
        self.session_combo.setPlaceholderText("Select session to add...")
        self._populate_session_combo()
        step_controls_layout.addWidget(self.session_combo, stretch=1)

        self.add_step_btn = QPushButton("Add Step")
        self.add_step_btn.clicked.connect(self._add_step)
        step_controls_layout.addWidget(self.add_step_btn)

        self.remove_step_btn = QPushButton("Remove Step")
        self.remove_step_btn.clicked.connect(self._remove_step)
        self.remove_step_btn.setEnabled(False)
        step_controls_layout.addWidget(self.remove_step_btn)

        self.move_up_btn = QPushButton("↑ Move Up")
        self.move_up_btn.clicked.connect(self._move_step_up)
        self.move_up_btn.setEnabled(False)
        step_controls_layout.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton("↓ Move Down")
        self.move_down_btn.clicked.connect(self._move_step_down)
        self.move_down_btn.setEnabled(False)
        step_controls_layout.addWidget(self.move_down_btn)

        steps_layout.addLayout(step_controls_layout)

        steps_group.setLayout(steps_layout)
        layout.addWidget(steps_group)

        # Step configuration section
        config_group = QGroupBox("Step Configuration")
        config_layout = QFormLayout()

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 60000)
        self.delay_spin.setSingleStep(100)
        self.delay_spin.setSuffix(" ms")
        self.delay_spin.setValue(0)
        self.delay_spin.valueChanged.connect(self._update_current_step)
        config_layout.addRow("Delay after step:", self.delay_spin)

        self.continue_on_failure_check = QCheckBox("Continue workflow if this step fails")
        self.continue_on_failure_check.setChecked(True)
        self.continue_on_failure_check.stateChanged.connect(self._update_current_step)
        config_layout.addRow("", self.continue_on_failure_check)

        self.step_description_edit = QLineEdit()
        self.step_description_edit.setPlaceholderText("Optional step description")
        self.step_description_edit.textChanged.connect(self._update_current_step)
        config_layout.addRow("Step description:", self.step_description_edit)

        config_group.setLayout(config_layout)
        config_group.setEnabled(False)
        self.config_group = config_group
        layout.addWidget(config_group)

        # Dialog buttons
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save Workflow")
        self.save_btn.clicked.connect(self._validate_and_accept)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _populate_session_combo(self):
        """Populate session combo box with available sessions."""
        self.session_combo.clear()
        self.session_combo.addItem("-- Select a session --", None)

        # Group sessions by tab
        sessions_by_tab = {}
        for session in self.sessions:
            # Only include single_app sessions
            if session.type != SessionType.SINGLE_APP:
                continue

            tab_id = session.tab_id
            if tab_id not in sessions_by_tab:
                sessions_by_tab[tab_id] = []
            sessions_by_tab[tab_id].append(session)

        # Add sessions grouped by tab
        if self.tabs_collection:
            sorted_tabs = sorted(self.tabs_collection.tabs, key=lambda t: t.order)
            for tab in sorted_tabs:
                if tab.id in sessions_by_tab:
                    # Add separator
                    self.session_combo.addItem(f"─── {tab.icon} {tab.name} ───", None)
                    self.session_combo.setItemData(
                        self.session_combo.count() - 1,
                        Qt.ItemFlag.NoItemFlags,
                        Qt.ItemDataRole.UserRole - 1
                    )

                    # Add sessions from this tab
                    for session in sessions_by_tab[tab.id]:
                        display_text = f"  {session.icon} {session.name}"
                        self.session_combo.addItem(display_text, session.id)

    def _add_step(self):
        """Add a new step to the workflow."""
        session_id = self.session_combo.currentData()

        if not session_id:
            QMessageBox.warning(self, "No Session Selected", "Please select a session to add.")
            return

        # Find the session
        session = next((s for s in self.sessions if s.id == session_id), None)
        if not session:
            QMessageBox.warning(self, "Session Not Found", "Selected session not found.")
            return

        # Create workflow step
        step = WorkflowStep(
            order=len(self.workflow_steps),
            session_ref=session.id,
            delay_ms=0,
            continue_on_failure=True,
            description=f"Launch {session.name}"
        )

        self.workflow_steps.append(step)
        self._refresh_steps_list()

        # Select the newly added step
        self.steps_list.setCurrentRow(len(self.workflow_steps) - 1)

    def _remove_step(self):
        """Remove the selected step from the workflow."""
        current_row = self.steps_list.currentRow()

        if current_row < 0 or current_row >= len(self.workflow_steps):
            return

        self.workflow_steps.pop(current_row)

        # Reorder remaining steps
        for i, step in enumerate(self.workflow_steps):
            step.order = i

        self._refresh_steps_list()

    def _move_step_up(self):
        """Move the selected step up in the sequence."""
        current_row = self.steps_list.currentRow()

        if current_row <= 0:
            return

        # Swap steps
        self.workflow_steps[current_row], self.workflow_steps[current_row - 1] = \
            self.workflow_steps[current_row - 1], self.workflow_steps[current_row]

        # Update order
        self.workflow_steps[current_row].order = current_row
        self.workflow_steps[current_row - 1].order = current_row - 1

        self._refresh_steps_list()
        self.steps_list.setCurrentRow(current_row - 1)

    def _move_step_down(self):
        """Move the selected step down in the sequence."""
        current_row = self.steps_list.currentRow()

        if current_row < 0 or current_row >= len(self.workflow_steps) - 1:
            return

        # Swap steps
        self.workflow_steps[current_row], self.workflow_steps[current_row + 1] = \
            self.workflow_steps[current_row + 1], self.workflow_steps[current_row]

        # Update order
        self.workflow_steps[current_row].order = current_row
        self.workflow_steps[current_row + 1].order = current_row + 1

        self._refresh_steps_list()
        self.steps_list.setCurrentRow(current_row + 1)

    def _refresh_steps_list(self):
        """Refresh the steps list widget."""
        self.steps_list.clear()

        for i, step in enumerate(self.workflow_steps):
            # Find session for this step
            session = None
            if step.session_ref:
                session = next((s for s in self.sessions if s.id == step.session_ref), None)

            # Build display text
            if session:
                display_text = f"{i + 1}. {session.icon} {session.name}"
            else:
                display_text = f"{i + 1}. Unknown session"

            # Add delay info
            if step.delay_ms > 0:
                display_text += f" (wait {step.delay_ms}ms)"

            # Add failure handling info
            if not step.continue_on_failure:
                display_text += " [STOP ON FAILURE]"

            item = QListWidgetItem(display_text)
            self.steps_list.addItem(item)

    def _on_step_selected(self, row: int):
        """Handle step selection.

        Args:
            row: Selected row index
        """
        if row < 0 or row >= len(self.workflow_steps):
            self.config_group.setEnabled(False)
            self.remove_step_btn.setEnabled(False)
            self.move_up_btn.setEnabled(False)
            self.move_down_btn.setEnabled(False)
            return

        # Enable controls
        self.config_group.setEnabled(True)
        self.remove_step_btn.setEnabled(True)
        self.move_up_btn.setEnabled(row > 0)
        self.move_down_btn.setEnabled(row < len(self.workflow_steps) - 1)

        # Load step configuration
        step = self.workflow_steps[row]
        self.delay_spin.blockSignals(True)
        self.continue_on_failure_check.blockSignals(True)
        self.step_description_edit.blockSignals(True)

        self.delay_spin.setValue(step.delay_ms)
        self.continue_on_failure_check.setChecked(step.continue_on_failure)
        self.step_description_edit.setText(step.description or "")

        self.delay_spin.blockSignals(False)
        self.continue_on_failure_check.blockSignals(False)
        self.step_description_edit.blockSignals(False)

    def _update_current_step(self):
        """Update the currently selected step with UI values."""
        current_row = self.steps_list.currentRow()

        if current_row < 0 or current_row >= len(self.workflow_steps):
            return

        step = self.workflow_steps[current_row]
        step.delay_ms = self.delay_spin.value()
        step.continue_on_failure = self.continue_on_failure_check.isChecked()
        step.description = self.step_description_edit.text()

        self._refresh_steps_list()
        self.steps_list.setCurrentRow(current_row)

    def _load_workflow_data(self):
        """Load existing workflow data into UI."""
        if not self.workflow:
            return

        self.name_edit.setText(self.workflow.name)
        self.icon_edit.setText(self.workflow.icon)
        self.description_edit.setText(self.workflow.description)

        # Set tab selection
        if self.workflow.tab_id:
            for i in range(self.tab_combo.count()):
                if self.tab_combo.itemData(i) == self.workflow.tab_id:
                    self.tab_combo.setCurrentIndex(i)
                    break

        self._refresh_steps_list()

    def _validate_and_accept(self):
        """Validate workflow and accept dialog."""
        # Validate name
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a workflow name.")
            return

        # Validate steps
        if len(self.workflow_steps) == 0:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please add at least one step to the workflow."
            )
            return

        self.accept()

    def get_workflow(self) -> Workflow:
        """Get the workflow from the dialog.

        Returns:
            Workflow object
        """
        tab_id = self.tab_combo.currentData() or "uncategorized"

        if self.editing and self.workflow:
            # Update existing workflow
            self.workflow.name = self.name_edit.text().strip()
            self.workflow.icon = self.icon_edit.text().strip() or "🎯"
            self.workflow.description = self.description_edit.text().strip()
            self.workflow.tab_id = tab_id
            self.workflow.launch_sequence = self.workflow_steps
            self.workflow.updated_at = datetime.now()
            return self.workflow
        else:
            # Create new workflow
            return Workflow(
                id=str(uuid.uuid4()),
                name=self.name_edit.text().strip(),
                icon=self.icon_edit.text().strip() or "🎯",
                description=self.description_edit.text().strip(),
                tab_id=tab_id,
                type=SessionType.COMPOSITE_WORKFLOW,
                launch_sequence=self.workflow_steps,
                metadata={
                    "category_id": tab_id,
                    "tags": [],
                    "favorite": False,
                    "launch_count": 0,
                    "last_launched": None
                }
            )
