"""Test launchers on macOS."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_launcher.launchers.base import LaunchConfig, AppType
from context_launcher.launchers.browsers.chrome import ChromeLauncher
from context_launcher.launchers.editors.vscode import VSCodeLauncher


def test_chrome_launcher():
    """Test Chrome launcher on macOS."""
    print("=" * 60)
    print("CHROME LAUNCHER TEST")
    print("=" * 60)

    try:
        # Create a simple Chrome launch config
        config = LaunchConfig(
            app_type=AppType.BROWSER,
            app_name="chrome",
            parameters={
                "tabs": [
                    {"type": "url", "url": "https://www.google.com"},
                    {"type": "url", "url": "https://www.github.com"}
                ]
            },
            platform=sys.platform
        )

        launcher = ChromeLauncher(config)

        # Test path detection
        try:
            path = launcher.get_executable_path()
            print(f"✓ Chrome path detected: {path}")
        except Exception as e:
            print(f"✗ Chrome path detection failed: {e}")
            return

        # Test command building
        args = launcher._build_command_args()
        print(f"✓ Command built: {' '.join(args[:3])}... ({len(args)} args total)")

        # Test launch
        print("  Launching Chrome (will open in new window)...")
        result = launcher.launch()

        if result.success:
            print(f"✓ Launch successful: {result.message}")
            print(f"  PID: {result.process_id}")
        else:
            print(f"✗ Launch failed: {result.error_message}")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    print()


def test_vscode_launcher():
    """Test VS Code launcher on macOS."""
    print("=" * 60)
    print("VS CODE LAUNCHER TEST")
    print("=" * 60)

    try:
        # Create a VS Code launch config (without workspace, will open last workspace)
        config = LaunchConfig(
            app_type=AppType.EDITOR,
            app_name="vscode",
            parameters={
                "new_window": True
            },
            platform=sys.platform
        )

        launcher = VSCodeLauncher(config)

        # Test path detection
        try:
            path = launcher.get_executable_path()
            print(f"✓ VS Code path detected: {path}")
        except Exception as e:
            print(f"✗ VS Code path detection failed: {e}")
            return

        # Test command building
        args = launcher._build_command_args()
        print(f"✓ Command built: {' '.join(args)}")

        # Test launch
        print("  Launching VS Code...")
        result = launcher.launch()

        if result.success:
            print(f"✓ Launch successful: {result.message}")
            print(f"  PID: {result.process_id}")
        else:
            print(f"✗ Launch failed: {result.error_message}")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    print()


def test_vscode_with_workspace():
    """Test VS Code launcher with workspace on macOS."""
    print("=" * 60)
    print("VS CODE WITH WORKSPACE TEST")
    print("=" * 60)

    # Use this project as the workspace
    workspace_path = str(Path(__file__).parent.parent)

    try:
        config = LaunchConfig(
            app_type=AppType.EDITOR,
            app_name="vscode",
            parameters={
                "folder": workspace_path,
                "new_window": True
            },
            platform=sys.platform
        )

        launcher = VSCodeLauncher(config)

        print(f"  Opening workspace: {workspace_path}")

        result = launcher.launch()

        if result.success:
            print(f"✓ Launch successful: {result.message}")
            print(f"  PID: {result.process_id}")
        else:
            print(f"✗ Launch failed: {result.error_message}")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("macOS LAUNCHER TEST SUITE")
    print("=" * 60 + "\n")

    test_chrome_launcher()
    test_vscode_launcher()
    test_vscode_with_workspace()

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nNote: Chrome and VS Code windows should have opened.")
    print("You may need to grant permissions for the launcher to control these apps.")
