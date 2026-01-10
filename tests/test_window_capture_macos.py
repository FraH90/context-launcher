"""Simple test for window capture on macOS."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_launcher.core.window_manager import WindowManager, WindowState
from context_launcher.launchers.base import LaunchConfig, AppType
from context_launcher.launchers.browsers.chrome import ChromeLauncher


def main():
    """Test window capture with Chrome."""
    print("=" * 60)
    print("WINDOW CAPTURE TEST (macOS)")
    print("=" * 60)
    print()

    # Test monitor detection first
    print("1. Testing monitor detection...")
    wm = WindowManager()
    monitors = wm.get_monitors()
    print(f"   ✓ Found {len(monitors)} monitor(s)")
    print()

    # Launch Chrome
    print("2. Launching Chrome...")
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
        print(f"   ✗ Failed: {result.message}")
        return

    print(f"   ✓ Chrome launched (PID: {result.process_id})")
    print()

    # Wait for window to appear
    print("3. Waiting for window to appear (5 seconds)...")
    time.sleep(5)
    print()

    # Capture window state
    print("4. Capturing window state...")
    window_state = wm.get_window_state(result.process_id, timeout=10.0)

    if window_state:
        print(f"   ✓ Window captured:")
        print(f"     Position: ({window_state.x}, {window_state.y})")
        print(f"     Size: {window_state.width}x{window_state.height}")
        print(f"     Monitor: {window_state.monitor_index}")
        print()

        # Try to reposition the window
        print("5. Repositioning window to (200, 200) 900x700...")
        new_state = WindowState(
            x=200,
            y=200,
            width=900,
            height=700,
            monitor_index=0
        )

        time.sleep(2)
        success = wm.set_window_state(result.process_id, new_state, timeout=5.0)

        if success:
            print("   ✓ Window repositioned successfully!")
            print("     (You should see the window move)")
        else:
            print("   ✗ Failed to reposition window")
            print("     This may require accessibility permissions.")
            print("     Go to: System Settings > Privacy & Security > Accessibility")

    else:
        print("   ✗ Failed to capture window state")
        print("     The window may not have appeared yet")

    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
