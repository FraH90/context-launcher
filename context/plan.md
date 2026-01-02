# Context Launcher - Comprehensive Implementation Plan

## Executive Summary

Transform the Chrome Session Launcher into a professional, cross-platform **Workflow Launcher** that helps manage ADHD/executive dysfunction by centralizing all workflow management in one place. Support launching browsers (Chrome, Firefox, Edge), IDEs (VS Code, PyCharm), generic applications, and composite workflows that launch multiple apps together.

---

## Project Vision

**From:** Single-purpose Chrome tab launcher (461 lines)
**To:** Professional workflow management system supporting:
- Multiple browsers with session management
- IDE/editor workspace launching
- Generic application launching
- Composite workflows (multi-app launches)
- Category-based organization
- Automatic state capture from running apps
- Full cross-platform support (Windows + macOS)

---

## Architecture Overview

### Core Design Principles

1. **Plugin Architecture**: Each app type (Chrome, Firefox, VS Code) has its own launcher class
2. **Factory Pattern**: Dynamic launcher creation based on session configuration
3. **Separation of Concerns**: Core logic, UI, launchers, and state capture are independent modules
4. **JSON-based Storage**: Human-readable configs, one file per session for easy management
5. **Cross-platform First**: Platform detection and path resolution built-in from the start

### Project Structure

```
context-launcher/
├── src/context_launcher/           # Main package
│   ├── core/                       # Core data models & config
│   │   ├── config.py              # Configuration management
│   │   ├── session.py             # Session data models
│   │   ├── category.py            # Category/folder models
│   │   ├── workflow.py            # Composite workflow models
│   │   └── platform_utils.py      # Platform detection
│   │
│   ├── launchers/                  # Launcher plugins
│   │   ├── base.py                # Abstract base launcher
│   │   ├── factory.py             # Launcher factory
│   │   ├── browsers/              # Browser launchers
│   │   │   ├── base_browser.py
│   │   │   ├── chrome.py
│   │   │   ├── firefox.py
│   │   │   └── edge.py
│   │   ├── editors/               # IDE launchers
│   │   │   ├── vscode.py
│   │   │   └── pycharm.py
│   │   └── apps/                  # Generic app launchers
│   │       ├── generic.py
│   │       ├── slack.py
│   │       └── spotify.py
│   │
│   ├── capture/                    # State capture system
│   │   ├── base_capture.py
│   │   ├── browser_capture.py
│   │   └── vscode_capture.py
│   │
│   ├── ui/                         # PyQt6 UI components
│   │   ├── main_window.py
│   │   ├── session_dialog.py
│   │   ├── workflow_dialog.py
│   │   ├── capture_dialog.py
│   │   ├── settings_dialog.py
│   │   └── widgets/
│   │       ├── session_tree.py    # Tree view with categories
│   │       └── app_selector.py
│   │
│   └── utils/                      # Utilities
│       ├── logger.py
│       ├── threading.py
│       └── validators.py
│
├── config/                         # Application settings
│   ├── app_settings.json          # App paths per platform
│   └── user_preferences.json      # UI preferences
│
├── data/                           # User data
│   ├── sessions/                  # One JSON per session
│   ├── workflows/                 # Composite workflows
│   └── categories.json            # Category hierarchy
│
├── scripts/
│   └── migrate_v2_config.py       # Migration from v2
│
└── tests/                          # Test suite
```

---

## Data Models

### Session Schema (v3.0)

```json
{
  "version": "3.0",
  "id": "uuid",
  "name": "Morning Work Setup",
  "icon": "☀️",
  "description": "Email, calendar, tasks",
  "type": "single_app",
  "created_at": "2026-01-02T10:00:00Z",
  "updated_at": "2026-01-02T10:00:00Z",
  "metadata": {
    "category_id": "work",
    "tags": ["morning", "productivity"],
    "favorite": true,
    "launch_count": 42,
    "last_launched": "2026-01-02T09:00:00Z"
  },
  "launch_config": {
    "app_type": "browser",
    "app_name": "chrome",
    "parameters": {
      "profile": "Work Profile",
      "use_selenium": false,
      "tabs": [
        {"type": "url", "url": "https://mail.google.com", "pinned": true},
        {"type": "url", "url": "https://calendar.google.com"}
      ]
    }
  }
}
```

