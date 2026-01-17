"""Main entry point for Context Launcher."""

import sys
import os
import argparse
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from .utils.logger import setup_logging, get_logger
from .ui.main_window import MainWindow
from .core.debug_config import DebugConfig

# Application metadata
APP_NAME = "Context Launcher"
APP_VERSION = "3.0"


def _setup_macos_app_name():
    """Set the application name in macOS menu bar when running as a script.
    
    On macOS, Qt reads the application name from argv[0] for the menu bar.
    We modify sys.argv[0] to show our app name instead of 'Python'.
    """
    # Trick 1: Modify argv[0] - Qt uses this for the menu bar name on macOS
    # This must be done BEFORE QApplication is created
    sys.argv[0] = APP_NAME
    
    try:
        from Foundation import NSBundle
        from AppKit import NSApplication, NSImage, NSProcessInfo

        # Trick 2: Try to modify the process name
        try:
            NSProcessInfo.processInfo().setProcessName_(APP_NAME)
        except Exception:
            pass

        # Trick 3: Set the app name in bundle info (may not work for scripts)
        bundle = NSBundle.mainBundle()
        info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
        if info:
            info['CFBundleName'] = APP_NAME
            info['CFBundleDisplayName'] = APP_NAME

        # Set activation policy to regular app (shows in dock)
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(0)  # NSApplicationActivationPolicyRegular

        # Set dock icon
        resources_dir = Path(__file__).parent / "resources"
        icon_path = resources_dir / "icon.icns"
        if icon_path.exists():
            icon = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
            if icon:
                app.setApplicationIconImage_(icon)

    except ImportError:
        pass  # PyObjC not available
    except Exception:
        pass  # Silently ignore errors


def _get_app_icon() -> QIcon:
    """Get the application icon.

    Returns:
        QIcon for the application
    """
    # Try to load icon from resources folder
    resources_dir = Path(__file__).parent / "resources"

    # Check for various icon formats
    icon_names = ["icon.icns", "icon.ico", "icon.png", "icon.svg"]
    for icon_name in icon_names:
        icon_path = resources_dir / icon_name
        if icon_path.exists():
            return QIcon(str(icon_path))

    # Fallback: create an icon from emoji (will be blank but at least won't crash)
    return QIcon()


def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Context Launcher - Workflow Management")
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (shows all message boxes and verbose logging)'
    )
    args, unknown = parser.parse_known_args()

    # Set debug mode globally
    DebugConfig.set_debug_mode(args.debug)

    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    logger.info("Starting Context Launcher v3.0")
    if args.debug:
        logger.info("Debug mode enabled")

    # On macOS, set the app name before creating QApplication
    if sys.platform == 'darwin':
        _setup_macos_app_name()

    # Create Qt application (pass remaining args to Qt)
    app = QApplication(sys.argv[:1] + unknown)
    app.setApplicationName("Context Launcher")
    app.setApplicationDisplayName("Context Launcher")
    app.setOrganizationName("FraH")

    # Set application icon (for dock/taskbar)
    app_icon = _get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Create and show main window
    window = MainWindow()

    # Also set the icon on the window itself
    if not app_icon.isNull():
        window.setWindowIcon(app_icon)

    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
