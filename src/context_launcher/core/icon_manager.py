"""Cross-platform icon extraction and management for applications."""

import sys
import os
from pathlib import Path
from typing import Optional, Dict
from PySide6.QtGui import QIcon, QPixmap, QImage
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFileIconProvider

from ..utils.logger import get_logger

logger = get_logger(__name__)


class IconManager:
    """Manages application icon extraction and caching across platforms."""

    # Known app names and their common executable names/bundle IDs
    KNOWN_APPS = {
        # Browsers
        "chrome": {
            "windows": ["chrome.exe", "Google Chrome"],
            "darwin": ["com.google.Chrome", "Google Chrome"],
            "display_name": "Google Chrome"
        },
        "firefox": {
            "windows": ["firefox.exe", "Mozilla Firefox"],
            "darwin": ["org.mozilla.firefox", "Firefox"],
            "display_name": "Mozilla Firefox"
        },
        "edge": {
            "windows": ["msedge.exe", "Microsoft Edge"],
            "darwin": ["com.microsoft.edgemac", "Microsoft Edge"],
            "display_name": "Microsoft Edge"
        },
        # Editors
        "vscode": {
            "windows": ["Code.exe", "Visual Studio Code"],
            "darwin": ["com.microsoft.VSCode", "Visual Studio Code"],
            "display_name": "Visual Studio Code"
        },
        # Apps
        "slack": {
            "windows": ["slack.exe", "Slack"],
            "darwin": ["com.tinyspeck.slackmacgap", "Slack"],
            "display_name": "Slack"
        },
        "spotify": {
            "windows": ["Spotify.exe", "Spotify"],
            "darwin": ["com.spotify.client", "Spotify"],
            "display_name": "Spotify"
        },
    }

    def __init__(self):
        """Initialize the icon manager."""
        self._icon_cache: Dict[str, QIcon] = {}
        self._file_icon_provider = QFileIconProvider()

    def get_app_icon(self, app_name: str, executable_path: str = "") -> Optional[QIcon]:
        """Get the icon for an application.

        Args:
            app_name: Name of the app (e.g., 'chrome', 'vscode', 'slack')
            executable_path: Optional path to executable for custom apps

        Returns:
            QIcon if found, None otherwise
        """
        # Check cache first
        cache_key = f"{app_name}:{executable_path}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        icon = None

        # Try to get icon based on platform
        if sys.platform == 'win32':
            icon = self._get_icon_windows(app_name, executable_path)
        elif sys.platform == 'darwin':
            icon = self._get_icon_macos(app_name, executable_path)

        # Cache the result (even if None, to avoid repeated lookups)
        if icon and not icon.isNull():
            self._icon_cache[cache_key] = icon
            return icon

        return None

    def _get_icon_windows(self, app_name: str, executable_path: str = "") -> Optional[QIcon]:
        """Get application icon on Windows.

        Args:
            app_name: Name of the app
            executable_path: Optional path to executable

        Returns:
            QIcon if found, None otherwise
        """
        try:
            # If we have a direct executable path, use it
            if executable_path and os.path.exists(executable_path):
                return self._extract_icon_from_exe(executable_path)

            # Try to find the executable for known apps
            if app_name.lower() in self.KNOWN_APPS:
                app_info = self.KNOWN_APPS[app_name.lower()]
                exe_names = app_info.get("windows", [])

                # Common installation paths
                search_paths = [
                    Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")),
                    Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")),
                    Path(os.environ.get("LOCALAPPDATA", "")),
                    Path(os.environ.get("APPDATA", "")),
                ]

                for search_path in search_paths:
                    if not search_path.exists():
                        continue
                    for exe_name in exe_names:
                        # Search recursively (limited depth)
                        found_path = self._find_executable_windows(search_path, exe_name)
                        if found_path:
                            return self._extract_icon_from_exe(str(found_path))

            return None

        except Exception as e:
            logger.debug(f"Failed to get Windows icon for {app_name}: {e}")
            return None

    def _find_executable_windows(self, search_path: Path, exe_name: str, max_depth: int = 3) -> Optional[Path]:
        """Find an executable in a directory tree.

        Args:
            search_path: Path to search in
            exe_name: Executable name to find
            max_depth: Maximum directory depth to search

        Returns:
            Path to executable if found, None otherwise
        """
        try:
            if max_depth <= 0:
                return None

            for item in search_path.iterdir():
                if item.is_file() and item.name.lower() == exe_name.lower():
                    return item
                elif item.is_dir() and not item.name.startswith('.'):
                    result = self._find_executable_windows(item, exe_name, max_depth - 1)
                    if result:
                        return result
        except PermissionError:
            pass
        except Exception as e:
            logger.debug(f"Error searching {search_path}: {e}")

        return None

    def _extract_icon_from_exe(self, exe_path: str) -> Optional[QIcon]:
        """Extract icon from a Windows executable.

        Args:
            exe_path: Path to the executable

        Returns:
            QIcon if successful, None otherwise
        """
        try:
            # Use QFileIconProvider for basic icon extraction
            file_info = Path(exe_path)
            if file_info.exists():
                from PySide6.QtCore import QFileInfo
                qfile_info = QFileInfo(str(file_info))
                icon = self._file_icon_provider.icon(qfile_info)
                if not icon.isNull():
                    return icon

            # Try using win32api for better icon extraction
            try:
                import win32gui
                import win32ui
                import win32con
                import win32api

                # Extract large icon
                large, small = win32gui.ExtractIconEx(exe_path, 0)
                if large:
                    # Convert to QIcon
                    hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                    hbmp = win32ui.CreateBitmap()
                    hbmp.CreateCompatibleBitmap(hdc, 48, 48)
                    hdc_mem = hdc.CreateCompatibleDC()
                    hdc_mem.SelectObject(hbmp)
                    hdc_mem.DrawIcon((0, 0), large[0])

                    # Get bitmap bits
                    bmpinfo = hbmp.GetInfo()
                    bmpstr = hbmp.GetBitmapBits(True)

                    # Create QImage from bitmap data
                    img = QImage(bmpstr, bmpinfo['bmWidth'], bmpinfo['bmHeight'],
                                QImage.Format.Format_ARGB32)
                    pixmap = QPixmap.fromImage(img)

                    # Cleanup
                    win32gui.DestroyIcon(large[0])
                    if small:
                        win32gui.DestroyIcon(small[0])

                    return QIcon(pixmap)

            except ImportError:
                logger.debug("win32gui not available, using basic icon extraction")
            except Exception as e:
                logger.debug(f"win32gui icon extraction failed: {e}")

        except Exception as e:
            logger.debug(f"Failed to extract icon from {exe_path}: {e}")

        return None

    def _get_icon_macos(self, app_name: str, executable_path: str = "") -> Optional[QIcon]:
        """Get application icon on macOS.

        Args:
            app_name: Name of the app
            executable_path: Optional path to executable/app bundle

        Returns:
            QIcon if found, None otherwise
        """
        try:
            from AppKit import NSWorkspace, NSImage
            from Foundation import NSURL

            workspace = NSWorkspace.sharedWorkspace()

            # If we have a direct path to an app bundle
            if executable_path:
                app_path = self._resolve_app_path_macos(executable_path)
                if app_path:
                    return self._extract_icon_from_app_macos(app_path)

            # Try to find the app for known apps
            if app_name.lower() in self.KNOWN_APPS:
                app_info = self.KNOWN_APPS[app_name.lower()]
                identifiers = app_info.get("darwin", [])

                for identifier in identifiers:
                    # Try as bundle identifier first
                    app_url = workspace.URLForApplicationWithBundleIdentifier_(identifier)
                    if app_url:
                        app_path = app_url.path()
                        return self._extract_icon_from_app_macos(app_path)

                    # Try as app name in /Applications
                    app_paths = [
                        f"/Applications/{identifier}.app",
                        f"/System/Applications/{identifier}.app",
                        os.path.expanduser(f"~/Applications/{identifier}.app"),
                    ]
                    for app_path in app_paths:
                        if os.path.exists(app_path):
                            return self._extract_icon_from_app_macos(app_path)

            return None

        except ImportError:
            logger.debug("AppKit not available on this platform")
            return None
        except Exception as e:
            logger.debug(f"Failed to get macOS icon for {app_name}: {e}")
            return None

    def _resolve_app_path_macos(self, path: str) -> Optional[str]:
        """Resolve a path to a macOS app bundle.

        Args:
            path: Path to executable or app bundle

        Returns:
            Path to .app bundle if found, None otherwise
        """
        path = os.path.expanduser(path)

        # If it's already an .app bundle
        if path.endswith('.app') and os.path.exists(path):
            return path

        # If it's an executable inside an app bundle
        if '.app/' in path:
            app_path = path.split('.app/')[0] + '.app'
            if os.path.exists(app_path):
                return app_path

        # Try to find the app bundle containing this executable
        path_obj = Path(path)
        for parent in path_obj.parents:
            if parent.suffix == '.app' and parent.exists():
                return str(parent)

        return None

    def _extract_icon_from_app_macos(self, app_path: str) -> Optional[QIcon]:
        """Extract icon from a macOS application bundle.

        Args:
            app_path: Path to the .app bundle

        Returns:
            QIcon if successful, None otherwise
        """
        try:
            from AppKit import NSWorkspace, NSImage
            from Foundation import NSData

            workspace = NSWorkspace.sharedWorkspace()

            # Get the app's icon
            ns_image = workspace.iconForFile_(app_path)
            if not ns_image:
                return None

            # Convert NSImage to QIcon
            # Get the largest available representation
            ns_image.setSize_((512, 512))

            # Get TIFF representation
            tiff_data = ns_image.TIFFRepresentation()
            if not tiff_data:
                return None

            # Convert to QPixmap
            qimage = QImage.fromData(bytes(tiff_data))
            if qimage.isNull():
                return None

            pixmap = QPixmap.fromImage(qimage)
            return QIcon(pixmap)

        except Exception as e:
            logger.debug(f"Failed to extract icon from {app_path}: {e}")
            return None

    def get_icon_for_session(self, session) -> Optional[QIcon]:
        """Get the appropriate icon for a session.

        Args:
            session: Session object

        Returns:
            QIcon if app icon found, None otherwise (use emoji fallback)
        """
        # Check if icon field explicitly specifies an app icon
        if session.icon.startswith("app:"):
            app_name = session.icon[4:]  # Remove "app:" prefix
            return self.get_app_icon(app_name)

        # Otherwise, try to auto-detect from the app being launched
        app_name = session.launch_config.app_name
        params = session.launch_config.parameters

        # Get executable path if available
        executable_path = params.get('executable_path', '')

        return self.get_app_icon(app_name, executable_path)

    @staticmethod
    def is_app_icon(icon_string: str) -> bool:
        """Check if an icon string specifies an app icon.

        Args:
            icon_string: The icon field value (e.g., "app:chrome" or "🌐")

        Returns:
            True if it's an app icon reference, False if it's an emoji
        """
        return icon_string.startswith("app:")

    @staticmethod
    def get_app_name_from_icon(icon_string: str) -> Optional[str]:
        """Extract app name from an app icon string.

        Args:
            icon_string: The icon field value (e.g., "app:chrome")

        Returns:
            App name if it's an app icon reference, None otherwise
        """
        if icon_string.startswith("app:"):
            return icon_string[4:]
        return None

    def clear_cache(self):
        """Clear the icon cache."""
        self._icon_cache.clear()


# Global icon manager instance
_icon_manager: Optional[IconManager] = None


def get_icon_manager() -> IconManager:
    """Get the global icon manager instance.

    Returns:
        IconManager instance
    """
    global _icon_manager
    if _icon_manager is None:
        _icon_manager = IconManager()
    return _icon_manager
