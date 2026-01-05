"""Custom tree widget with smart drag-and-drop validation."""

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt, Signal


class SmartTreeWidget(QTreeWidget):
    """Tree widget with intelligent drag-and-drop validation."""

    # Signal emitted when an item is successfully dropped
    # Arguments: (source_item, target_item, source_type, target_type)
    item_dropped = Signal(QTreeWidgetItem, QTreeWidgetItem, str, str)

    def __init__(self, parent=None):
        """Initialize smart tree widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

    def dropEvent(self, event):
        """Handle drop event with validation.

        Args:
            event: Drop event
        """
        # Get the item being dropped
        source_item = self.currentItem()
        if not source_item:
            event.ignore()
            return

        # Get the target item
        target_item = self.itemAt(event.position().toPoint())
        if not target_item:
            event.ignore()
            return

        # Get item types
        source_type = source_item.data(0, Qt.ItemDataRole.UserRole + 1)
        target_type = target_item.data(0, Qt.ItemDataRole.UserRole + 1)

        # Validate the drop based on logical rules
        if not self._is_valid_drop(source_type, target_type, source_item, target_item):
            event.ignore()
            return

        # Allow the drop
        super().dropEvent(event)

        # Emit signal to parent that we need to save changes
        self.item_dropped.emit(source_item, target_item, source_type, target_type)

    def _is_valid_drop(self, source_type: str, target_type: str,
                       source_item: QTreeWidgetItem, target_item: QTreeWidgetItem) -> bool:
        """Check if a drop operation is logically valid.

        Args:
            source_type: Type of source item ('category', 'session', 'workflow')
            target_type: Type of target item
            source_item: Source tree item
            target_item: Target tree item

        Returns:
            True if drop is valid, False otherwise
        """
        # Can't drop onto itself
        if source_item == target_item:
            return False

        # Can't drop a parent into its own child (would create cycle)
        if source_type == 'category' and target_type == 'category':
            # Check if target is a descendant of source
            current = target_item
            while current:
                if current == source_item:
                    return False
                current = current.parent()

        # Valid drops:
        # 1. Category -> Category (moving category to be child of another, if not circular)
        if source_type == 'category' and target_type == 'category':
            return True

        # 2. Session -> Category (moving session to a category)
        if source_type == 'session' and target_type == 'category':
            return True

        # 3. Workflow -> Category (moving workflow to a category)
        if source_type == 'workflow' and target_type == 'category':
            return True

        # Invalid drops:
        # - Category -> Session/Workflow (can't nest category under item)
        # - Session -> Session (can't nest session under session)
        # - Session -> Workflow (can't nest session under workflow)
        # - Workflow -> Session (can't nest workflow under session)
        # - Workflow -> Workflow (can't nest workflow under workflow)

        return False
