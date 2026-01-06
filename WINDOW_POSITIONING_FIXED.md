# Window Positioning - FIXED ✅

## What Was Fixed

### Critical Bug: Wrong Window Being Positioned
**Problem**: Chrome window positioning was actually positioning VS Code window instead!

**Root Cause**: Both Chrome and VS Code use the same window class `Chrome_WidgetWin_` (Chromium/Electron-based). The fallback mechanism was finding the FIRST window with this class, which happened to be VS Code.

**Solution**: Enhanced `_find_window_by_app_name()` to match BOTH:
1. Window class pattern (e.g., `Chrome_WidgetWin_`)
2. Process executable name (e.g., `chrome.exe` vs `Code.exe`)

This ensures we find the correct application's window.

### Performance Issue: 7+ Second Delay
**Problem**: Window positioning took 5-7 seconds because it tried:
1. PID matching for 5 seconds (failed for Chrome/Spotify)
2. App name matching for 2 seconds (succeeded)

**Solution**: For known multi-process apps (Chrome, Firefox, Edge, Spotify, Discord, Slack), skip PID matching entirely and go straight to app name matching.

**Result**: Positioning now takes ~2 seconds instead of 7+ seconds.

## How It Works Now

### For Simple Apps (Notepad, Calculator, etc.):
1. Launch app → Get PID
2. Find window by PID (fast, reliable)
3. Position window
4. ✅ Takes ~1 second

### For Multi-Process Apps (Chrome, Spotify, etc.):
1. Launch app → Get PID (may be launcher process)
2. **Skip PID matching** (optimization)
3. Find window by app name + process name
4. Position window
5. ✅ Takes ~2 seconds (was 7+ seconds before)

## Supported Applications

Apps with optimized positioning:
- ✅ **Chrome** (chrome.exe)
- ✅ **Firefox** (firefox.exe)
- ✅ **Edge** (msedge.exe)
- ✅ **Spotify** (Spotify.exe)
- ✅ **VS Code** (Code.exe)
- ✅ **Discord** (Discord.exe)
- ✅ **Slack** (slack.exe)

All other apps will use standard PID matching.

## How to Use

1. **Configure Window Position**:
   - Right-click any session
   - Choose "🪟 Configure Window Position"
   - Set X, Y, Width, Height, Monitor
   - Check "Position window automatically on launch"
   - Click OK

2. **Launch Session**:
   - Double-click the session OR right-click → Launch
   - Window will automatically position after ~2 seconds
   - GUI remains responsive during positioning

3. **Verify**:
   - Check that the correct app's window was positioned
   - Verify position matches your configuration
   - Check logs for any errors

## Testing Results

### Notepad Test: ✅ PASSED
- Window found by PID
- Positioned to (100, 100) with size 600x400
- Verification confirmed exact match

### Chrome Test: ✅ PASSED (After Fix)
- Window found by app name + process name
- Correctly identified chrome.exe (not Code.exe)
- Positioned to (200, 200) with size 800x600
- No wrong window positioned

## Implementation Details

**File**: `src/context_launcher/core/window_manager.py`

**Key Method**: `_find_window_by_app_name()`
```python
# Find windows matching BOTH class pattern AND process name
if class_pattern in class_name:
    title = win32gui.GetWindowText(hwnd)
    if title:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        proc_name = proc.name()

        # Only include if process name matches
        if proc_name.lower() == process_name.lower():
            all_matches.append((hwnd, title, class_name, pid, proc_name))
```

**Optimization**: `_set_window_state_windows()`
```python
multi_process_apps = ['chrome', 'firefox', 'edge', 'spotify', 'discord', 'slack']

if app_name and app_name.lower() in multi_process_apps:
    # Skip PID matching - use app name directly (much faster)
    hwnd = self._find_window_by_app_name(app_name, timeout=2.0)
else:
    # Try PID matching first for other apps
    hwnd = self._find_window_by_pid_windows(process_id, timeout)
```

## What to Test Now

1. **Chrome Positioning**:
   - Create/edit a Chrome session
   - Configure window position (e.g., X=300, Y=200, Width=1000, Height=700)
   - Launch session
   - **Expected**: Window positions in ~2 seconds, correct Chrome window

2. **Spotify Positioning**:
   - Create a Spotify session
   - Configure window position
   - Launch session
   - **Expected**: Spotify window positions correctly

3. **Already Running Instance**:
   - Open Chrome manually
   - Launch a Chrome session with window positioning
   - **Expected**: The existing Chrome window repositions

## Known Limitations

1. **macOS/Linux**: Window management not yet implemented (graceful degradation)
2. **Initial Window Position**: Some apps (like Chrome) may briefly appear in default position before repositioning
3. **Multiple Windows**: If app has multiple windows, the first matching window will be positioned

## Logs Location

Check logs for detailed information:
```
C:\Users\FraH\AppData\Local\FraH\ContextLauncher\Logs\context_launcher.log
```

Look for lines containing:
- "Setting window state for PID"
- "is a multi-process app, using app name matching directly"
- "Found window by app name"
- "Automatically positioned window"
