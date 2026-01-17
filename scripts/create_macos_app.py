#!/usr/bin/env python3
"""Create a minimal macOS .app bundle that launches Context Launcher."""

import os
import sys
import stat
import shutil
from pathlib import Path

APP_NAME = "Context Launcher"
BUNDLE_ID = "com.frah.contextlauncher"

def create_app_bundle():
    """Create a minimal .app bundle in the project root."""
    
    project_root = Path(__file__).parent.parent
    app_path = project_root / f"{APP_NAME}.app"
    contents_path = app_path / "Contents"
    macos_path = contents_path / "MacOS"
    resources_path = contents_path / "Resources"
    
    # Clean up existing bundle
    if app_path.exists():
        shutil.rmtree(app_path)
    
    # Create directory structure
    macos_path.mkdir(parents=True)
    resources_path.mkdir(parents=True)
    
    # Create Info.plist
    info_plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>{APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>{BUNDLE_ID}</string>
    <key>CFBundleVersion</key>
    <string>3.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>3.0</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <true/>
</dict>
</plist>
'''
    (contents_path / "Info.plist").write_text(info_plist)
    
    # Create launcher script
    launcher_script = f'''#!/bin/bash
# Context Launcher - macOS App Bundle Launcher
# This script launches the Python application with proper environment

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_CONTENTS="$(dirname "$SCRIPT_DIR")"
APP_BUNDLE="$(dirname "$APP_CONTENTS")"
PROJECT_ROOT="$(dirname "$APP_BUNDLE")"

# Change to project directory
cd "$PROJECT_ROOT"

# Try to find uv first, then fall back to python
if command -v uv &> /dev/null; then
    exec uv run python -m context_launcher "$@"
elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    exec "$PROJECT_ROOT/.venv/bin/python" -m context_launcher "$@"
else
    exec python3 -m context_launcher "$@"
fi
'''
    launcher_path = macos_path / "launcher"
    launcher_path.write_text(launcher_script)
    
    # Make launcher executable
    os.chmod(launcher_path, os.stat(launcher_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    
    # Copy icon if exists
    icon_src = project_root / "src" / "context_launcher" / "resources" / "icon.icns"
    if icon_src.exists():
        shutil.copy(icon_src, resources_path / "icon.icns")
    
    print(f"✅ Created {app_path}")
    print(f"   You can now double-click '{APP_NAME}.app' to launch the application.")
    print(f"   The menu bar will show '{APP_NAME}' instead of 'Python'.")
    print()
    print(f"   To add to Dock: drag '{APP_NAME}.app' to your Dock")
    print(f"   To add to Applications: move '{APP_NAME}.app' to /Applications")
    
    return app_path


if __name__ == "__main__":
    create_app_bundle()
