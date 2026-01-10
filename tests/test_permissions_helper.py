"""Test the accessibility permissions helper."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_launcher.core.accessibility_helper_macos import AccessibilityHelper


def main():
    """Test the permissions helper."""
    print("=" * 60)
    print("ACCESSIBILITY PERMISSIONS HELPER TEST")
    print("=" * 60)
    print()

    helper = AccessibilityHelper()

    # Check current status
    print("Checking current permission status...")
    has_permissions = helper.check_permissions()

    if has_permissions:
        print("✅ SUCCESS: Accessibility permissions are already granted!")
        print()
        print("Window positioning will work without any additional setup.")
    else:
        print("❌ Accessibility permissions are NOT granted.")
        print()
        print("Window positioning requires these permissions to work.")
        print()

        # Show instructions
        print(helper.get_permission_instructions())

        # Offer to open settings
        print()
        response = input("Open System Settings now? (y/n): ").strip().lower()

        if response in ['y', 'yes']:
            print("\n📖 Opening System Settings...")
            helper.open_accessibility_settings()
            print()
            print("✓ Settings opened!")
            print()
            print("After enabling permissions:")
            print("  1. Close System Settings")
            print("  2. Restart this application")
            print("  3. Window positioning will work!")
        else:
            print("\nNo problem! You can enable permissions anytime:")
            print("  System Settings > Privacy & Security > Accessibility")

    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
