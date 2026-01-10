"""Test window positioning with any running application on macOS."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_launcher.core.window_manager import WindowManager, WindowState
import psutil


def list_gui_apps():
    """List running GUI applications."""
    print("Looking for running GUI applications...")
    print()

    apps = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name']
            pid = proc.info['pid']

            # Filter for common GUI apps
            if name in ['Finder', 'Safari', 'Google Chrome', 'Firefox', 'Code',
                       'Visual Studio Code', 'Terminal', 'iTerm2', 'Slack',
                       'Discord', 'Spotify', 'Mail', 'Messages', 'Notes',
                       'Calendar', 'TextEdit', 'Pages', 'Numbers', 'Keynote']:
                apps.append((pid, name))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return apps


def test_app_window(pid, app_name):
    """Test window positioning for a specific app."""
    print("=" * 60)
    print(f"TESTING: {app_name} (PID: {pid})")
    print("=" * 60)
    print()

    wm = WindowManager()

    # Get monitor info
    monitors = wm.get_monitors()
    if not monitors:
        print("✗ No monitors detected")
        return False

    screen_width = monitors[0]['width']
    screen_height = monitors[0]['height']

    # Capture current state
    print("1. Capturing current window state...")
    initial_state = wm.get_window_state(pid, timeout=5.0)

    if not initial_state:
        print(f"   ✗ No visible window found for {app_name}")
        print(f"     This app may not have a main window or it may be minimized")
        return False

    print(f"   ✓ Window found:")
    print(f"     Position: ({initial_state.x}, {initial_state.y})")
    print(f"     Size: {initial_state.width}x{initial_state.height}")
    print()

    # Test moving window
    print("2. Testing window repositioning...")
    print("   Moving to center of screen...")

    new_x = (screen_width - 800) // 2
    new_y = (screen_height - 600) // 2

    test_state = WindowState(
        x=new_x,
        y=new_y,
        width=800,
        height=600,
        monitor_index=0
    )

    time.sleep(1)
    success = wm.set_window_state(pid, test_state, timeout=5.0)

    if not success:
        print("   ✗ Failed to move window")
        print("     Accessibility permissions may be required")
        return False

    print("   ✓ Window moved to center!")
    time.sleep(2)
    print()

    # Restore original position
    print("3. Restoring original position...")
    time.sleep(1)
    success = wm.set_window_state(pid, initial_state, timeout=5.0)

    if success:
        print("   ✓ Window restored!")
    else:
        print("   ✗ Failed to restore (but move worked)")

    print()
    return True


def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("GENERIC WINDOW POSITIONING TEST (macOS)")
    print("=" * 60)
    print()

    # List available apps
    apps = list_gui_apps()

    if not apps:
        print("No suitable GUI applications found running.")
        print("Please start an application (VS Code, Safari, Finder, etc.) and try again.")
        return

    print(f"Found {len(apps)} running GUI application(s):")
    for i, (pid, name) in enumerate(apps, 1):
        print(f"  {i}. {name} (PID: {pid})")

    print()

    # Test each app
    tested = 0
    successful = 0

    for pid, name in apps:
        if test_app_window(pid, name):
            successful += 1
        tested += 1

        if tested < len(apps):
            print()
            time.sleep(1)

    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Apps tested: {tested}")
    print(f"Successful: {successful}")
    print(f"Failed: {tested - successful}")
    print()

    if successful > 0:
        print("✅ Window positioning is working!")
        if successful < tested:
            print("⚠️  Some apps couldn't be positioned (may not have windows)")
    else:
        print("✗ Window positioning failed for all apps")
        print("   Please check accessibility permissions:")
        print("   System Settings > Privacy & Security > Accessibility")


if __name__ == '__main__':
    main()
