"""Simple test for monitor detection on macOS."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_launcher.core.window_manager import WindowManager


def test_monitors():
    """Test basic monitor detection."""
    print("Testing macOS monitor detection...")
    print()

    try:
        wm = WindowManager()
        monitors = wm.get_monitors()

        print(f"Found {len(monitors)} monitor(s):")
        print()

        for monitor in monitors:
            primary = " [PRIMARY]" if monitor['is_primary'] else ""
            print(f"Monitor {monitor['index']}{primary}:")
            print(f"  Position: ({monitor['x']}, {monitor['y']})")
            print(f"  Size: {monitor['width']}x{monitor['height']}")
            print(f"  Display ID: {monitor.get('display_id', 'N/A')}")
            print()

        if monitors:
            print("✓ Monitor detection working!")
        else:
            print("✗ No monitors detected")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_monitors()