### Composite Workflow Schema

```json
{
  "version": "3.0",
  "id": "workflow-uuid",
  "name": "Deep Work Session",
  "icon": "🎯",
  "type": "composite_workflow",
  "launch_sequence": [
    {
      "order": 1,
      "delay_ms": 0,
      "session_ref": "chrome-docs-session-id"
    },
    {
      "order": 2,
      "delay_ms": 2000,
      "inline_config": {
        "app_type": "editor",
        "app_name": "vscode",
        "parameters": {
          "workspace": "/path/to/workspace.code-workspace"
        }
      }
    }
  ]
}
```

### Category Schema

```json
{
  "version": "3.0",
  "categories": [
    {
      "id": "work",
      "name": "Work",
      "icon": "💼",
      "parent_id": null,
      "expanded": true,
      "order": 1
    },
    {
      "id": "work-dev",
      "name": "Development",
      "icon": "👨‍💻",
      "parent_id": "work",
      "expanded": true,
      "order": 1
    }
  ]
}
```

---

## Implementation Phases

### Phase 1: Foundation & Multi-Browser Support

**Goal**: Establish new architecture, support multiple browsers

**Tasks**:
1. Create new project structure with all directories
2. Implement base classes:
   - `BaseLauncher` (abstract launcher interface)
   - `BrowserLauncher` (browser-specific base)
   - `LaunchConfig`, `LaunchResult` data classes
3. Implement launcher factory with plugin registration
4. Implement concrete browser launchers:
   - `ChromeLauncher` (subprocess-based, not Selenium)
   - `FirefoxLauncher`
   - `EdgeLauncher`
5. Create new data models with Pydantic validation
6. Implement `ConfigManager` with platform-aware path resolution
7. Create migration script from v2 config to v3
8. Build basic UI with session list (no categories yet)
9. Setup logging framework
10. Write unit tests for launchers

**Deliverables**:
- Complete folder structure
- Working Chrome/Firefox/Edge launchers via subprocess
- Migrated sessions from v2
- Basic UI for launching sessions
- Test coverage for core components

**Success Criteria**:
- Launch Chrome/Firefox/Edge with multiple tabs
- Config properly migrated without data loss
- No Selenium dependency (optional feature)

---

### Phase 2: Multi-App Launcher System

**Goal**: Support IDEs, generic applications, communication apps

**Tasks**:
1. Implement `VSCodeLauncher`:
   - Workspace/folder opening
   - CLI command detection (`code` command)
   - Platform-specific path resolution
2. Implement `PyCharmLauncher`:
   - Project opening
   - Recent projects detection
3. Implement `GenericAppLauncher`:
   - Accept any executable path
   - Command-line arguments support
   - Working directory setting
4. Implement communication app launchers:
   - `SlackLauncher` (basic app opening)
   - `DiscordLauncher`
5. Enhance `PlatformManager`:
   - Auto-detect VS Code installation
   - Auto-detect PyCharm installation
   - Handle macOS .app bundles
6. Update session dialog:
   - App type selector dropdown
   - Dynamic parameter fields based on app type
   - App-specific configuration UI
7. Add app icon resources
8. Write tests for all new launchers

**Deliverables**:
- Working VS Code launcher with workspace support
- Working PyCharm launcher
- Generic app launcher for any executable
- Enhanced session editor with app selection
- Cross-platform path detection

**Success Criteria**:
- Open VS Code with specific workspace on Windows/macOS
- Launch PyCharm with project
- Launch any generic app (Slack, Spotify, etc.)

---

### Phase 3: Composite Workflows

**Goal**: Launch multiple apps in sequence

**Tasks**:
1. Create `Workflow` data model
2. Implement `WorkflowExecutor`:
   - Sequential launch with delays
   - Error handling (continue or stop on failure)
   - Progress reporting
3. Create `WorkflowDialog`:
   - Add multiple sessions to workflow
   - Configure launch order and delays
   - Preview workflow steps
4. Update UI:
   - Distinguish workflows from sessions visually
   - Show workflow execution progress
   - Handle long-running launches
5. Implement workflow persistence (separate JSON files)
6. Add workflow validation (circular dependency check)

