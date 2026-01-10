"""Debug script to see what windows are available on macOS."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
)


def list_all_windows():
    """List all windows on the system."""
    print("Listing all on-screen windows...")
    print("=" * 80)

    window_list = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )

    if not window_list:
        print("No windows found")
        return

    print(f"Found {len(window_list)} windows\n")

    for i, window in enumerate(window_list):
        pid = window.get('kCGWindowOwnerPID', 'N/A')
        name = window.get('kCGWindowOwnerName', 'N/A')
        title = window.get('kCGWindowName', '')
        layer = window.get('kCGWindowLayer', 'N/A')
        on_screen = window.get('kCGWindowIsOnscreen', False)
        bounds = window.get('kCGWindowBounds', {})

        width = bounds.get('Width', 0) if bounds else 0
        height = bounds.get('Height', 0) if bounds else 0

        # Filter for main application windows only
        if width > 100 and height > 100:  # Reasonable window size
            print(f"Window {i}:")
            print(f"  Owner: {name} (PID: {pid})")
            if title:
                print(f"  Title: {title}")
            print(f"  Size: {width}x{height}")
            print(f"  Layer: {layer}")
            print(f"  On Screen: {on_screen}")
            print(f"  Bounds: {bounds}")
            print()


if __name__ == '__main__':
    list_all_windows()
