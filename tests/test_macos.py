"""Test script for macOS compatibility."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from context_launcher.core.platform_utils import PlatformManager
from context_launcher.core.config import ConfigManager


def test_platform_detection():
    """Test platform detection."""
    print("=" * 60)
    print("PLATFORM DETECTION TEST")
    print("=" * 60)

    platform = PlatformManager.get_platform()
    print(f"Platform: {platform}")
    print(f"Is Windows: {PlatformManager.is_windows()}")
    print(f"Is macOS: {PlatformManager.is_macos()}")
    print(f"Is Linux: {PlatformManager.is_linux()}")
    print()


def test_path_detection():
    """Test application path detection."""
    print("=" * 60)
    print("APPLICATION PATH DETECTION TEST")
    print("=" * 60)

    apps = ['chrome', 'firefox', 'edge', 'vscode']

    for app in apps:
        print(f"\n{app.upper()}:")
        paths = getattr(PlatformManager, f'get_{app}_paths')()
        print(f"  Search paths:")
        for path in paths:
            exists = "✓" if path.exists() else "✗"
            print(f"    {exists} {path}")

        found = PlatformManager.find_executable(app)
        if found:
            print(f"  ✓ Found: {found}")
        else:
            print(f"  ✗ Not found")
    print()


def test_config_directories():
    """Test configuration directory detection."""
    print("=" * 60)
    print("CONFIGURATION DIRECTORY TEST")
    print("=" * 60)

    config_dir = PlatformManager.get_default_config_dir()
    data_dir = PlatformManager.get_default_data_dir()
    log_dir = PlatformManager.get_default_log_dir()

    print(f"Config dir: {config_dir}")
    print(f"  Exists: {config_dir.exists()}")

    print(f"Data dir: {data_dir}")
    print(f"  Exists: {data_dir.exists()}")

    print(f"Log dir: {log_dir}")
    print(f"  Exists: {log_dir.exists()}")
    print()


def test_config_manager():
    """Test config manager initialization."""
    print("=" * 60)
    print("CONFIG MANAGER TEST")
    print("=" * 60)

    try:
        config_manager = ConfigManager()
        print(f"✓ ConfigManager initialized")
        print(f"  Data directory: {config_manager.data_dir}")
        print(f"  Tabs file: {config_manager.tabs_path}")
        print(f"  Sessions directory: {config_manager.sessions_dir}")

        # Check if default data was created
        if config_manager.tabs_path.exists():
            print(f"  ✓ Tabs file exists")
        else:
            print(f"  ✗ Tabs file not created")

        if config_manager.sessions_dir.exists():
            session_files = list(config_manager.sessions_dir.glob("*.json"))
            print(f"  ✓ Sessions directory exists ({len(session_files)} sessions)")
        else:
            print(f"  ✗ Sessions directory not created")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("macOS COMPATIBILITY TEST SUITE")
    print("=" * 60 + "\n")

    test_platform_detection()
    test_path_detection()
    test_config_directories()
    test_config_manager()

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