**Deliverables**:
- Workflow data model and executor
- Workflow editor UI
- Ability to launch 3+ apps in sequence
- Progress feedback during execution

**Success Criteria**:
- Create workflow that launches Chrome + VS Code + Slack
- Handle app launch failures gracefully
- Save and reload workflows

---

### Phase 4: State Capture

**Goal**: Capture running app states and create sessions automatically

**Tasks**:
1. Implement browser state capture:
   - **Chrome**: Use Chrome DevTools Protocol (requires debug port)
   - **Firefox**: Platform-specific (AppleScript on macOS, automation on Windows)
   - Detect open tabs, URLs, window positions
2. Implement VS Code state capture:
   - Detect running VS Code processes
   - Parse command-line arguments for workspace paths
   - Read VS Code state files for open files
3. Implement generic process capture:
   - Use `psutil` to enumerate processes
   - Extract executable paths and arguments
4. Create `CaptureDialog`:
   - Show detected running apps
   - Select which apps to capture
   - Preview captured state
   - Create session from captured state
5. Add "Capture Current State" button to main window
6. Handle edge cases:
   - Multiple browser windows
   - Private/incognito windows (skip or include?)
   - Apps without detectable state

**Technical Approach**:

**Chrome Capture** (Chrome DevTools Protocol):
```python
# Start Chrome with: chrome.exe --remote-debugging-port=9222
# Query: http://localhost:9222/json
import requests

def capture_chrome_tabs():
    response = requests.get('http://localhost:9222/json')
    tabs = response.json()
    return [{'url': tab['url'], 'title': tab['title']} for tab in tabs]
```

**VS Code Capture**:
```python
# Find VS Code processes and extract workspace from cmdline
import psutil

for proc in psutil.process_iter(['name', 'cmdline']):
    if 'code' in proc.info['name'].lower():
        for arg in proc.info['cmdline']:
            if arg.endswith('.code-workspace'):
                workspace = arg
```

**Deliverables**:
- Browser tab capture for Chrome (DevTools Protocol)
- VS Code workspace detection
- Process-based capture for generic apps
- Capture dialog UI
- Create sessions from captured state

**Success Criteria**:
- Detect 5 open Chrome tabs and create session
- Detect VS Code workspace and create session
- Handle multiple browser windows
- Manual and automatic capture both work

---

### Phase 5: Category Organization

**Goal**: Hierarchical organization with folders

**Tasks**:
1. Implement `Category` data model with parent-child relationships
2. Create `CategoryDialog` for CRUD operations
3. Replace `QListWidget` with `QTreeWidget`:
   - Show categories as folders
   - Show sessions as children
   - Support expand/collapse
   - Persist expand/collapse state
4. Implement drag-and-drop:
   - Move sessions between categories
   - Reorder sessions within category
   - Move categories (change parent)
5. Add category context menu:
   - New session in category
   - Edit category
   - Delete category (with confirmation)
6. Visual enhancements:
   - Color coding by category
   - Indent levels for hierarchy
   - Icons for folders vs sessions
7. Add "Uncategorized" default category
8. Implement category filtering/search

**Deliverables**:
- Tree view with collapsible categories
- Drag-and-drop organization
- Category editor dialog
- Persistent category structure

**Success Criteria**:
- Create nested categories (Work > Development > Python)
- Move sessions between categories via drag-and-drop
- Expand/collapse state saved between sessions
- Search filters by session name across all categories

---

### Phase 6: Advanced Features & Polish

**Goal**: Professional polish and power-user features

**Tasks**:
1. **Window Management**:
   - Save/restore window positions
   - Save/restore window sizes
   - Multi-monitor support
   - Platform-specific window APIs (win32gui, AppKit)

2. **Launch Statistics**:
   - Track launch count per session
   - Track last launched timestamp
   - Show most-used sessions at top
   - Usage analytics dashboard

3. **Favorites System**:
   - Mark sessions as favorites
   - Favorites section at top of UI
   - Quick access shortcuts

4. **Search & Filter**:
   - Fuzzy search by name
   - Filter by tags
   - Filter by app type
   - Recent launches section

5. **Keyboard Shortcuts**:
   - Ctrl+N: New session
   - Ctrl+F: Focus search
   - Enter: Launch selected
   - Ctrl+E: Edit selected
   - Ctrl+,: Settings

