"""Test window capture (read-only, no permissions needed) on macOS."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_launcher.core.window_manager import WindowManager
import psutil


def main():
    """Test window capture for all running apps."""
    print("\n" + "=" * 60)
    print("WINDOW CAPTURE TEST (Read-Only - No Permissions Needed)")
    print("=" * 60)
    print()

    wm = WindowManager()

    # Get monitors
    print("MONITOR DETECTION:")
    print("-" * 60)
    monitors = wm.get_monitors()

    if not monitors:
        print("✗ No monitors detected")
        return

    for monitor in monitors:
        primary = " [PRIMARY]" if monitor['is_primary'] else ""
        print(f"Monitor {monitor['index']}{primary}:")
        print(f"  Position: ({monitor['x']}, {monitor['y']})")
        print(f"  Size: {monitor['width']}x{monitor['height']}")
        print()

    # Find GUI applications
    print("SCANNING FOR GUI APPLICATIONS:")
    print("-" * 60)

    gui_apps = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name']
            pid = proc.info['pid']

            # Check if app has a visible window
            state = wm.get_window_state(pid, timeout=0.5)
            if state:
                gui_apps.append((pid, name, state))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if not gui_apps:
        print("No GUI applications with visible windows found.")
        return

    print(f"Found {len(gui_apps)} application(s) with visible windows:\n")

    # Display info for each app
    for pid, name, state in sorted(gui_apps, key=lambda x: x[1]):
        print(f"• {name} (PID: {pid})")
        print(f"  Position: ({state.x}, {state.y})")
        print(f"  Size: {state.width}x{state.height}")
        print(f"  Monitor: {state.monitor_index}")
        print()

    print("=" * 60)
    print("RESULTS:")
    print("=" * 60)
    print(f"✅ Monitor detection: Working")
    print(f"✅ Window enumeration: Working")
    print(f"✅ Window capture: Working")
    print(f"✅ Found {len(gui_apps)} application window(s)")
    print()
    print("Note: Window positioning requires accessibility permissions.")
    print("This test only captures window states (read-only operation).")
    print()


if __name__ == '__main__':
    main()
