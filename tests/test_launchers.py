"""Simple test script to verify browser launchers work."""

import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from context_launcher.launchers import LaunchConfig, AppType, LauncherFactory
from context_launcher.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def test_chrome_launcher():
    """Test Chrome launcher with some example tabs."""
    print("\n" + "="*60)
    print("Testing Chrome Launcher")
    print("="*60)

    # Create launch configuration
    config = LaunchConfig(
        app_type=AppType.BROWSER,
        app_name='chrome',
        parameters={
            'tabs': [
                {'type': 'url', 'url': 'https://www.google.com'},
                {'type': 'url', 'url': 'https://www.github.com'},
                {'type': 'url', 'url': 'https://www.stackoverflow.com'},
            ],
            'profile': '',  # Use default profile
            'use_selenium': False
        },
        platform=sys.platform
    )

    # Create launcher using factory
    try:
        launcher = LauncherFactory.create_launcher(config)
        print(f"✓ Created launcher: {launcher.__class__.__name__}")

        # Get executable path
        exe_path = launcher.get_executable_path()
        print(f"✓ Found Chrome executable: {exe_path}")

        # Validate config
        is_valid = launcher.validate_config()
        print(f"✓ Configuration valid: {is_valid}")

        # Launch browser
        print(f"\nLaunching Chrome with {len(config.parameters['tabs'])} tabs...")
        result = launcher.launch()

        if result.success:
            print(f"✓ SUCCESS: {result.message}")
            print(f"  Process ID: {result.process_id}")
        else:
            print(f"✗ FAILED: {result.message}")
            if result.error:
                print(f"  Error: {result.error}")

        return result.success

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_firefox_launcher():
    """Test Firefox launcher if available."""
    print("\n" + "="*60)
    print("Testing Firefox Launcher")
    print("="*60)

    config = LaunchConfig(
        app_type=AppType.BROWSER,
        app_name='firefox',
        parameters={
            'tabs': [
                {'type': 'url', 'url': 'https://www.mozilla.org'},
                {'type': 'url', 'url': 'https://www.github.com'},
            ],
            'profile': '',
            'use_selenium': False
        },
        platform=sys.platform
    )

    try:
        launcher = LauncherFactory.create_launcher(config)
        print(f"✓ Created launcher: {launcher.__class__.__name__}")

        exe_path = launcher.get_executable_path()
        print(f"✓ Found Firefox executable: {exe_path}")

        is_valid = launcher.validate_config()
        print(f"✓ Configuration valid: {is_valid}")

        print(f"\nLaunching Firefox with {len(config.parameters['tabs'])} tabs...")
        result = launcher.launch()

        if result.success:
            print(f"✓ SUCCESS: {result.message}")
            print(f"  Process ID: {result.process_id}")
        else:
            print(f"✗ FAILED: {result.message}")

        return result.success

    except Exception as e:
        print(f"✗ Firefox not found or error: {e}")
        return False


def test_edge_launcher():
    """Test Edge launcher if available (Windows/macOS)."""
    print("\n" + "="*60)
    print("Testing Edge Launcher")
    print("="*60)

    config = LaunchConfig(
        app_type=AppType.BROWSER,
        app_name='edge',
        parameters={
            'tabs': [
                {'type': 'url', 'url': 'https://www.bing.com'},
                {'type': 'url', 'url': 'https://www.github.com'},
            ],
            'profile': '',
            'use_selenium': False
        },
        platform=sys.platform
    )

    try:
        launcher = LauncherFactory.create_launcher(config)
        print(f"✓ Created launcher: {launcher.__class__.__name__}")

        exe_path = launcher.get_executable_path()
        print(f"✓ Found Edge executable: {exe_path}")

        is_valid = launcher.validate_config()
        print(f"✓ Configuration valid: {is_valid}")

        print(f"\nLaunching Edge with {len(config.parameters['tabs'])} tabs...")
        result = launcher.launch()

        if result.success:
            print(f"✓ SUCCESS: {result.message}")
            print(f"  Process ID: {result.process_id}")
        else:
            print(f"✗ FAILED: {result.message}")

        return result.success

    except Exception as e:
        print(f"✗ Edge not found or error: {e}")
        return False


def test_platform_detection():
    """Test platform detection utilities."""
    print("\n" + "="*60)
    print("Testing Platform Detection")
    print("="*60)

    from context_launcher.core.platform_utils import PlatformManager

    print(f"Platform: {PlatformManager.get_platform()}")
    print(f"Is Windows: {PlatformManager.is_windows()}")
    print(f"Is macOS: {PlatformManager.is_macos()}")
    print(f"Is Linux: {PlatformManager.is_linux()}")

    print("\nSearching for executables:")

    chrome_path = PlatformManager.find_executable('chrome')
    print(f"  Chrome: {chrome_path if chrome_path else 'Not found'}")

    firefox_path = PlatformManager.find_executable('firefox')
    print(f"  Firefox: {firefox_path if firefox_path else 'Not found'}")

    edge_path = PlatformManager.find_executable('edge')
    print(f"  Edge: {edge_path if edge_path else 'Not found'}")


def test_config_manager():
    """Test configuration manager."""
    print("\n" + "="*60)
    print("Testing Configuration Manager")
    print("="*60)

    from context_launcher.core.config import ConfigManager

    config_manager = ConfigManager()

    print(f"Config directory: {config_manager.config_dir}")
    print(f"Data directory: {config_manager.data_dir}")
    print(f"Sessions directory: {config_manager.sessions_dir}")

    # Load settings
    settings = config_manager.load_app_settings()
    print(f"\n✓ Loaded app settings (version: {settings.get('version')})")
    print(f"  Applications configured: {list(settings.get('applications', {}).keys())}")

    prefs = config_manager.load_user_preferences()
    print(f"✓ Loaded user preferences (theme: {prefs.get('ui', {}).get('theme')})")

    categories = config_manager.load_categories()
    print(f"✓ Loaded categories: {len(categories.get('categories', []))} category(ies)")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CONTEXT LAUNCHER - PHASE 1 TESTING")
    print("="*60)

    # Test platform detection
    test_platform_detection()

    # Test config manager
    test_config_manager()

    # Test browser launchers
    results = []

    # Always test Chrome (most common)
    results.append(('Chrome', test_chrome_launcher()))

    # Test Firefox if user wants
    if input("\n\nTest Firefox launcher? (y/n): ").lower() == 'y':
        results.append(('Firefox', test_firefox_launcher()))

    # Test Edge if user wants
    if input("\nTest Edge launcher? (y/n): ").lower() == 'y':
        results.append(('Edge', test_edge_launcher()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{name}: {status}")

    print("\n✓ Phase 1 testing complete!")
    print("\nNote: Browser windows were actually launched. Check if they opened correctly.")


if __name__ == '__main__':
    main()