6. **Import/Export**:
   - Export sessions to ZIP
   - Import sessions from ZIP
   - Share workflows with others
   - Backup/restore functionality

7. **UI Polish**:
   - Dark theme support
   - Custom color schemes
   - Session preview on hover
   - Launch animations/feedback
   - System tray icon with quick launch menu

8. **Error Recovery**:
   - Retry failed launches
   - Fallback executable paths
   - Helpful error messages
   - Diagnostic logging

**Deliverables**:
- Window positioning system
- Launch statistics tracking
- Favorites functionality
- Comprehensive search/filter
- Keyboard shortcut system
- Import/export dialogs
- Dark theme
- System tray integration

**Success Criteria**:
- Sessions restore window positions
- Keyboard shortcuts work as expected
- Export/import preserves all data
- Dark theme applies consistently

---

## Migration Strategy

### From v2 to v3

**Migration Script**: `scripts/migrate_v2_config.py`

**Steps**:
1. Detect v2 config at `src/config.json`
2. Backup v2 config to `src/config.json.v2.backup`
3. Parse v2 sessions array
4. Create v3 session files in `data/sessions/`
5. Convert Chrome-specific settings to `config/app_settings.json`
6. Create default "Uncategorized" category
7. Assign all migrated sessions to "Uncategorized"
8. Preserve YouTube channel tabs with Selenium flag enabled
9. Generate UUIDs for session IDs
10. Log migration results

**Backward Compatibility**:
- Keep v2 backup permanently
- Offer "Export as v2 format" option
- Document breaking changes

---

## Technology Stack

### Core Dependencies

```
PyQt6>=6.6.0                    # GUI framework (already in use)
pydantic>=2.5.0                 # Data validation & models
psutil>=5.9.0                   # Process management
platformdirs>=4.1.0             # Cross-platform config dirs
jsonschema>=4.20.0              # JSON schema validation
```

### Optional Dependencies

```
selenium>=4.16.0                # Optional browser automation
pywin32>=306                    # Windows window management
pyobjc>=10.0                    # macOS window management (macOS only)
```

### Development Dependencies

```
pytest>=7.4.3
pytest-qt>=4.2.0
black>=23.12.0
mypy>=1.7.0
```

### Launcher Approaches

**Browsers**: Use `subprocess.Popen` with command-line arguments (simple, fast, no dependencies)
- Selenium is **optional** for advanced features (YouTube channel switching)
- Make Selenium opt-in per session

**IDEs**: Use CLI commands or direct executable launching
- VS Code: `code <workspace>` command
- PyCharm: Direct executable with project path argument

**Generic Apps**: Direct executable with `subprocess.Popen`

---

## Critical Implementation Details

### Cross-Platform Path Resolution

```python
# src/context_launcher/core/platform_utils.py
import sys
from pathlib import Path

class PlatformManager:
    @staticmethod
    def get_chrome_paths():
        if sys.platform == 'win32':
            return [
                Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
                Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
            ]
        elif sys.platform == 'darwin':
            return [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")]
        return []

    @staticmethod
    def find_executable(app_name: str):
        search_func = getattr(PlatformManager, f'get_{app_name}_paths', None)
        if search_func:
            for path in search_func():
                if path.exists():
                    return path
        return None
```

### Browser Launching (Subprocess Approach)

```python
# src/context_launcher/launchers/browsers/chrome.py
import subprocess

class ChromeLauncher(BrowserLauncher):
    async def _launch_native(self):
        args = [self.get_executable_path()]

        if self.profile:
            args.append(f"--profile-directory={self.profile}")

        args.append("--new-window")
        args.extend([tab['url'] for tab in self.tabs])

        process = subprocess.Popen(args)
        return LaunchResult(success=True, process_id=process.pid)
```

### VS Code Launching

```python
# src/context_launcher/launchers/editors/vscode.py
class VSCodeLauncher(BaseLauncher):
    async def launch(self):
        workspace = self.config.parameters.get('workspace')

        # Try CLI command first
        args = ['code', workspace]

        try:
            process = subprocess.Popen(args)
            return LaunchResult(success=True, process_id=process.pid)
        except FileNotFoundError:
            # Fallback to direct executable
            exe_path = self.get_executable_path()
            process = subprocess.Popen([exe_path, workspace])
            return LaunchResult(success=True, process_id=process.pid)
```

