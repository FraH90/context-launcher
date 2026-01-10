"""Main entry point for Context Launcher."""

import sys
import argparse
from PySide6.QtWidgets import QApplication
from .utils.logger import setup_logging, get_logger
from .ui.main_window import MainWindow
from .core.debug_config import DebugConfig


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

    # Create Qt application (pass remaining args to Qt)
    app = QApplication(sys.argv[:1] + unknown)
    app.setApplicationName("Context Launcher")
    app.setOrganizationName("FraH")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
