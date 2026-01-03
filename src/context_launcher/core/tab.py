"""Tab data models and management."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid


class Tab(BaseModel):
    """User-defined tab/category for organizing sessions (supports hierarchy)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    icon: str = "📁"
    order: int = 0
    parent_id: Optional[str] = None  # For hierarchical categories
    color: Optional[str] = None  # Optional color for visual distinction
    expanded: bool = True  # Whether category is expanded in tree view
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tab':
        """Create Tab from dictionary."""
        return cls.model_validate(data)

    def is_child_of(self, parent_id: str) -> bool:
        """Check if this tab is a child of the given parent.

        Args:
            parent_id: ID of potential parent

        Returns:
            True if this tab's parent_id matches
        """
        return self.parent_id == parent_id

    def is_root(self) -> bool:
        """Check if this is a root-level category.

        Returns:
            True if parent_id is None
        """
        return self.parent_id is None


class TabsCollection(BaseModel):
    """Collection of tabs with metadata."""
    version: str = "3.0"
    tabs: List[Tab] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TabsCollection':
        """Create TabsCollection from dictionary."""
        return cls.model_validate(data)

    def get_tab_by_id(self, tab_id: str) -> Optional[Tab]:
        """Get tab by ID."""
        for tab in self.tabs:
            if tab.id == tab_id:
                return tab
        return None

    def add_tab(self, tab: Tab):
        """Add a new tab to the collection."""
        # Set order to be at the end
        if self.tabs:
            tab.order = max(t.order for t in self.tabs) + 1
        else:
            tab.order = 0
        self.tabs.append(tab)

    def remove_tab(self, tab_id: str) -> bool:
        """Remove a tab by ID.

        Returns:
            True if tab was removed, False if not found
        """
        for i, tab in enumerate(self.tabs):
            if tab.id == tab_id:
                self.tabs.pop(i)
                return True
        return False

    def reorder_tabs(self, tab_ids: List[str]):
        """Reorder tabs based on provided ID list."""
        # Create a mapping of tab_id to tab
        tab_map = {tab.id: tab for tab in self.tabs}

        # Rebuild tabs list in new order
        self.tabs = []
        for order, tab_id in enumerate(tab_ids):
            if tab_id in tab_map:
                tab = tab_map[tab_id]
                tab.order = order
                self.tabs.append(tab)

    def get_root_tabs(self) -> List[Tab]:
        """Get all root-level tabs (no parent).

        Returns:
            List of root tabs sorted by order
        """
        return sorted([t for t in self.tabs if t.is_root()], key=lambda t: t.order)

    def get_children(self, parent_id: str) -> List[Tab]:
        """Get all child tabs of a given parent.

        Args:
            parent_id: ID of parent tab

        Returns:
            List of child tabs sorted by order
        """
        return sorted([t for t in self.tabs if t.is_child_of(parent_id)], key=lambda t: t.order)

    def get_all_descendants(self, tab_id: str) -> List[Tab]:
        """Get all descendants of a tab (recursive).

        Args:
            tab_id: ID of parent tab

        Returns:
            List of all descendant tabs
        """
        descendants = []
        children = self.get_children(tab_id)
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_all_descendants(child.id))
        return descendants

    def move_tab(self, tab_id: str, new_parent_id: Optional[str]):
        """Move a tab to a new parent category.

        Args:
            tab_id: ID of tab to move
            new_parent_id: ID of new parent (None for root level)
        """
        tab = self.get_tab_by_id(tab_id)
        if tab:
            tab.parent_id = new_parent_id
            tab.updated_at = datetime.now()

    def update_expanded_state(self, tab_id: str, expanded: bool):
        """Update the expanded state of a category.

        Args:
            tab_id: ID of tab
            expanded: New expanded state
        """
        tab = self.get_tab_by_id(tab_id)
        if tab:
            tab.expanded = expanded
            tab.updated_at = datetime.now()


# Helper functions

def create_default_tabs() -> TabsCollection:
    """Create default tabs for new installations."""
    return TabsCollection(
        tabs=[
            Tab(id="work", name="Work", icon="💼", order=0),
            Tab(id="entertainment", name="Entertainment", icon="🎮", order=1),
            Tab(id="personal", name="Personal", icon="🧠", order=2),
            Tab(id="uncategorized", name="Uncategorized", icon="📁", order=999),
        ]
    )
