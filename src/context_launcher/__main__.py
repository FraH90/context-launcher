"""Main entry point for Context Launcher."""

import sys
from PySide6.QtWidgets import QApplication
from .utils.logger import setup_logging, get_logger
from .ui.main_window import MainWindow


def main():
    """Main entry point."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    logger.info("Starting Context Launcher v3.0")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Context Launcher")
    app.setOrganizationName("FraH")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
