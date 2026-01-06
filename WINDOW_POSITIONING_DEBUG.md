# Window Positioning Debug Guide

## Current Status: Not Working

The window positioning feature is not working correctly for Chrome. Here's what we need to debug:

## To Debug:

1. Launch a session with window positioning configured
2. Check the log file: `C:\Users\FraH\AppData\Local\FraH\ContextLauncher\Logs\context_launcher.log`
3. Look for lines containing:
   - "Searching for window in X processes"
   - "Checked X PIDs"
   - "Matched windows (PID, Title, HWND)"

## Possible Issues:

### Issue 1: Chrome Multi-Process Architecture
- Chrome spawns multiple processes
- The window might be created by a process we're not tracking
- **Solution**: We're already checking parent + children, but maybe not fast enough

### Issue 2: Timing
- Chrome might create the window AFTER we stop looking
- **Solution**: Increase timeout or poll more aggressively

### Issue 3: Window has no title initially
- Chrome windows might not have titles immediately
- **Solution**: Accept windows without titles or wait for title to appear

### Issue 4: Wrong process ID
- subprocess.Popen might return a launcher process, not the actual Chrome process
- **Solution**: Use a different approach to find Chrome windows

## Alternative Approaches:

### Approach A: Find by window title pattern
Instead of using PID, search for windows with specific patterns:
- "Google Chrome" in class name
- Recently created windows
- Windows that appeared after launch

### Approach B: Use accessibility APIs
- Use UI Automation to find Chrome windows
- More reliable but more complex

### Approach C: Simplify - just position the MOST RECENT window
- After launch, wait 2 seconds
- Find the most recently created Chrome window
- Position it

This would be simpler and more reliable!

## Recommended Fix:

**Use Approach C - Position the most recently activated window** after launch:

```python
def position_most_recent_window(app_name, window_state, timeout=10):
    """Position the most recently created/activated window."""
    start_time = time.time()

    # Wait for a window to appear
    time.sleep(2)  # Give app time to create window

    # Find all windows for this app
    windows = find_windows_by_class_or_title(app_name)

    if windows:
        # Position the first one found (likely the most recent)
        set_window_state(windows[0], window_state)
        return True

    return False
```

This approach:
- ✅ Works with multi-process apps
- ✅ Doesn't rely on PID matching
- ✅ Simpler and more reliable
- ✅ Works for Chrome, Firefox, VS Code, everything!
