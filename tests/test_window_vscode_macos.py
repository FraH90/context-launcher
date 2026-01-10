"""Test window positioning with VS Code on macOS."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_launcher.core.window_manager import WindowManager, WindowState
from context_launcher.launchers.base import LaunchConfig, AppType
from context_launcher.launchers.editors.vscode import VSCodeLauncher


def main():
    """Test window positioning with VS Code."""
    print("=" * 60)
    print("VS CODE WINDOW POSITIONING TEST (macOS)")
    print("=" * 60)
    print()

    # Test monitor detection
    print("1. Testing monitor detection...")
    wm = WindowManager()
    monitors = wm.get_monitors()

    if not monitors:
        print("   ✗ No monitors detected!")
        return

    print(f"   ✓ Found {len(monitors)} monitor(s)")

    screen_width = monitors[0]['width']
    screen_height = monitors[0]['height']
    print(f"   Screen: {screen_width}x{screen_height}")
    print()

    # Launch VS Code
    print("2. Launching VS Code with this project...")
    config = LaunchConfig(
        app_type=AppType.EDITOR,
        app_name="vscode",
        parameters={
            "folder": str(Path(__file__).parent.parent),
            "new_window": True
        },
        platform=sys.platform
    )

    launcher = VSCodeLauncher(config)
    result = launcher.launch()

    if not result.success:
        print(f"   ✗ Failed: {result.message}")
        return

    pid = result.process_id
    print(f"   ✓ VS Code launched (PID: {pid})")
    print()

    # Wait for window to appear
    print("3. Waiting for window to appear (3 seconds)...")
    time.sleep(3)
    print()

    # Capture initial window state
    print("4. Capturing initial window state...")
    initial_state = wm.get_window_state(pid, timeout=10.0)

    if not initial_state:
        print("   ✗ Failed to capture window state")
        print("   The window may not have appeared yet or VS Code is not running")
        return

    print(f"   ✓ Window captured:")
    print(f"     Position: ({initial_state.x}, {initial_state.y})")
    print(f"     Size: {initial_state.width}x{initial_state.height}")
    print(f"     Monitor: {initial_state.monitor_index}")
    print()

    # Test 1: Move to top-left corner
    print("5. TEST 1: Moving to top-left corner (100, 100)...")
    test1_state = WindowState(
        x=100,
        y=100,
        width=800,
        height=600,
        monitor_index=0
    )

    time.sleep(1)
    success = wm.set_window_state(pid, test1_state, timeout=5.0)

    if success:
        print("   ✓ Window moved to top-left!")
        print("     You should see VS Code window move to top-left corner")
    else:
        print("   ✗ Failed to move window")
        print("     Check if accessibility permissions are enabled:")
        print("     System Settings > Privacy & Security > Accessibility")
        return

    time.sleep(2)
    print()

    # Test 2: Move to right side
    print("6. TEST 2: Moving to right side...")
    test2_state = WindowState(
        x=screen_width - 900,
        y=100,
        width=800,
        height=600,
        monitor_index=0
    )

    time.sleep(1)
    success = wm.set_window_state(pid, test2_state, timeout=5.0)

    if success:
        print("   ✓ Window moved to right side!")
    else:
        print("   ✗ Failed to move window")
        return

    time.sleep(2)
    print()

    # Test 3: Make it larger
    print("7. TEST 3: Resizing to larger size...")
    test3_state = WindowState(
        x=200,
        y=150,
        width=1000,
        height=700,
        monitor_index=0
    )

    time.sleep(1)
    success = wm.set_window_state(pid, test3_state, timeout=5.0)

    if success:
        print("   ✓ Window resized!")
    else:
        print("   ✗ Failed to resize window")
        return

    time.sleep(2)
    print()

    # Test 4: Restore original position
    print("8. TEST 4: Restoring original position...")
    print(f"   Restoring to: ({initial_state.x}, {initial_state.y}) {initial_state.width}x{initial_state.height}")

    time.sleep(1)
    success = wm.set_window_state(pid, initial_state, timeout=5.0)

    if success:
        print("   ✓ Window restored to original position!")
    else:
        print("   ✗ Failed to restore window")
        return

    print()
    print("=" * 60)
    print("ALL TESTS PASSED! ✅")
    print("=" * 60)
    print()
    print("Summary:")
    print("  ✅ Monitor detection working")
    print("  ✅ Window capture working")
    print("  ✅ Window positioning working")
    print("  ✅ Window resizing working")
    print("  ✅ State restoration working")
    print()
    print("Window positioning is fully functional on macOS!")


if __name__ == '__main__':
    main()
