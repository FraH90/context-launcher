"""Window management for saving and restoring window positions and sizes."""

import sys
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes
    import win32gui
    import win32con
    import win32process
    import win32api
elif sys.platform == 'darwin':
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
        CGDisplayBounds,
        CGMainDisplayID,
        CGGetActiveDisplayList,
    )
    from AppKit import (
        NSWorkspace,
        NSRunningApplication,
        NSApplicationActivateIgnoringOtherApps,
        NSScreen,
    )
    import subprocess


@dataclass
class WindowState:
    """Represents the state of a window."""
    x: int
    y: int
    width: int
    height: int
    monitor_index: int = 0  # Which monitor the window is on
    is_maximized: bool = False
    is_minimized: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowState':
        """Create from dictionary."""
        return cls(**data)


class WindowManager:
    """Cross-platform window management system."""

    def __init__(self):
        """Initialize window manager."""
        self.logger = logging.getLogger("context_launcher.WindowManager")
        self._platform = sys.platform

    def get_window_state(self, process_id: int, timeout: float = 5.0) -> Optional[WindowState]:
        """Get the window state for a given process.

        Args:
            process_id: Process ID of the application
            timeout: Maximum time to wait for window to appear (seconds)

        Returns:
            WindowState if found, None otherwise
        """
        if self._platform == 'win32':
            return self._get_window_state_windows(process_id, timeout)
        elif self._platform == 'darwin':
            return self._get_window_state_macos(process_id, timeout)
        else:
            return self._get_window_state_linux(process_id, timeout)

    def set_window_state(self, process_id: int, state: WindowState, timeout: float = 5.0, app_name: str = None) -> bool:
        """Set the window state for a given process.

        Args:
            process_id: Process ID of the application
            state: Desired window state
            timeout: Maximum time to wait for window to appear (seconds)
            app_name: Application name for smarter window finding (chrome, firefox, etc.)

        Returns:
            True if successful, False otherwise
        """
        if self._platform == 'win32':
            return self._set_window_state_windows(process_id, state, timeout, app_name)
        elif self._platform == 'darwin':
            return self._set_window_state_macos(process_id, state, timeout)
        else:
            return self._set_window_state_linux(process_id, state, timeout)

    def get_monitors(self) -> List[Dict[str, Any]]:
        """Get information about all connected monitors.

        Returns:
            List of monitor info dictionaries
        """
        if self._platform == 'win32':
            return self._get_monitors_windows()
        elif self._platform == 'darwin':
            return self._get_monitors_macos()
        else:
            return self._get_monitors_linux()

    # Windows implementation

    def _get_window_state_windows(self, process_id: int, timeout: float) -> Optional[WindowState]:
        """Get window state on Windows."""
        try:
            hwnd = self._find_window_by_pid_windows(process_id, timeout)
            if not hwnd:
                return None

            # Get window placement
            placement = win32gui.GetWindowPlacement(hwnd)
            show_cmd = placement[1]
            rect = win32gui.GetWindowRect(hwnd)

            is_maximized = show_cmd == win32con.SW_SHOWMAXIMIZED
            is_minimized = show_cmd == win32con.SW_SHOWMINIMIZED

            # Get monitor index
            monitor_index = self._get_monitor_index_windows(hwnd)

            return WindowState(
                x=rect[0],
                y=rect[1],
                width=rect[2] - rect[0],
                height=rect[3] - rect[1],
                monitor_index=monitor_index,
                is_maximized=is_maximized,
                is_minimized=is_minimized
            )

        except Exception as e:
            self.logger.error(f"Failed to get window state: {e}")
            return None

    def _set_window_state_windows(self, process_id: int, state: WindowState, timeout: float, app_name: str = None) -> bool:
        """Set window state on Windows."""
        try:
            self.logger.info(f"Setting window state for PID {process_id}, app_name: {app_name}")

            # For known multi-process/single-instance apps, skip PID matching and go straight to app name
            multi_process_apps = ['chrome', 'firefox', 'edge', 'spotify', 'discord', 'slack']

            if app_name and app_name.lower() in multi_process_apps:
                # Skip PID matching for these apps - use app name directly (much faster)
                self.logger.info(f"{app_name} is a multi-process app, using app name matching directly")
                hwnd = self._find_window_by_app_name(app_name, timeout=2.0)
            else:
                # For other apps, try PID-based matching first
                hwnd = self._find_window_by_pid_windows(process_id, timeout)

                # If that fails and we know the app name, try finding by window class
                if not hwnd and app_name:
                    self.logger.info(f"PID matching failed, trying to find window by app name: {app_name}")
                    hwnd = self._find_window_by_app_name(app_name, timeout=2.0)
                elif not hwnd:
                    self.logger.warning(f"PID matching failed and no app_name provided for fallback")

            if not hwnd:
                return False

            # Restore window if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)

            # Set position and size
            if state.is_maximized:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
            else:
                # First restore to normal state
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)

                # Then set position and size
                win32gui.SetWindowPos(
                    hwnd,
                    None,
                    state.x,
                    state.y,
                    state.width,
                    state.height,
                    win32con.SWP_NOZORDER
                )

            return True

        except Exception as e:
            self.logger.error(f"Failed to set window state: {e}")
            return False

    def _find_window_by_pid_windows(self, process_id: int, timeout: float) -> Optional[int]:
        """Find window handle by process ID on Windows.

        For multi-process apps like Chrome, this also checks child processes.
        """
        import psutil

        end_time = time.time() + timeout
        found_hwnd = [None]

        # Get all PIDs to check (parent + children)
        pids_to_check = set([process_id])
        try:
            parent_process = psutil.Process(process_id)
            # Add all child processes
            for child in parent_process.children(recursive=True):
                pids_to_check.add(child.pid)
            self.logger.info(f"Searching for window in {len(pids_to_check)} processes (parent + children)")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # If we can't access process info, just try the main PID
            self.logger.warning(f"Could not access process {process_id} info, using only parent PID")

        matched_windows = []  # Track matched windows for debugging

        def callback(hwnd, _):
            """Callback for EnumWindows."""
            if not win32gui.IsWindowVisible(hwnd):
                return True

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid in pids_to_check:
                # Check if it's a main window (not a child)
                if win32gui.GetParent(hwnd) == 0:
                    # Get window title to filter out empty/hidden windows
                    title = win32gui.GetWindowText(hwnd)
                    matched_windows.append((pid, title, hwnd))  # Debug logging
                    if title:  # Only accept windows with titles
                        found_hwnd[0] = hwnd
                        return False  # Stop enumeration
            return True

        # Poll for window with timeout
        attempt = 0
        while time.time() < end_time:
            attempt += 1
            # Refresh child process list each iteration (Chrome spawns processes dynamically)
            try:
                parent_process = psutil.Process(process_id)
                for child in parent_process.children(recursive=True):
                    pids_to_check.add(child.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            if attempt % 10 == 0:  # Log every 10 attempts (every 2 seconds)
                self.logger.debug(f"Attempt {attempt}: Checking {len(pids_to_check)} processes")

            win32gui.EnumWindows(callback, None)
            if found_hwnd[0]:
                self.logger.info(f"Found window handle: {found_hwnd[0]} after {attempt} attempts")
                return found_hwnd[0]
            time.sleep(0.2)  # Slightly longer wait between attempts

        self.logger.warning(f"No window found for process {process_id} after {timeout}s timeout.")
        self.logger.warning(f"Checked {len(pids_to_check)} PIDs: {pids_to_check}")
        self.logger.warning(f"Matched windows (PID, Title, HWND): {matched_windows}")
        return None

    def _find_window_by_app_name(self, app_name: str, timeout: float = 2.0) -> Optional[int]:
        """Find window by application name (for single-instance apps like Chrome).

        Args:
            app_name: Application name (chrome, firefox, edge, etc.)
            timeout: Time to wait for window

        Returns:
            Window handle if found, None otherwise
        """
        import psutil

        # Map app names to window class AND process name patterns
        app_patterns = {
            'chrome': {
                'class': 'Chrome_WidgetWin_',
                'process': 'chrome.exe'
            },
            'firefox': {
                'class': 'MozillaWindowClass',
                'process': 'firefox.exe'
            },
            'edge': {
                'class': 'Chrome_WidgetWin_',
                'process': 'msedge.exe'
            },
            'vscode': {
                'class': 'Chrome_WidgetWin_',
                'process': 'Code.exe'
            },
            'spotify': {
                'class': 'Chrome_WidgetWin_',
                'process': 'Spotify.exe'
            },
            'discord': {
                'class': 'Chrome_WidgetWin_',
                'process': 'Discord.exe'
            },
            'slack': {
                'class': 'Chrome_WidgetWin_',
                'process': 'slack.exe'
            }
        }

        app_info = app_patterns.get(app_name.lower())
        if not app_info:
            self.logger.warning(f"No window pattern known for app: {app_name}")
            return None

        class_pattern = app_info['class']
        process_name = app_info['process']

        # Wait a bit for window to appear
        time.sleep(2.0)

        # Find matching windows AND filter by process name
        all_matches = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return True

            try:
                class_name = win32gui.GetClassName(hwnd)
                if class_pattern in class_name:
                    title = win32gui.GetWindowText(hwnd)
                    if title:  # Has a title
                        # Get the process for this window
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        try:
                            proc = psutil.Process(pid)
                            proc_name = proc.name()

                            # Only include if process name matches
                            if proc_name.lower() == process_name.lower():
                                all_matches.append((hwnd, title, class_name, pid, proc_name))
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
            except:
                pass

            return True

        win32gui.EnumWindows(callback, None)

        if all_matches:
            self.logger.info(f"Found {len(all_matches)} matching windows for {app_name}")
            for hwnd, title, cls, pid, pname in all_matches:
                self.logger.info(f"  - HWND {hwnd}: {title} ({cls}) PID={pid} Process={pname}")

            # Return the first match (they all match the process name)
            chosen = all_matches[0]
            self.logger.info(f"Using: {chosen[1]} (PID={chosen[3]})")
            return chosen[0]

        self.logger.warning(f"No matching windows found for app: {app_name} (process: {process_name})")
        return None

    def _get_monitor_index_windows(self, hwnd: int) -> int:
        """Get monitor index for a window on Windows."""
        try:
            monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
            monitors = self._get_monitors_windows()

            for i, mon_info in enumerate(monitors):
                if mon_info.get('handle') == monitor:
                    return i

            return 0
        except:
            return 0

    def _get_monitors_windows(self) -> List[Dict[str, Any]]:
        """Get monitor information on Windows."""
        try:
            monitors = []
            for i, monitor in enumerate(win32api.EnumDisplayMonitors()):
                handle = monitor[0]
                info = win32api.GetMonitorInfo(handle)
                work_area = info['Work']
                monitor_area = info['Monitor']

                monitors.append({
                    'index': i,
                    'handle': handle,
                    'is_primary': info['Flags'] == 1,
                    'x': monitor_area[0],
                    'y': monitor_area[1],
                    'width': monitor_area[2] - monitor_area[0],
                    'height': monitor_area[3] - monitor_area[1],
                    'work_x': work_area[0],
                    'work_y': work_area[1],
                    'work_width': work_area[2] - work_area[0],
                    'work_height': work_area[3] - work_area[1],
                })

            return monitors
        except Exception as e:
            self.logger.error(f"Failed to get monitors: {e}")
            return []

    # macOS implementation

    def _get_monitors_macos(self) -> List[Dict[str, Any]]:
        """Get monitor information on macOS using NSScreen."""
        try:
            monitors = []
            screens = NSScreen.screens()

            for i, screen in enumerate(screens):
                frame = screen.frame()
                visible_frame = screen.visibleFrame()

                # NSScreen uses bottom-left origin, convert to top-left
                # Main screen is at index 0
                monitors.append({
                    'index': i,
                    'is_primary': i == 0,
                    'x': int(frame.origin.x),
                    'y': int(frame.origin.y),
                    'width': int(frame.size.width),
                    'height': int(frame.size.height),
                    'work_x': int(visible_frame.origin.x),
                    'work_y': int(visible_frame.origin.y),
                    'work_width': int(visible_frame.size.width),
                    'work_height': int(visible_frame.size.height),
                })

            return monitors
        except Exception as e:
            self.logger.error(f"Failed to get monitors on macOS: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_window_state_macos(self, process_id: int, timeout: float) -> Optional[WindowState]:
        """Get window state on macOS using Quartz."""
        try:
            import psutil

            # Get process name for matching
            try:
                process = psutil.Process(process_id)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.logger.error(f"Could not access process {process_id}")
                return None

            end_time = time.time() + timeout

            while time.time() < end_time:
                # Get all windows
                window_list = CGWindowListCopyWindowInfo(
                    kCGWindowListOptionOnScreenOnly,
                    kCGNullWindowID
                )

                if not window_list:
                    time.sleep(0.2)
                    continue

                # Find window by process ID
                for window in window_list:
                    window_pid = window.get('kCGWindowOwnerPID', 0)

                    if window_pid == process_id:
                        # Get window bounds
                        bounds = window.get('kCGWindowBounds', {})
                        if not bounds:
                            continue

                        x = int(bounds.get('X', 0))
                        y = int(bounds.get('Y', 0))
                        width = int(bounds.get('Width', 0))
                        height = int(bounds.get('Height', 0))

                        # Skip if window has no size (likely invisible)
                        if width == 0 or height == 0:
                            continue

                        # Get window layer (0 is normal, negative is background)
                        layer = window.get('kCGWindowLayer', 0)

                        # Check if window is on screen (basic check)
                        is_on_screen = window.get('kCGWindowIsOnscreen', False)

                        if is_on_screen and layer == 0:
                            # Determine monitor index
                            monitors = self._get_monitors_macos()
                            monitor_index = 0
                            for i, monitor in enumerate(monitors):
                                if (x >= monitor['x'] and
                                    y >= monitor['y'] and
                                    x < monitor['x'] + monitor['width'] and
                                    y < monitor['y'] + monitor['height']):
                                    monitor_index = i
                                    break

                            self.logger.info(f"Found window for PID {process_id}: {width}x{height} at ({x}, {y})")

                            return WindowState(
                                x=x,
                                y=y,
                                width=width,
                                height=height,
                                monitor_index=monitor_index,
                                is_maximized=False,  # macOS doesn't have true maximize
                                is_minimized=False
                            )

                time.sleep(0.2)

            self.logger.warning(f"No window found for process {process_id} ({process_name}) after {timeout}s timeout")
            return None

        except Exception as e:
            self.logger.error(f"Failed to get window state on macOS: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _set_window_state_macos(self, process_id: int, state: WindowState, timeout: float) -> bool:
        """Set window state on macOS using AppleScript."""
        try:
            import psutil

            # Get process info
            try:
                process = psutil.Process(process_id)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.logger.error(f"Could not access process {process_id}")
                return False

            # Map process names to AppleScript app names
            app_name_map = {
                'Google Chrome': 'Google Chrome',
                'Google Chrome Helper': 'Google Chrome',
                'Google Chrome Helper (Renderer)': 'Google Chrome',
                'Google Chrome Helper (GPU)': 'Google Chrome',
                'Firefox': 'Firefox',
                'firefox': 'Firefox',
                'Microsoft Edge': 'Microsoft Edge',
                'Code': 'Visual Studio Code',
                'Code Helper': 'Visual Studio Code',
            }

            app_name = app_name_map.get(process_name, process_name)

            # Wait a bit for window to appear
            time.sleep(0.5)

            # macOS uses top-left origin, but coordinates are relative to screen
            # AppleScript expects {x, y, x+width, y+height} format
            x1 = state.x
            y1 = state.y
            x2 = state.x + state.width
            y2 = state.y + state.height

            # Build AppleScript command with error handling
            script = f'''
            try
                tell application "System Events"
                    tell process "{app_name}"
                        set frontmost to true
                        tell window 1
                            set position to {{{x1}, {y1}}}
                            set size to {{{state.width}, {state.height}}}
                        end tell
                    end tell
                end tell
                return "success"
            on error errMsg
                return "error: " & errMsg
            end try
            '''

            self.logger.info(f"Setting window position for '{app_name}' (PID {process_id}) to {state.width}x{state.height} at ({state.x}, {state.y})")

            # Execute AppleScript
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stdout.strip()

            if result.returncode == 0 and output == "success":
                self.logger.info(f"Successfully set window position for {app_name}")
                return True
            else:
                error_msg = result.stderr if result.stderr else output
                self.logger.warning(f"AppleScript failed: {error_msg}")
                if "not allowed assistive access" in error_msg.lower() or "error" in output.lower():
                    self.logger.warning("Accessibility permissions may be required.")
                    self.logger.warning("Go to: System Settings > Privacy & Security > Accessibility")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("AppleScript command timed out")
            return False
        except Exception as e:
            self.logger.error(f"Failed to set window state on macOS: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Linux implementation (placeholder)

    def _get_window_state_linux(self, process_id: int, timeout: float) -> Optional[WindowState]:
        """Get window state on Linux."""
        self.logger.warning("Window management not yet implemented for Linux")
        return None

    def _set_window_state_linux(self, process_id: int, state: WindowState, timeout: float) -> bool:
        """Set window state on Linux."""
        self.logger.warning("Window management not yet implemented for Linux")
        return False

    def _get_monitors_linux(self) -> List[Dict[str, Any]]:
        """Get monitor information on Linux."""
        self.logger.warning("Monitor detection not yet implemented for Linux")
        return []