---

## UI/UX for ADHD Friendliness

### Design Principles

1. **Visual Clarity**: Large icons, ample whitespace, high contrast
2. **Minimal Friction**: Double-click to launch, no confirmation dialogs
3. **Contextual Organization**: Categories as mental buckets
4. **Clear Feedback**: Progress indicators, status messages
5. **Quick Access**: Favorites, recent, search prominently placed

### Main Window Layout

```
┌─────────────────────────────────────────────┐
│  Context Launcher              [⚙️] [🔍]    │
├─────────────────────────────────────────────┤
│  Search: [_________________]  [+ New] [📸]  │
│                                             │
│  📌 Favorites                               │
│    ☀️ Morning Work Setup           [▶️]     │
│    🎯 Deep Work Session            [▶️]     │
│                                             │
│  ▼ 💼 Work                                  │
│    ▼ 👨‍💻 Development                        │
│      🌐 Chrome - Docs              [▶️]     │
│      💻 VS Code - MyApp            [▶️]     │
│      🎯 Deep Work Workflow         [▶️]     │
│    ▶ 📊 Analytics                           │
│  ▼ 🏠 Personal                              │
│    🎬 Entertainment                [▶️]     │
│  ▶ 📚 Learning                              │
└─────────────────────────────────────────────┘

[📸] = Capture Current State button
```

---

## Testing Strategy

### Unit Tests
- Test each launcher in isolation
- Mock subprocess calls
- Test data model validation
- Test platform utilities

### Integration Tests
- Test workflow execution end-to-end
- Test state capture
- Test migration scripts

### Manual Testing Checklist
- [ ] Test on Windows 10/11
- [ ] Test on macOS (if available)
- [ ] Test Chrome, Firefox, Edge launching
- [ ] Test VS Code workspace opening
- [ ] Test generic app launching
- [ ] Test workflow execution (3+ apps)
- [ ] Test state capture
- [ ] Test migration from v2
- [ ] Test with missing executables (error handling)
- [ ] Test drag-and-drop organization

---

## Key Files to Create/Modify

### Phase 1 - Foundation
- **New**: `src/context_launcher/launchers/base.py` - Abstract base launcher
- **New**: `src/context_launcher/launchers/factory.py` - Factory pattern
- **New**: `src/context_launcher/launchers/browsers/chrome.py` - Chrome launcher (refactored from v2)
- **New**: `src/context_launcher/core/config.py` - Config manager
- **New**: `src/context_launcher/core/session.py` - Session models
- **New**: `scripts/migrate_v2_config.py` - Migration script
- **Modify**: `src/context_launcher/ui/main_window.py` - Refactor from v2's MainWindow

### Phase 2 - Multi-App
- **New**: `src/context_launcher/launchers/editors/vscode.py` - VS Code launcher
- **New**: `src/context_launcher/launchers/apps/generic.py` - Generic app launcher
- **New**: `src/context_launcher/core/platform_utils.py` - Platform utilities

### Phase 3 - Workflows
- **New**: `src/context_launcher/core/workflow.py` - Workflow model
- **New**: `src/context_launcher/ui/workflow_dialog.py` - Workflow editor

### Phase 4 - State Capture
- **New**: `src/context_launcher/capture/browser_capture.py` - Browser state capture
- **New**: `src/context_launcher/capture/vscode_capture.py` - VS Code capture
- **New**: `src/context_launcher/ui/capture_dialog.py` - Capture UI

### Phase 5 - Categories
- **New**: `src/context_launcher/core/category.py` - Category model
- **New**: `src/context_launcher/ui/widgets/session_tree.py` - Tree widget

---

## Success Metrics

### Phase 1
- [ ] All v2 sessions migrated without data loss
- [ ] Chrome/Firefox/Edge launch with 5+ tabs each
- [ ] No Selenium dependency for basic launching
- [ ] Tests pass on Windows

### Phase 2
- [ ] VS Code opens with correct workspace
- [ ] Generic app launcher works for Slack/Spotify
- [ ] Cross-platform paths resolve correctly

