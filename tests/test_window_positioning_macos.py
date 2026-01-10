"""Test window positioning system on macOS."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_launcher.core.window_manager import WindowManager, WindowState
from context_launcher.launchers.base import LaunchConfig, AppType
from context_launcher.launchers.browsers.chrome import ChromeLauncher
from context_launcher.launchers.editors.vscode import VSCodeLauncher


def test_monitor_detection():
    """Test monitor detection on macOS."""
    print("=" * 60)
    print("MONITOR DETECTION TEST")
    print("=" * 60)

    try:
        wm = WindowManager()
        monitors = wm.get_monitors()

        print(f"✓ Found {len(monitors)} monitor(s)")
        for monitor in monitors:
            primary = " (PRIMARY)" if monitor['is_primary'] else ""
            print(f"\n  Monitor {monitor['index']}{primary}:")
            print(f"    Position: ({monitor['x']}, {monitor['y']})")
            print(f"    Size: {monitor['width']}x{monitor['height']}")
            print(f"    Display ID: {monitor.get('display_id', 'N/A')}")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    print()


def test_chrome_window_capture():
    """Test capturing Chrome window position."""
    print("=" * 60)
    print("CHROME WINDOW CAPTURE TEST")
    print("=" * 60)

    try:
        # Launch Chrome
        config = LaunchConfig(
            app_type=AppType.BROWSER,
            app_name="chrome",
            parameters={
                "tabs": [
                    {"type": "url", "url": "https://www.google.com"}
                ]
            },
            platform=sys.platform
        )

        launcher = ChromeLauncher(config)
        result = launcher.launch()

        if not result.success:
            print(f"✗ Failed to launch Chrome: {result.message}")
            return

        print(f"✓ Chrome launched (PID: {result.process_id})")
        print("  Waiting 3 seconds for window to appear...")
        time.sleep(3)

        # Capture window state
        wm = WindowManager()
        window_state = wm.get_window_state(result.process_id, timeout=10.0)

        if window_state:
            print(f"✓ Window state captured:")
            print(f"    Position: ({window_state.x}, {window_state.y})")
            print(f"    Size: {window_state.width}x{window_state.height}")
            print(f"    Monitor: {window_state.monitor_index}")
            return window_state, result.process_id
        else:
            print(f"✗ Failed to capture window state")
            return None, None

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    print()


def test_chrome_window_positioning(captured_state, pid):
    """Test setting Chrome window position."""
    print("=" * 60)
    print("CHROME WINDOW POSITIONING TEST")
    print("=" * 60)

    if not captured_state or not pid:
        print("✗ Skipping (no captured state)")
        return

    try:
        # Create a new position (move to top-left quarter of screen)
        new_state = WindowState(
            x=100,
            y=100,
            width=800,
            height=600,
            monitor_index=0
        )

        print(f"  Moving window to ({new_state.x}, {new_state.y})")
        print(f"  Resizing to {new_state.width}x{new_state.height}")
        print("  Waiting 2 seconds...")
        time.sleep(2)

        wm = WindowManager()
        success = wm.set_window_state(pid, new_state, timeout=5.0)

        if success:
            print("✓ Window position set successfully")
            print("  Waiting 2 seconds...")
            time.sleep(2)

            # Restore original position
            print(f"\n  Restoring original position...")
            print(f"    Position: ({captured_state.x}, {captured_state.y})")
            print(f"    Size: {captured_state.width}x{captured_state.height}")
            time.sleep(1)

            success = wm.set_window_state(pid, captured_state, timeout=5.0)

            if success:
                print("✓ Window restored to original position")
            else:
                print("✗ Failed to restore original position")
        else:
            print("✗ Failed to set window position")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    print()


def test_vscode_window_positioning():
    """Test VS Code window positioning."""
    print("=" * 60)
    print("VS CODE WINDOW POSITIONING TEST")
    print("=" * 60)

    try:
        # Launch VS Code
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
            print(f"✗ Failed to launch VS Code: {result.message}")
            return

        print(f"✓ VS Code launched (PID: {result.process_id})")
        print("  Waiting 3 seconds for window to appear...")
        time.sleep(3)

        # Capture initial state
        wm = WindowManager()
        initial_state = wm.get_window_state(result.process_id, timeout=10.0)

        if not initial_state:
            print(f"✗ Failed to capture initial window state")
            return

        print(f"✓ Initial window state captured:")
        print(f"    Position: ({initial_state.x}, {initial_state.y})")
        print(f"    Size: {initial_state.width}x{initial_state.height}")

        # Move to right side of screen
        new_state = WindowState(
            x=900,
            y=100,
            width=700,
            height=800,
            monitor_index=0
        )

        print(f"\n  Moving window to ({new_state.x}, {new_state.y})")
        print(f"  Resizing to {new_state.width}x{new_state.height}")
        time.sleep(2)

        success = wm.set_window_state(result.process_id, new_state, timeout=5.0)

        if success:
            print("✓ VS Code window positioned successfully")
        else:
            print("✗ Failed to position VS Code window")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    print()


def test_multi_window_scenario():
    """Test positioning multiple windows."""
    print("=" * 60)
    print("MULTI-WINDOW SCENARIO TEST")
    print("=" * 60)
    print("This test will:")
    print("  1. Launch Chrome on the left side")
    print("  2. Launch VS Code on the right side")
    print("  3. Demonstrate saved window positions")
    print()

    try:
        wm = WindowManager()
        monitors = wm.get_monitors()

        if not monitors:
            print("✗ No monitors detected")
            return

        screen_width = monitors[0]['width']
        screen_height = monitors[0]['height']

        # Launch Chrome on left side
        print("Launching Chrome on left side...")
        chrome_config = LaunchConfig(
            app_type=AppType.BROWSER,
            app_name="chrome",
            parameters={
                "tabs": [
                    {"type": "url", "url": "https://github.com"}
                ]
            },
            platform=sys.platform
        )

        chrome_launcher = ChromeLauncher(chrome_config)
        chrome_result = chrome_launcher.launch()

        if not chrome_result.success:
            print(f"✗ Failed to launch Chrome")
            return

        time.sleep(3)

        # Position Chrome on left half
        chrome_state = WindowState(
            x=0,
            y=100,
            width=screen_width // 2 - 20,
            height=screen_height - 200,
            monitor_index=0
        )

        wm.set_window_state(chrome_result.process_id, chrome_state)
        print(f"✓ Chrome positioned on left side")

        time.sleep(2)

        # Launch VS Code on right side
        print("Launching VS Code on right side...")
        vscode_config = LaunchConfig(
            app_type=AppType.EDITOR,
            app_name="vscode",
            parameters={
                "folder": str(Path(__file__).parent.parent),
                "new_window": True
            },
            platform=sys.platform
        )

        vscode_launcher = VSCodeLauncher(vscode_config)
        vscode_result = vscode_launcher.launch()

        if not vscode_result.success:
            print(f"✗ Failed to launch VS Code")
            return

        time.sleep(3)

        # Position VS Code on right half
        vscode_state = WindowState(
            x=screen_width // 2 + 20,
            y=100,
            width=screen_width // 2 - 20,
            height=screen_height - 200,
            monitor_index=0
        )

        wm.set_window_state(vscode_result.process_id, vscode_state)
        print(f"✓ VS Code positioned on right side")
        print()
        print("✓ Multi-window scenario complete!")
        print("  Both windows should now be side-by-side")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("macOS WINDOW POSITIONING TEST SUITE")
    print("=" * 60 + "\n")

    test_monitor_detection()

    print("\n" + "=" * 60)
    print("INTERACTIVE TESTS")
    print("=" * 60)
    print("The following tests will launch applications and move windows.")
    print("You should see windows being positioned automatically.")
    print()
    input("Press ENTER to continue...")
    print()

    # Test Chrome capture and positioning
    captured_state, pid = test_chrome_window_capture()
    if captured_state and pid:
        test_chrome_window_positioning(captured_state, pid)

    # Test VS Code positioning
    test_vscode_window_positioning()

    # Test multi-window scenario
    print("\n" + "=" * 60)
    print("FINAL TEST: Multi-Window Scenario")
    print("=" * 60)
    input("Press ENTER to run the multi-window test...")
    print()

    test_multi_window_scenario()

    print("=" * 60)
    print("ALL TESTS COMPLETE")
    print("=" * 60)
    print("\nNote: You may need to grant accessibility permissions")
    print("for the Terminal/Python to control window positions.")
    print("Go to: System Settings > Privacy & Security > Accessibility")
