"""Test Phase 2 - Multi-app launchers."""

import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from context_launcher.launchers import LaunchConfig, AppType, LauncherFactory
from context_launcher.utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def test_vscode_launcher():
    """Test VS Code launcher."""
    print("\n" + "="*60)
    print("Testing VS Code Launcher")
    print("="*60)

    # Test with a folder (current directory)
    folder_path = str(Path.cwd())

    config = LaunchConfig(
        app_type=AppType.EDITOR,
        app_name='vscode',
        parameters={
            'folder': folder_path,
            'new_window': True
        },
        platform=sys.platform
    )

    try:
        launcher = LauncherFactory.create_launcher(config)
        print(f"✓ Created launcher: {launcher.__class__.__name__}")

        exe_path = launcher.get_executable_path()
        print(f"✓ Found VS Code: {exe_path}")

        is_valid = launcher.validate_config()
        print(f"✓ Configuration valid: {is_valid}")

        print(f"\nLaunching VS Code with folder: {folder_path}")
        result = launcher.launch()

        if result.success:
            print(f"✓ SUCCESS: {result.message}")
            print(f"  Process ID: {result.process_id}")
            return True
        else:
            print(f"✗ FAILED: {result.message}")
            return False

    except Exception as e:
        print(f"✗ VS Code test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generic_launcher():
    """Test generic app launcher."""
    print("\n" + "="*60)
    print("Testing Generic App Launcher")
    print("="*60)

    # Test with Notepad (Windows) or TextEdit (Mac)
    if sys.platform == 'win32':
        exe_path = r"C:\Windows\System32\notepad.exe"
        app_name = "Notepad"
    elif sys.platform == 'darwin':
        exe_path = "/Applications/TextEdit.app/Contents/MacOS/TextEdit"
        app_name = "TextEdit"
    else:
        exe_path = "/usr/bin/gedit"
        app_name = "gedit"

    config = LaunchConfig(
        app_type=AppType.GENERIC,
        app_name='generic',
        parameters={
            'executable_path': exe_path
        },
        platform=sys.platform
    )

    try:
        launcher = LauncherFactory.create_launcher(config)
        print(f"✓ Created launcher: {launcher.__class__.__name__}")

        is_valid = launcher.validate_config()
        print(f"✓ Configuration valid: {is_valid}")

        print(f"\nLaunching {app_name}...")
        result = launcher.launch()

        if result.success:
            print(f"✓ SUCCESS: {result.message}")
            print(f"  Process ID: {result.process_id}")
            return True
        else:
            print(f"✗ FAILED: {result.message}")
            return False

    except Exception as e:
        print(f"✗ Generic app test failed: {e}")
        return False


def test_available_launchers():
    """Test that all launchers are registered."""
    print("\n" + "="*60)
    print("Available Launchers")
    print("="*60)

    launchers = LauncherFactory.get_available_launchers()

    print(f"\nRegistered launchers ({len(launchers)}):")
    for name, launcher_class in launchers.items():
        print(f"  • {name}: {launcher_class.__name__}")

    return True


def main():
    """Run Phase 2 tests."""
    print("\n" + "="*60)
    print("PHASE 2 TESTING - Multi-App Launchers")
    print("="*60)

    # Test available launchers
    test_available_launchers()

    results = []

    # Test VS Code
    if input("\n\nTest VS Code launcher? (y/n): ").lower() == 'y':
        results.append(('VS Code', test_vscode_launcher()))

    # Test generic app
    if input("\nTest Generic App launcher (Notepad/TextEdit)? (y/n): ").lower() == 'y':
        results.append(('Generic App', test_generic_launcher()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{name}: {status}")

    print("\n✓ Phase 2 testing complete!")


if __name__ == '__main__':
    main()
