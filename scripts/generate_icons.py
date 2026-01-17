#!/usr/bin/env python3
"""Generate application icons for macOS (.icns) and Windows (.ico) from SVG.

Usage:
    python scripts/generate_icons.py

Requirements:
    - PySide6 (for SVG rendering)
    - Pillow (pip install Pillow) for icon format conversion

This script generates:
    - src/context_launcher/resources/icon.icns (macOS)
    - src/context_launcher/resources/icon.ico (Windows)
    - src/context_launcher/resources/icon.png (fallback)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root / "src"))


def generate_icons():
    """Generate icon files from SVG."""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtCore import QSize, Qt

    # Initialize Qt app (required for rendering)
    app = QApplication.instance() or QApplication([])

    resources_dir = project_root / "src" / "context_launcher" / "resources"
    svg_path = resources_dir / "icon.svg"

    if not svg_path.exists():
        print(f"Error: SVG file not found at {svg_path}")
        return False

    # Load SVG
    renderer = QSvgRenderer(str(svg_path))
    if not renderer.isValid():
        print("Error: Invalid SVG file")
        return False

    # Generate PNG at various sizes
    sizes = [16, 32, 48, 64, 128, 256, 512, 1024]
    images = {}

    for size in sizes:
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()

        # Save individual PNG for reference
        png_path = resources_dir / f"icon_{size}.png"
        image.save(str(png_path))
        images[size] = image
        print(f"Generated: {png_path}")

    # Save main PNG (512x512)
    main_png = resources_dir / "icon.png"
    images[512].save(str(main_png))
    print(f"Generated: {main_png}")

    # Try to generate ICO and ICNS using Pillow
    try:
        from PIL import Image

        # Load PNG images for Pillow
        pil_images = {}
        for size in sizes:
            png_path = resources_dir / f"icon_{size}.png"
            pil_images[size] = Image.open(str(png_path))

        # Generate ICO (Windows) - include common sizes
        ico_sizes = [16, 32, 48, 64, 128, 256]
        ico_images = [pil_images[s] for s in ico_sizes if s in pil_images]

        ico_path = resources_dir / "icon.ico"
        # ICO format requires saving the largest image and including others as sizes
        pil_images[256].save(
            str(ico_path),
            format='ICO',
            sizes=[(s, s) for s in ico_sizes]
        )
        print(f"Generated: {ico_path}")

        # For macOS ICNS, we need the iconutil command or a library
        # Let's create a temporary iconset folder and use iconutil on macOS
        if sys.platform == 'darwin':
            import subprocess
            import tempfile
            import shutil

            iconset_dir = Path(tempfile.mkdtemp()) / "icon.iconset"
            iconset_dir.mkdir()

            # macOS iconset requires specific naming
            iconset_mapping = {
                16: "icon_16x16.png",
                32: "icon_16x16@2x.png",  # 32 is 16@2x
                32: "icon_32x32.png",
                64: "icon_32x32@2x.png",  # 64 is 32@2x
                128: "icon_128x128.png",
                256: "icon_128x128@2x.png",  # 256 is 128@2x
                256: "icon_256x256.png",
                512: "icon_256x256@2x.png",  # 512 is 256@2x
                512: "icon_512x512.png",
                1024: "icon_512x512@2x.png",  # 1024 is 512@2x
            }

            # Create all required sizes
            icon_files = [
                (16, "icon_16x16.png"),
                (32, "icon_16x16@2x.png"),
                (32, "icon_32x32.png"),
                (64, "icon_32x32@2x.png"),
                (128, "icon_128x128.png"),
                (256, "icon_128x128@2x.png"),
                (256, "icon_256x256.png"),
                (512, "icon_256x256@2x.png"),
                (512, "icon_512x512.png"),
                (1024, "icon_512x512@2x.png"),
            ]

            for size, filename in icon_files:
                src = resources_dir / f"icon_{size}.png"
                dst = iconset_dir / filename
                shutil.copy(str(src), str(dst))

            # Run iconutil to create ICNS
            icns_path = resources_dir / "icon.icns"
            try:
                subprocess.run(
                    ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
                    check=True,
                    capture_output=True
                )
                print(f"Generated: {icns_path}")
            except subprocess.CalledProcessError as e:
                print(f"Warning: iconutil failed: {e}")
            except FileNotFoundError:
                print("Warning: iconutil not found (macOS only)")

            # Cleanup
            shutil.rmtree(iconset_dir.parent)

        # Clean up individual size PNGs (keep only main icon.png)
        for size in sizes:
            png_path = resources_dir / f"icon_{size}.png"
            if png_path.exists() and size != 512:
                png_path.unlink()

        print("\nIcon generation complete!")
        print(f"Icons saved to: {resources_dir}")

    except ImportError:
        print("\nNote: Pillow not installed. Install with 'pip install Pillow' for ICO/ICNS generation.")
        print("SVG and PNG icons are available and will work on most systems.")

    return True


if __name__ == "__main__":
    generate_icons()
