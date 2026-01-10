"""Category editor dialog for creating/editing hierarchical categories."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QComboBox, QMessageBox, QColorDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from typing import Optional

from ..core.tab import Tab, TabsCollection


class CategoryDialog(QDialog):
    """Dialog for creating/editing categories."""

    def __init__(self, parent=None, category: Optional[Tab] = None,
                 tabs_collection: Optional[TabsCollection] = None):
        """Initialize category dialog.

        Args:
            parent: Parent widget
            category: Optional category to edit (None for new category)
            tabs_collection: Collection of tabs for parent selection
        """
        super().__init__(parent)

        self.category = category
        self.editing = category is not None
        self.tabs_collection = tabs_collection
        self.selected_color: Optional[str] = None

        title = "Edit Category" if self.editing else "New Category"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)

        self._init_ui()

        if self.editing:
            self._load_category_data()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Form layout
        form_layout = QFormLayout()

        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)

        # Icon (emoji)
        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("📁")
        self.icon_edit.setMaxLength(4)  # Allow multi-char emojis
        form_layout.addRow("Icon (emoji):", self.icon_edit)

        # Parent category
        self.parent_combo = QComboBox()
        self._populate_parent_combo()
        form_layout.addRow("Parent Category:", self.parent_combo)

        # Color picker
        color_layout = QHBoxLayout()
        self.color_button = QPushButton("Choose Color (Optional)")
        self.color_button.clicked.connect(self._choose_color)
        color_layout.addWidget(self.color_button)

        self.color_preview = QLineEdit()
        self.color_preview.setReadOnly(True)
        self.color_preview.setMaximumWidth(100)
        self.color_preview.setPlaceholderText("No color")
        color_layout.addWidget(self.color_preview)

        self.clear_color_btn = QPushButton("Clear")
        self.clear_color_btn.clicked.connect(self._clear_color)
        color_layout.addWidget(self.clear_color_btn)

        form_layout.addRow("Color:", color_layout)

        layout.addLayout(form_layout)

        # Dialog buttons
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._validate_and_accept)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _populate_parent_combo(self):
        """Populate parent category combo box."""
        self.parent_combo.clear()
        self.parent_combo.addItem("(Root Level)", None)

        if not self.tabs_collection:
            return

        # Get root tabs and build hierarchy
        def add_category_recursive(tab: Tab, level: int = 0):
            """Add category and its children to combo box."""
            # Don't allow setting self as parent
            if self.editing and self.category and tab.id == self.category.id:
                return

            # Don't allow setting descendants as parent (would create cycle)
            if self.editing and self.category:
                descendants = self.tabs_collection.get_all_descendants(self.category.id)
                if any(d.id == tab.id for d in descendants):
                    return

            indent = "  " * level
            display_text = f"{indent}{tab.icon} {tab.name}"
            self.parent_combo.addItem(display_text, tab.id)

            # Add children
            children = self.tabs_collection.get_children(tab.id)
            for child in children:
                add_category_recursive(child, level + 1)

        # Add all root categories
        root_tabs = self.tabs_collection.get_root_tabs()
        for tab in root_tabs:
            add_category_recursive(tab)

    def _choose_color(self):
        """Open color picker dialog."""
        initial_color = QColor(self.selected_color) if self.selected_color else QColor(Qt.GlobalColor.white)
        color = QColorDialog.getColor(initial_color, self, "Choose Category Color")

        if color.isValid():
            self.selected_color = color.name()
            self._update_color_preview()

    def _clear_color(self):
        """Clear selected color."""
        self.selected_color = None
        self._update_color_preview()

    def _update_color_preview(self):
        """Update color preview display."""
        if self.selected_color:
            self.color_preview.setText(self.selected_color)
            self.color_preview.setStyleSheet(f"background-color: {self.selected_color};")
        else:
            self.color_preview.setText("")
            self.color_preview.setStyleSheet("")

    def _load_category_data(self):
        """Load existing category data into UI."""
        if not self.category:
            return

        self.name_edit.setText(self.category.name)
        self.icon_edit.setText(self.category.icon)

        # Set parent selection
        if self.category.parent_id:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == self.category.parent_id:
                    self.parent_combo.setCurrentIndex(i)
                    break

        # Set color
        if self.category.color:
            self.selected_color = self.category.color
            self._update_color_preview()

    def _validate_and_accept(self):
        """Validate category and accept dialog."""
        # Validate name
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a category name.")
            return

        self.accept()

    def get_category(self) -> Tab:
        """Get the category from the dialog.

        Returns:
            Tab object representing the category
        """
        parent_id = self.parent_combo.currentData()

        if self.editing and self.category:
            # Update existing category
            self.category.name = self.name_edit.text().strip()
            self.category.icon = self.icon_edit.text().strip() or "📁"
            self.category.parent_id = parent_id
            self.category.color = self.selected_color
            return self.category
        else:
            # Create new category
            return Tab(
                name=self.name_edit.text().strip(),
                icon=self.icon_edit.text().strip() or "📁",
                parent_id=parent_id,
                color=self.selected_color
            )
