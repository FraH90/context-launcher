# macOS Accessibility Permissions Guide

## Why Permissions Are Required

macOS has a security feature called **Accessibility** that protects users from malicious applications. Any app that wants to:

- Control windows of other applications
- Simulate keyboard/mouse input
- Monitor what you're typing

Must be explicitly granted permission by the user.

## What Works WITHOUT Permissions

✅ **These features work immediately, no setup required:**

- Launching applications (Chrome, VS Code, etc.)
- Capturing/reading window positions
- Monitor detection
- Session management
- All launcher functionality
- GUI application

## What Requires Permissions

❌ **These features require accessibility permissions:**

- **Automatically positioning windows**
- **Resizing application windows**
- **Restoring saved window layouts**

## Why We Can't Bypass This

**There is NO way to bypass macOS accessibility permissions.** This is by design for security:

1. **System Protection:** Prevents malware from taking control of your apps
2. **User Privacy:** Protects against keyloggers and screen recording
3. **Transparency:** Users must explicitly approve each app

### Alternatives Don't Work

- ❌ **App-specific APIs:** Very limited, not universal
- ❌ **Different automation tools:** All require same permissions
- ❌ **Workarounds:** None exist that maintain functionality

## How to Grant Permissions (One-Time Setup)

### Method 1: Automatic (Recommended)

Run our helper tool:

```bash
uv run python tests/test_permissions_helper.py
```

It will:
1. Check if permissions are granted
2. Guide you through the process
3. Open System Settings automatically

### Method 2: Manual Setup

1. Open **System Settings**
2. Go to **Privacy & Security**
3. Click **Accessibility** in the sidebar
4. Click the lock icon 🔒 (enter your password)
5. Find **Terminal** or **Python** in the list
6. Toggle the switch to **ON** ✓
7. Restart Context Launcher

### Method 3: Direct Link

Click this link to open directly:
```
x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility
```

## Checking Permission Status

### Programmatically

```python
from context_launcher.core.accessibility_helper_macos import AccessibilityHelper

helper = AccessibilityHelper()
if helper.check_permissions():
    print("✅ Permissions granted!")
else:
    print("❌ Permissions not granted")
    helper.open_accessibility_settings()
```

### Quick Test

```bash
# Test if permissions are working
osascript -e 'tell application "System Events" to get name of first process'
```

If this returns an app name, permissions are working!

## User Experience Best Practices

### For Application Developers

**✅ DO:**
- Detect permission status on first run
- Show clear, helpful error messages
- Offer to open System Settings automatically
- Work in "read-only" mode without permissions
- Explain WHY permissions are needed

**❌ DON'T:**
- Silently fail
- Show technical error messages
- Require permissions for basic features
- Repeatedly prompt if user declines

### Example Implementation

```python
from context_launcher.core.window_manager import WindowManager
from context_launcher.core.accessibility_helper_macos import AccessibilityHelper

wm = WindowManager()
helper = AccessibilityHelper()

# Try to position window
success = wm.set_window_state(pid, state)

if not success and not helper.check_permissions():
    # Show friendly message
    print("⚠️  Window positioning requires accessibility permissions.")
    print()
    if helper.prompt_for_permissions():
        print("Please restart after enabling permissions.")
```

## What Context Launcher Does

### Smart Permission Handling

1. **First Launch:**
   - Works immediately in "launcher-only" mode
   - Window capture works (read-only)
   - Clear message about optional window positioning

2. **When User Tries Window Positioning:**
   - Detects missing permissions
   - Shows helpful instructions
   - Offers to open System Settings
   - Guides through the process

3. **After Permissions Granted:**
   - Full window positioning works
   - Settings are remembered
   - No more prompts needed

### Graceful Degradation

Without permissions, Context Launcher still provides:
- ✅ Launch applications with multiple tabs
- ✅ Organize sessions and workflows
- ✅ Capture current window positions
- ✅ Visual reminders of saved layouts
- ⚠️ Manual window positioning (user arranges)

## Technical Details

### How Permissions Work

```applescript
# This requires accessibility permissions:
tell application "System Events"
    tell process "Google Chrome"
        set position of window 1 to {100, 100}
    end tell
end tell
```

```python
# This does NOT require permissions:
from Quartz import CGWindowListCopyWindowInfo
windows = CGWindowListCopyWindowInfo(...)  # Read-only ✓
```

### Permission Scope

Granting accessibility to **Terminal** or **Python** allows:
- All Python scripts run from that terminal
- Only while that terminal is running
- Specific to that Python interpreter

### Security Implications

**What we can do with permissions:**
- Control window positions/sizes
- Simulate clicks (we don't use this)
- Read UI elements (we don't use this)

**What we actually do:**
- Only move/resize windows
- Only for apps the user launched
- Only when user explicitly requests it

## Troubleshooting

### Permissions Enabled But Not Working

1. **Restart the application completely**
2. Check you enabled the correct app (Terminal vs Python vs...)
3. Try running from a new terminal window
4. Check System Settings > Accessibility again

### Can't Find App in Accessibility List

1. Click the **+** button under the list
2. Navigate to the application
3. Add it manually
4. Toggle it ON

### "Not Allowed Assistive Access" Error

This means permissions aren't granted. Follow the setup steps above.

### Works on Windows But Not macOS

This is expected! Windows doesn't have this security restriction.
macOS is more protective of user privacy and security.

## Comparison with Other Platforms

| Platform | Permission Needed | Method |
|----------|-------------------|--------|
| **Windows** | ❌ None | Direct API access |
| **macOS** | ✅ Accessibility | User must approve |
| **Linux** | ⚠️ Varies | X11: none, Wayland: varies |

## Conclusion

**There is no way to avoid accessibility permissions on macOS** for window positioning. This is a fundamental security feature.

The best approach is:
1. ✅ Make the permission process easy and clear
2. ✅ Provide value without permissions
3. ✅ Show users why it's worth enabling
4. ✅ Handle both scenarios gracefully

Our implementation does all of this!
