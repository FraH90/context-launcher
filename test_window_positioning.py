"""
Test script for window positioning functionality.
This will help us debug what's going wrong.
"""

import time
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from context_launcher.core.window_manager import WindowManager, WindowState
from context_launcher.utils.logger import get_logger

logger = get_logger("test_window_positioning")


def test_notepad_positioning():
    """Test window positioning with Notepad (simple, reliable Windows app)."""

    print("\n" + "="*80)
    print("TEST: Window Positioning with Notepad")
    print("="*80)

    # Step 1: Launch Notepad
    print("\n[STEP 1] Launching Notepad...")
    process = subprocess.Popen(['notepad.exe'])
    pid = process.pid
    print(f"OK Notepad launched with PID: {pid}")

    # Step 2: Wait for window to appear
    print("\n[STEP 2] Waiting 2 seconds for window to appear...")
    time.sleep(2)

    # Step 3: Try to find the window
    print("\n[STEP 3] Searching for Notepad window...")
    wm = WindowManager()

    # Try finding by PID
    print(f"  Searching by PID {pid} (timeout: 5s)...")
    hwnd = wm._find_window_by_pid_windows(pid, timeout=5.0)

    if hwnd:
        print(f"OK Found window by PID: HWND={hwnd}")
    else:
        print("FAIL Could not find window by PID")
        print("  Trying fallback: find by app name 'notepad'...")

        # Try by app name (using generic pattern)
        import win32gui

        def find_notepad():
            found = []
            def callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    if 'Notepad' in class_name or 'Untitled' in title or 'Notepad' in title:
                        found.append((hwnd, title, class_name))
                return True

            win32gui.EnumWindows(callback, None)
            return found

        notepad_windows = find_notepad()
        print(f"  Found {len(notepad_windows)} Notepad windows:")
        for hwnd, title, cls in notepad_windows:
            print(f"    - HWND {hwnd}: '{title}' (class: {cls})")

        if notepad_windows:
            hwnd = notepad_windows[0][0]
            print(f"OK Using first match: HWND={hwnd}")

    if not hwnd:
        print("\nFAIL TEST FAILED: Could not find Notepad window at all!")
        process.kill()
        return False

    # Step 4: Get current window state
    print("\n[STEP 4] Getting current window position...")
    current_state = wm.get_window_state(pid, timeout=1.0)

    if current_state:
        print(f"OK Current position: ({current_state.x}, {current_state.y})")
        print(f"  Current size: {current_state.width}x{current_state.height}")
        print(f"  Monitor: {current_state.monitor_index}")
        print(f"  Maximized: {current_state.is_maximized}")
    else:
        print("FAIL Could not get current window state")

    # Step 5: Set a new position
    print("\n[STEP 5] Moving window to new position...")

    target_state = WindowState(
        x=100,
        y=100,
        width=600,
        height=400,
        monitor_index=0,
        is_maximized=False,
        is_minimized=False
    )

    print(f"  Target position: ({target_state.x}, {target_state.y})")
    print(f"  Target size: {target_state.width}x{target_state.height}")

    success = wm.set_window_state(pid, target_state, timeout=2.0, app_name='notepad')

    if success:
        print("OK set_window_state returned True")
    else:
        print("FAIL set_window_state returned False")

    # Step 6: Verify the position changed
    print("\n[STEP 6] Verifying new position...")
    time.sleep(1)

    new_state = wm.get_window_state(pid, timeout=1.0)

    if new_state:
        print(f"  New position: ({new_state.x}, {new_state.y})")
        print(f"  New size: {new_state.width}x{new_state.height}")

        # Check if position matches (with some tolerance)
        x_match = abs(new_state.x - target_state.x) < 10
        y_match = abs(new_state.y - target_state.y) < 10
        width_match = abs(new_state.width - target_state.width) < 10
        height_match = abs(new_state.height - target_state.height) < 10

        if x_match and y_match and width_match and height_match:
            print("OK Position MATCHES target!")
            print("\n" + "="*80)
            print("OKOKOK TEST PASSED OKOKOK")
            print("="*80)
            success_result = True
        else:
            print("FAIL Position DOES NOT MATCH target!")
            print(f"  X: {'OK' if x_match else 'FAIL'} (expected {target_state.x}, got {new_state.x})")
            print(f"  Y: {'OK' if y_match else 'FAIL'} (expected {target_state.y}, got {new_state.y})")
            print(f"  Width: {'OK' if width_match else 'FAIL'} (expected {target_state.width}, got {new_state.width})")
            print(f"  Height: {'OK' if height_match else 'FAIL'} (expected {target_state.height}, got {new_state.height})")
            print("\n" + "="*80)
            print("FAILFAILFAIL TEST FAILED FAILFAILFAIL")
            print("="*80)
            success_result = False
    else:
        print("FAIL Could not get new window state for verification")
        success_result = False

    # Step 7: Cleanup
    print("\n[STEP 7] Cleaning up...")
    print("  Press Enter to close Notepad and exit test...")
    input()
    process.kill()
    print("OK Notepad closed")

    return success_result


