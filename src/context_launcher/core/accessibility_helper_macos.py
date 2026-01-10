"""Helper for macOS accessibility permissions."""

import sys
import subprocess
from typing import Optional


class AccessibilityHelper:
    """Helper for checking and requesting accessibility permissions on macOS."""

    @staticmethod
    def check_permissions() -> bool:
        """Check if accessibility permissions are granted.

        Returns:
            True if permissions are granted, False otherwise
        """
        if sys.platform != 'darwin':
            return True  # Not macOS, no permissions needed

        # Try a simple AppleScript command that requires permissions
        script = '''
        try
            tell application "System Events"
                get name of first process whose frontmost is true
            end tell
            return "success"
        on error
            return "error"
        end try
        '''

        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout.strip() == "success"
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False

    @staticmethod
    def open_accessibility_settings():
        """Open System Settings to Accessibility preferences.

        This helps guide the user to grant permissions.
        """
        if sys.platform != 'darwin':
            return

        # Open System Settings to the Accessibility pane
        script = '''
        tell application "System Settings"
            activate
            delay 0.5
            reveal pane id "com.apple.preference.security"
        end tell
        '''

        try:
            subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                timeout=5
            )
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            # Fallback: open with direct URL
            subprocess.run(
                ['open', 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'],
                capture_output=True
            )

    @staticmethod
    def get_permission_instructions() -> str:
        """Get user-friendly instructions for granting permissions.

        Returns:
            Formatted instructions string
        """
        return """
╔════════════════════════════════════════════════════════════════╗
║          Accessibility Permissions Required                    ║
╚════════════════════════════════════════════════════════════════╝

To control window positions, Context Launcher needs accessibility
permissions. This is a one-time setup.

STEPS TO ENABLE:

1. Click "Open Settings" (or manually go to System Settings)

2. Navigate to: Privacy & Security > Accessibility

3. Click the lock icon 🔒 to make changes (enter your password)

4. Find "Terminal" or "Python" in the list

5. Toggle the switch to ON ✓

6. Restart Context Launcher

WHY THIS IS NEEDED:
macOS requires explicit permission for apps to control other
applications' windows. This is a security feature to prevent
malicious software from taking control of your system.

WHAT WE CAN DO WITHOUT PERMISSIONS:
✓ Launch applications
✓ Capture/save window positions (read-only)
✓ Manage sessions and workflows

WHAT REQUIRES PERMISSIONS:
✗ Automatically position windows
✗ Resize application windows
"""

    @staticmethod
    def prompt_for_permissions() -> bool:
        """Interactive prompt to help user grant permissions.

        Returns:
            True if user wants to proceed to settings, False otherwise
        """
        print(AccessibilityHelper.get_permission_instructions())
        print()

        response = input("Would you like to open System Settings now? (y/n): ").strip().lower()

        if response in ['y', 'yes']:
            print("\nOpening System Settings...")
            AccessibilityHelper.open_accessibility_settings()
            print("\nOnce you've enabled permissions, please restart Context Launcher.")
            return True
        else:
            print("\nYou can enable permissions later in:")
            print("System Settings > Privacy & Security > Accessibility")
            return False


def check_and_prompt_if_needed() -> bool:
    """Check permissions and prompt user if not granted.

    Returns:
        True if permissions are granted or not needed, False otherwise
    """
    if sys.platform != 'darwin':
        return True  # Not macOS

    helper = AccessibilityHelper()

    if helper.check_permissions():
        return True

    print("\n⚠️  Accessibility permissions not detected.\n")
    helper.prompt_for_permissions()
    return False


if __name__ == '__main__':
    # Test the helper
    helper = AccessibilityHelper()

    print("Checking accessibility permissions...")
    has_permissions = helper.check_permissions()

    if has_permissions:
        print("✅ Accessibility permissions are granted!")
    else:
        print("❌ Accessibility permissions are NOT granted.")
        print()
        helper.prompt_for_permissions()
