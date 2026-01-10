"""Debug configuration for Context Launcher."""


class DebugConfig:
    """Global debug configuration."""

    _debug_mode = False

    @classmethod
    def set_debug_mode(cls, enabled: bool):
        """Set debug mode on/off.

        Args:
            enabled: True to enable debug mode, False to disable
        """
        cls._debug_mode = enabled

    @classmethod
    def is_debug_mode(cls) -> bool:
        """Check if debug mode is enabled.

        Returns:
            True if debug mode is enabled
        """
        return cls._debug_mode