def test_chrome_positioning():
    """Test with Chrome (multi-process, single-instance app)."""

    print("\n" + "="*80)
    print("TEST: Window Positioning with Chrome")
    print("="*80)

    # Step 1: Launch Chrome
    print("\n[STEP 1] Launching Chrome...")
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    if not Path(chrome_path).exists():
        print(f"FAIL Chrome not found at {chrome_path}")
        return False

    process = subprocess.Popen([chrome_path, '--new-window', 'about:blank'])
    pid = process.pid
    print(f"OK Chrome launched with PID: {pid}")

    # Step 2: Wait longer for Chrome
    print("\n[STEP 2] Waiting 3 seconds for Chrome window...")
    time.sleep(3)

    # Step 3: Find window
    print("\n[STEP 3] Searching for Chrome window...")
    wm = WindowManager()

    # Try PID matching first
    print(f"  [3a] Trying PID matching (pid={pid}, timeout=5s)...")
    hwnd = wm._find_window_by_pid_windows(pid, timeout=5.0)

    if hwnd:
        print(f"  OK Found by PID: HWND={hwnd}")
    else:
        print("  FAIL PID matching failed")
        print("  [3b] Trying app name fallback (app_name='chrome')...")
        hwnd = wm._find_window_by_app_name('chrome', timeout=2.0)

        if hwnd:
            print(f"  OK Found by app name: HWND={hwnd}")
        else:
            print("  FAIL App name matching also failed")

    if not hwnd:
        print("\nFAIL TEST FAILED: Could not find Chrome window!")
        return False

    # Step 4: Try to position it
    print("\n[STEP 4] Setting window position...")

    target_state = WindowState(
        x=200,
        y=200,
        width=800,
        height=600,
        monitor_index=0,
        is_maximized=False,
        is_minimized=False
    )

    success = wm.set_window_state(pid, target_state, timeout=2.0, app_name='chrome')

    if success:
        print("OK set_window_state returned True")
    else:
        print("FAIL set_window_state returned False")

    # Step 5: Verify
    print("\n[STEP 5] Verifying position...")
    time.sleep(1)

    # For Chrome, we need to use the hwnd we found, not PID
    import win32gui
    try:
        rect = win32gui.GetWindowRect(hwnd)
        actual_x, actual_y = rect[0], rect[1]
        actual_w, actual_h = rect[2] - rect[0], rect[3] - rect[1]

        print(f"  Position: ({actual_x}, {actual_y})")
        print(f"  Size: {actual_w}x{actual_h}")

        x_match = abs(actual_x - target_state.x) < 10
        y_match = abs(actual_y - target_state.y) < 10

        if x_match and y_match:
            print("OK Position roughly matches!")
            result = True
        else:
            print("FAIL Position does not match")
            result = False
    except Exception as e:
        print(f"FAIL Error checking position: {e}")
        result = False

    print("\n[CLEANUP] Press Enter to exit (Chrome will stay open)...")
    input()

    return result


if __name__ == '__main__':
    print("\n")
    print("+" + "="*78 + "+")
    print("|" + " "*20 + "WINDOW POSITIONING DEBUG TEST" + " "*28 + "|")
    print("+" + "="*78 + "+")

    print("\nThis test will help us understand why window positioning isn't working.")
    print("\nChoose a test:")
    print("  1. Test with Notepad (simple, single-process)")
    print("  2. Test with Chrome (complex, multi-process)")
    print("  3. Run both tests")

    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice == '1':
        test_notepad_positioning()
    elif choice == '2':
        test_chrome_positioning()
    elif choice == '3':
        print("\n" + "v"*80 + "\n")
        notepad_result = test_notepad_positioning()
        print("\n" + "v"*80 + "\n")
        chrome_result = test_chrome_positioning()

        print("\n" + "="*80)
        print("FINAL RESULTS:")
        print(f"  Notepad: {('PASS' if notepad_result else 'FAIL')}")
        print(f"  Chrome:  {('PASS' if chrome_result else 'FAIL')}")
        print("="*80)
    else:
        print("Invalid choice")
