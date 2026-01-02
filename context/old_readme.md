# Chrome Session Launcher

A PyQt6-based desktop application that allows you to organize and launch Chrome browser sessions with predefined sets of tabs. Perfect for managing different browsing contexts like work, entertainment, or social media.

## Features

- **Session Management**: Create, edit, and delete custom browser sessions
- **Multiple Tab Types**: Support for regular URLs and YouTube channels
- **Custom Icons**: Personalize each session with emoji icons
- **One-Click Launch**: Launch all tabs from a session with a single click
- **Profile Support**: Use specific Chrome profiles for different sessions
- **Persistent Storage**: Sessions are saved locally in JSON format

## Screenshot

![Chrome Session Launcher GUI](doc/gui_interface.png)

## Requirements

- Python 3.x
- PyQt6
- Selenium
- ChromeDriver

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd context_launcher
```

2. Install required dependencies:
```bash
pip install PyQt6 selenium
```

3. Download [ChromeDriver](https://chromedriver.chromium.org/) and note its path

## Usage

1. Run the application using the batch file:
```bash
launch.bat
```

   Or run directly:
```bash
python src/context_launcher.py
```

2. **Add a Session**: Click "Add" to create a new session with tabs
3. **Edit a Session**: Select a session and click "Edit" to modify it
4. **Launch a Session**: Double-click or select and click "Launch" to open all tabs
5. **Settings**: Configure Chrome profile and ChromeDriver paths

## Configuration

The application stores configuration in `src/config.json` including:
- Chrome profile path
- ChromeDriver path
- All saved sessions

## Example Sessions

- **Entertainment**: Netflix, Prime Video, and other streaming sites
- **YouTube Channels**: Quick access to specific YouTube channels
- **Work**: Project management, email, and collaboration tools

## License

MIT License
