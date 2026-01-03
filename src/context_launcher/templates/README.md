# Default Templates

This directory contains JSON template files that define the default tabs and sessions created when Context Launcher runs for the first time.

## Files

### `default_tabs.json`
Defines the default category tabs shown in the main window.

**Structure:**
```json
{
  "version": "3.0",
  "tabs": [
    {
      "id": "unique-id",
      "name": "Display Name",
      "icon": "emoji-icon",
      "order": 0
    }
  ]
}
```

**Fields:**
- `id`: Unique identifier (lowercase, no spaces)
- `name`: Display name shown in UI
- `icon`: Emoji icon (single emoji character)
- `order`: Sort order (lower numbers appear first)

**Example:**
```json
{
  "id": "morning",
  "name": "Morning Routine",
  "icon": "☀️",
  "order": 0
}
```

### `default_sessions.json`
Defines the default sessions created on first run.

**Structure:**
```json
{
  "version": "3.0",
  "sessions": [
    {
      "name": "Session Name",
      "icon": "emoji",
      "description": "Description",
      "tab_id": "work",
      "type": "single_app",
      "metadata": {
        "category_id": "work",
        "tags": [],
        "favorite": false
      },
      "launch_config": {
        "app_type": "browser",
        "app_name": "chrome",
        "parameters": {
          "tabs": [
            {"type": "url", "url": "https://example.com"}
          ],
          "profile": ""
        }
      }
    }
  ]
}
```

**App Types:**

1. **Browser** (`app_type: "browser"`)
   - `app_name`: "chrome", "firefox", or "edge"
   - `parameters.tabs`: Array of `{"type": "url", "url": "..."}` or `{"type": "youtube", "channelHandle": "@handle"}`
   - `parameters.profile`: Browser profile name (optional)

2. **Editor** (`app_type: "editor"`)
   - `app_name`: "vscode"
   - `parameters.workspace`: Path to workspace/folder

3. **Generic App** (`app_type: "generic"`)
   - `app_name`: "slack", "spotify", or "generic"
   - `parameters.executable_path`: Full path to executable (for generic)
   - `parameters.arguments`: Array of command-line arguments (optional)
   - `parameters.working_directory`: Working directory (optional)

## Customizing Defaults

To customize the defaults:

1. Edit the JSON files in this directory
2. Delete `tabs.json` and `sessions/` directory from user data folder:
   - Windows: `%LOCALAPPDATA%\FraH\ContextLauncher\`
   - macOS: `~/Library/Application Support/ContextLauncher/`
   - Linux: `~/.local/share/ContextLauncher/`
3. Restart the application

The app will recreate defaults from your modified templates.

## Notes

- `id` and `created_at`/`updated_at` fields in sessions are auto-generated and can be omitted from templates
- Sessions reference tabs via `tab_id` - ensure the tab exists in `default_tabs.json`
- The template files are packaged with the application and won't be modified by the app
