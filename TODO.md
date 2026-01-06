# Context Launcher - TODO & Roadmap

## Current Status
- ✅ Phase 1-3: Core functionality (browser/editor/generic launchers, workflows)
- ✅ Phase 5: Category organization (tree/tab dual views)
- ✅ Phase 6: Window management, favorites, backup/restore, dark theme

## Roadmap

### Phase 7: GUI Polish & UX Improvements
**Goal:** Refine existing features at the GUI level for better user experience

**Tasks:**
- [ ] Improve visual design and layout
- [ ] Better integrate favorites into the UI (dedicated view/filter?)
- [ ] Enhanced window position configuration dialog
- [ ] Visual feedback for window positioning (progress indicators)
- [ ] Better error messages and user notifications
- [ ] Streamline session/workflow creation dialogs
- [ ] Add icons/visual indicators for different app types
- [ ] Improve context menus (better organization, icons)
- [ ] Polish dark theme (ensure all UI elements are themed)
- [ ] Add tooltips and help text throughout UI
- [ ] Session/workflow preview cards (show what will launch)
- [ ] Better drag-and-drop visual feedback in tree view

### Phase 8: State Capture System
**Goal:** Capture current workspace layout and convert it into a workflow

**Vision:**
The user should be able to:
1. Manually arrange windows on their screen exactly how they want them
2. Click a "Capture Workspace" button in Context Launcher
3. Enter a capture wizard that guides them through selecting windows
4. Click on window title bars to select which programs to capture
5. System automatically detects:
   - Executable path of the application
   - Window position (x, y)
   - Window size (width, height)
   - Monitor index
   - Window state (maximized, normal, etc.)
6. Save all captured windows as a new workflow
7. Later, launch that workflow to recreate the exact layout

**Technical Implementation:**

#### 8.1 Capture Wizard UI
- [ ] Add "📸 Capture Workspace" button to main window
- [ ] Create capture wizard dialog with instructions
- [ ] Implement window selection mode:
  - Overlay semi-transparent screen to indicate capture mode
  - Instructions: "Click window title bars to capture..."
  - Visual feedback when hovering over windows
  - Click to add window to capture list
  - Show list of captured windows with preview
  - Allow reordering captured windows
  - Remove button for each captured window

#### 8.2 Window Detection & Analysis
- [ ] Implement click-to-window detection:
  - Get window handle (HWND) from mouse click on title bar
  - Extract window information from HWND:
    - Process ID
    - Executable path (from process)
    - Window title
    - Window position and size
    - Monitor information
    - Window state (maximized, minimized, normal)
- [ ] Handle edge cases:
  - Multi-process apps (Chrome, Spotify, etc.)
  - Apps without standard title bars
  - Multiple windows from same app

#### 8.3 Workflow Generation
- [ ] Convert captured windows into workflow structure:
  - Create Session for each captured window
  - Auto-detect app type (browser, editor, generic)
  - Extract command-line arguments if possible
  - Set window_state for each session
  - Group all sessions into a Workflow
- [ ] Workflow naming and organization:
  - Prompt user for workflow name
  - Auto-suggest name based on captured apps
  - Choose category for workflow
  - Add description/tags

#### 8.4 Browser Tab Capture (Advanced)
- [ ] For browsers, capture open tabs:
  - Chrome: Read tabs from debugging protocol or bookmarks
  - Firefox: Read from session store
  - Edge: Similar to Chrome
- [ ] Add captured URLs to browser session configuration

#### 8.5 VS Code Workspace Capture
- [ ] Detect open VS Code workspace/folder
- [ ] Extract workspace path from process
- [ ] Configure VS Code session with workspace

#### 8.6 Validation & Testing
- [ ] Test capture wizard with various window types
- [ ] Test workflow recreation matches original layout
- [ ] Handle missing executables gracefully
- [ ] Test with multi-monitor setups

**User Flow Example:**
```
1. User arranges windows:
   - Chrome (left half of Monitor 1)
   - VS Code (right half of Monitor 1)
   - Spotify (top-right corner of Monitor 2)
   - Slack (bottom-right corner of Monitor 2)

2. User clicks "Capture Workspace" in Context Launcher

3. Wizard appears: "Click on each window title bar you want to capture"

4. User clicks:
   - Chrome title bar → System captures chrome.exe, position (0, 0, 960, 1080)
   - VS Code title bar → System captures Code.exe, workspace path, position (960, 0, 960, 1080)
   - Spotify title bar → System captures Spotify.exe, position (1920, 0, 400, 300)
   - Slack title bar → System captures slack.exe, position (1920, 300, 400, 780)

5. User clicks "Finish Capture"

6. Workflow creation dialog:
   - Name: "Morning Work Setup"
   - Category: "Work"
   - Description: "My typical morning workspace"
   - Shows list of 4 captured apps

7. User saves → Workflow created with 4 sessions, each with window_state configured

8. Next day: User double-clicks "Morning Work Setup" workflow
   → All 4 apps launch and position themselves exactly as captured
```

**Benefits:**
- ⚡ Much faster than manually creating sessions
- 🎯 Ensures exact layout recreation
- 🔄 Easy to update (just re-capture)
- 👁️ Visual, intuitive workflow creation
- 🚀 Perfect for ADHD users (minimal setup friction)

---

## Future Enhancements (Phase 9+)

### Not Yet Prioritized:
- [ ] Hierarchical categories (nested folders)
- [ ] Advanced search and filtering
- [ ] Keyboard shortcuts system
- [ ] System tray integration with quick launch menu
- [ ] Launch on startup option
- [ ] Session templates (create sessions from templates)
- [ ] Cloud sync integration
- [ ] Scheduled/automatic workflow launches
- [ ] Window arrangement presets (split-screen templates)
- [ ] Multi-monitor configuration detection
- [ ] Export/import individual sessions (not just full backup)

---

## Known Issues & Technical Debt

### Window Management:
- [ ] macOS and Linux implementations (currently Windows-only)
- [ ] Multiple windows from same app (only first window positioned)
- [ ] Brief flash when window repositions (can we minimize this?)

### UI/UX:
- [ ] Drag-and-drop validation could be stricter
- [ ] Some error messages are too technical

### Performance:
- [ ] Large number of sessions (100+) might slow down UI
- [ ] Consider lazy loading or pagination

---

## Development Notes

### Technology Stack:
- Python 3.11+
- PySide6 (Qt6) - GUI
- pywin32 - Windows API (window management)
- psutil - Process information
- Pydantic - Data validation

### Key Files:
- `src/context_launcher/ui/main_window.py` - Main UI
- `src/context_launcher/core/window_manager.py` - Window positioning
- `src/context_launcher/core/session.py` - Data models
- `src/context_launcher/launchers/` - App launchers

### Testing:
- Manual testing with test scripts in `tests/`
- Window positioning tested with Notepad and Chrome
