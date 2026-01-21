"""Session data models using Pydantic."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class SessionType(str, Enum):
    """Type of session."""
    SINGLE_APP = "single_app"
    COMPOSITE_WORKFLOW = "composite_workflow"


class TabType(str, Enum):
    """Type of browser tab."""
    URL = "url"
    YOUTUBE = "youtube"


class Tab(BaseModel):
    """Browser tab configuration."""
    type: TabType
    url: Optional[str] = None
    channel_handle: Optional[str] = Field(None, alias="channelHandle")
    pinned: bool = False

    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase


class SessionMetadata(BaseModel):
    """Metadata about a session."""
    category_id: str = "uncategorized"
    tags: List[str] = Field(default_factory=list)
    favorite: bool = False
    launch_count: int = 0
    last_launched: Optional[datetime] = None
    window_state: Optional[Dict[str, Any]] = None  # Saved window position/size


class LaunchConfiguration(BaseModel):
    """Launch configuration for an application."""
    app_type: str  # browser, editor, communication, generic
    app_name: str  # chrome, firefox, vscode, etc.
    parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"  # Allow extra fields for flexibility


class Session(BaseModel):
    """Session model representing a single application launch configuration."""
    version: str = "3.0"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    icon: str = "🌐"  # Can be "app:appname" for app icon, or emoji for direct icon
    fallback_icon: str = "🌐"  # Emoji to use if app icon can't be loaded
    description: str = ""
    tab_id: str = "uncategorized"  # References the tab this session belongs to
    type: SessionType = SessionType.SINGLE_APP
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)
    launch_config: LaunchConfiguration

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode='json', by_alias=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create Session from dictionary."""
        return cls.model_validate(data)

    def update_launch_stats(self):
        """Update launch statistics."""
        self.metadata.launch_count += 1
        self.metadata.last_launched = datetime.now()
        self.updated_at = datetime.now()


class WorkflowStep(BaseModel):
    """A step in a composite workflow."""
    order: int
    delay_ms: int = 0
    session_ref: Optional[str] = None  # Reference to existing session ID
    inline_config: Optional[LaunchConfiguration] = None  # Or inline launch config
    continue_on_failure: bool = True  # Whether to continue if this step fails
    description: str = ""  # Optional description of what this step does


class Workflow(BaseModel):
    """Composite workflow that launches multiple applications."""
    version: str = "3.0"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    icon: str = "🎯"
    description: str = ""
    tab_id: str = "uncategorized"  # References the tab this workflow belongs to
    type: SessionType = SessionType.COMPOSITE_WORKFLOW
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)
    launch_sequence: List[WorkflowStep] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(mode='json', by_alias=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """Create Workflow from dictionary."""
        return cls.model_validate(data)

    def update_launch_stats(self):
        """Update launch statistics."""
        self.metadata.launch_count += 1
        self.metadata.last_launched = datetime.now()
        self.updated_at = datetime.now()


# Helper functions for creating sessions

def create_browser_session(
    name: str,
    browser: str,
    tabs: List[Dict[str, Any]],
    icon: str = "🌐",
    profile: str = "",
    tab_id: str = "uncategorized"
) -> Session:
    """Helper to create a browser session.

    Args:
        name: Session name
        browser: Browser name (chrome, firefox, edge)
        tabs: List of tab dictionaries with 'type' and 'url'
        icon: Session icon (emoji)
        profile: Browser profile name
        tab_id: Tab ID this session belongs to

    Returns:
        Session instance
    """
    return Session(
        name=name,
        icon=icon,
        description=f"{browser.capitalize()} session with {len(tabs)} tab(s)",
        tab_id=tab_id,
        metadata=SessionMetadata(category_id=tab_id),  # Keep for backward compatibility
        launch_config=LaunchConfiguration(
            app_type="browser",
            app_name=browser,
            parameters={
                "tabs": tabs,
                "profile": profile,
                "use_selenium": False
            }
        )
    )


def create_vscode_session(
    name: str,
    workspace_path: str,
    icon: str = "💻",
    tab_id: str = "uncategorized"
) -> Session:
    """Helper to create a VS Code session.

    Args:
        name: Session name
        workspace_path: Path to workspace or folder
        icon: Session icon
        tab_id: Tab ID this session belongs to

    Returns:
        Session instance
    """
    return Session(
        name=name,
        icon=icon,
        description=f"VS Code workspace: {workspace_path}",
        tab_id=tab_id,
        metadata=SessionMetadata(category_id=tab_id),
        launch_config=LaunchConfiguration(
            app_type="editor",
            app_name="vscode",
            parameters={
                "workspace": workspace_path
            }
        )
    )


def create_generic_app_session(
    name: str,
    app_name: str,
    executable_path: str,
    arguments: Optional[List[str]] = None,
    icon: str = "⚙️",
    tab_id: str = "uncategorized"
) -> Session:
    """Helper to create a generic application session.

    Args:
        name: Session name
        app_name: Application identifier (for factory)
        executable_path: Path to executable
        arguments: Optional command-line arguments
        icon: Session icon
        tab_id: Tab ID this session belongs to

    Returns:
        Session instance
    """
    return Session(
        name=name,
        icon=icon,
        description=f"Launch {name}",
        tab_id=tab_id,
        metadata=SessionMetadata(category_id=tab_id),
        launch_config=LaunchConfiguration(
            app_type="generic",
            app_name=app_name,
            parameters={
                "executable_path": executable_path,
                "arguments": arguments or []
            }
        )
    )


def create_uwp_session(
    name: str,
    app_name: str,
    aumid: Optional[str] = None,
    protocol: Optional[str] = None,
    icon: str = "🪟",
    tab_id: str = "uncategorized"
) -> Session:
    """Helper to create a UWP/Store app session (Windows only).

    Args:
        name: Session name
        app_name: UWP app identifier (key in UWP_APP_REGISTRY)
        aumid: Optional explicit Application User Model ID
        protocol: Optional protocol URI (e.g., 'calculator:', 'ms-photos:')
        icon: Session icon
        tab_id: Tab ID this session belongs to

    Returns:
        Session instance
    """
    parameters = {}
    if aumid:
        parameters['aumid'] = aumid
    if protocol:
        parameters['protocol'] = protocol

    return Session(
        name=name,
        icon=icon,
        description=f"Launch {name} (Windows Store app)",
        tab_id=tab_id,
        metadata=SessionMetadata(category_id=tab_id),
        launch_config=LaunchConfiguration(
            app_type="uwp",
            app_name=app_name,
            parameters=parameters
        )
    )