### Phase 3
- [ ] Composite workflow launches 3+ apps in sequence
- [ ] Delays between launches work correctly
- [ ] Error in one app doesn't block others

### Phase 4
- [ ] Capture 10+ Chrome tabs automatically
- [ ] Detect open VS Code workspace
- [ ] Create session from captured state in <5 clicks

### Phase 5
- [ ] Create 3-level category hierarchy
- [ ] Drag-and-drop sessions between categories
- [ ] Expand/collapse state persists

### Phase 6
- [ ] All keyboard shortcuts functional
- [ ] Export/import preserves 100% of data
- [ ] Dark theme applies to all dialogs

---

## Risk Mitigation

### Risk: Browser state capture unreliable
**Mitigation**: Provide manual entry as fallback, make capture optional feature

### Risk: Cross-platform testing limited (only have Windows)
**Mitigation**: Use platform-specific abstractions, provide macOS user testing beta

### Risk: Too complex for ADHD use case
**Mitigation**: Keep UI simple, provide sensible defaults, make advanced features optional

### Risk: Migration breaks existing sessions
**Mitigation**: Always backup v2 config, provide rollback mechanism, extensive migration testing

---

## Next Steps

1. **Get user approval** on this plan
2. **Phase 1 implementation**: Start with folder structure and base classes
3. **Iterative development**: Complete one phase before starting next
4. **User testing**: Get feedback after each phase
5. **Documentation**: Write docs as features are built

This plan transforms the Chrome Session Launcher into a professional workflow management tool while preserving its simplicity and adding powerful new capabilities for managing ADHD/executive function challenges.


---

## Old text describing chrome session program:

Chrome Session Launcher - Project Overview

This is a desktop productivity application built with Python and PyQt6 that helps you organize and launch Chrome browser sessions with predefined sets of tabs.

What It Does
The app acts as a context switcher for web browsing - instead of manually opening multiple tabs every time you switch between different activities (work, entertainment, research), you can launch entire sets of tabs with one click.

Core Features
Session Management: Create, edit, and delete browsing sessions
Multi-Tab Launching: Open multiple URLs at once
YouTube Channel Switching: Special automation to switch YouTube accounts/channels
Custom Icons: Assign emojis to sessions for visual organization
Chrome Profile Support: Use specific Chrome profiles for different contexts

Technical Stack
Python 3 with PyQt6 (GUI framework)
Selenium WebDriver (browser automation)
JSON (configuration storage)
Windows batch file launcher

Key Files
src/context_launcher.py - Main application (461 lines)
src/config.json - Persistent session storage
launch.bat - Windows launcher script
old_code/ - Legacy PyQt5 version
Architecture

5 Main Classes:
ChromeLauncher - Selenium-based browser automation
LaunchWorker - Async thread for non-blocking launches
SessionDialog - Create/edit sessions
SettingsDialog - Configure Chrome/ChromeDriver paths
MainWindow - Main UI orchestration
The app follows an MVC-like pattern with clean separation between UI, business logic, and data storage. What would you like to work on? Some potential areas:
Adding new features
Improving existing functionality
Bug fixes
Code refactoring
Cross-platform support

CHAT:
Ok. I want to expand the scope of this project. Not only a chrome launcher, I want to use this to launch a "work session" of a certain type; so it could be a chrome window with certain tabs opened (thing that it already does), a vscode project in a certain folder, I dont have other idea in mind rn but it could be expanded more. 
It must serve to "manage" a litl bit my adhd/executive disfunction, place in a central place all the workflows and stuff i use more. 
Also for example i could remove some icons of software from my windows/macos toolbar, and put it into a section of this "launcher", to keep everything more clean
Currently i use both windows and macos, so possibly this should be multiplatform
It should be possible to "save" a certain workflow/software to open/state/etc in the program itself, from the gui, without reprogramming it. I'm thinking about saving "states" in a certain folder in json format; each json file for each session/scope (one for chrome sessions, one for programs to open i dunno etc)

Right now this is the interface:

Make a very detailed plan, in /context/plan.md that will allow us to develop this software, and expaind its current state. We can start from scratch if u want, taking only inspiration from original project, so we can create a better src folder structure, a better class organization, etc. It must be a very professional project

