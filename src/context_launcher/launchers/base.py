"""Base launcher classes and data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
import logging


class AppType(Enum):
    """Application type categories."""
    BROWSER = "browser"
    EDITOR = "editor"
    COMMUNICATION = "communication"
    GENERIC = "generic"


@dataclass
class LaunchConfig:
    """Configuration for launching an application."""
    app_type: AppType
    app_name: str  # chrome, firefox, vscode, etc.
    parameters: Dict[str, Any]  # App-specific parameters
    platform: str  # win32, darwin, linux

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LaunchConfig':
        """Create LaunchConfig from dictionary."""
        return cls(
            app_type=AppType(data['app_type']),
            app_name=data['app_name'],
            parameters=data.get('parameters', {}),
            platform=data.get('platform', 'win32')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'app_type': self.app_type.value,
            'app_name': self.app_name,
            'parameters': self.parameters,
            'platform': self.platform
        }


@dataclass
class LaunchResult:
    """Result of a launch operation."""
    success: bool
    message: str
    process_id: Optional[int] = None
    error: Optional[Exception] = None

    @classmethod
    def success_result(cls, message: str, process_id: Optional[int] = None) -> 'LaunchResult':
        """Create a successful result."""
        return cls(success=True, message=message, process_id=process_id)

    @classmethod
    def error_result(cls, message: str, error: Optional[Exception] = None) -> 'LaunchResult':
        """Create an error result."""
        return cls(success=False, message=message, error=error)


class LaunchError(Exception):
    """Base exception for launch errors."""
    pass


class ExecutableNotFoundError(LaunchError):
    """Executable path not found."""
    pass


class ConfigurationError(LaunchError):
    """Invalid configuration."""
    pass


class BaseLauncher(ABC):
    """Abstract base class for all launchers."""

    def __init__(self, config: LaunchConfig):
        """Initialize launcher with configuration.

        Args:
            config: Launch configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"context_launcher.{self.__class__.__name__}")

    @abstractmethod
    def launch(self) -> LaunchResult:
        """Launch the application with configured parameters.

        Returns:
            LaunchResult with success status and details
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate launch configuration.

        Returns:
            True if configuration is valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass

    @abstractmethod
    def get_executable_path(self) -> str:
        """Get platform-specific executable path.

        Returns:
            Path to executable

        Raises:
            ExecutableNotFoundError: If executable not found
        """
        pass

    def supports_state_capture(self) -> bool:
        """Check if this launcher supports state capture.

        Returns:
            True if state capture is supported
        """
        return False

    def _log_launch(self, message: str):
        """Log launch information."""
        self.logger.info(message)

    def _log_error(self, message: str, exc: Optional[Exception] = None):
        """Log error information."""
        if exc:
            self.logger.error(message, exc_info=exc)
        else:
            self.logger.error(message)
