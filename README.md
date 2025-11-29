# PathOpener

A macOS application that intelligently opens files and folders with your preferred applications based on configurable glob pattern rules.

## Features

- **Smart Path Opening**: Automatically opens paths with the right application based on glob patterns
- **Application Management**: Configure macOS apps and scripts to handle your files
- **Rule-Based Routing**: Define glob patterns to automatically route paths to specific applications
- **Interactive Selection**: When no rule matches, choose from your configured applications
- **Visual Interface**: See application icons, names, and paths in an intuitive UI
- **Drag & Drop Support**: Drop files/folders directly onto the app

## How It Works

1. **With Rules**: When launched with a path, PathOpener checks your configured rules. If a glob pattern matches, it automatically opens the path with the associated application.

2. **Without Rules**: If no rule matches, PathOpener displays a list of your configured applications with their icons and paths, allowing you to select one.

3. **Settings Panel**: When launched without arguments, PathOpener opens the settings panel where you can:
   - Add macOS applications or scripts
   - Remove applications
   - Configure glob pattern rules for each application
   - Enable/disable rules
   - See application icons, names, and paths

## Usage

### Basic Usage

```bash
# Launch with a file path
./PathOpener.app/Contents/MacOS/PathOpener /path/to/file.txt

# Launch with a folder path
./PathOpener.app/Contents/MacOS/PathOpener /path/to/folder

# Launch without arguments to open settings
./PathOpener.app/Contents/MacOS/PathOpener
```

### Setting Up Applications

1. Open PathOpener (launches settings by default)
2. Click the "+" button to add an application
3. Select a macOS app (`.app`) or script file
4. The application appears in the list with its icon and path

### Configuring Rules

1. Select an application from the list
2. In the rules editor, enter a glob pattern
3. Click "Add Rule"
4. Rules are evaluated in order for each path

### Glob Pattern Examples

```
**/*.js              # All JavaScript files anywhere
**/*.{ts,tsx}        # TypeScript files anywhere
/Users/*/Documents/** # Any file in any user's Documents
*.pdf                # PDF files in current directory
/tmp/**              # Everything in /tmp
**/*.test.js         # All test JavaScript files
```

### Removing Items

- **Remove Application**: Right-click an application and select "Remove"
- **Remove Rule**: Click the trash icon next to a rule

## Building the App

### Requirements

- macOS 13.0 or later
- Xcode 15.0 or later
- Swift 5.0 or later

### Build Instructions

1. Open the project in Xcode:
   ```bash
   open PathOpener/PathOpener.xcodeproj
   ```

2. Build the application:
   - Select "Product" → "Build" (⌘B)
   - Or run: `xcodebuild -project PathOpener/PathOpener.xcodeproj -scheme PathOpener -configuration Release build`

3. The built app will be located in:
   ```
   ~/Library/Developer/Xcode/DerivedData/PathOpener-*/Build/Products/Release/PathOpener.app
   ```

### Quick Build Script

```bash
#!/bin/bash
xcodebuild -project PathOpener/PathOpener.xcodeproj \
           -scheme PathOpener \
           -configuration Release \
           -derivedDataPath ./build \
           build

echo "Built app is at: ./build/Build/Products/Release/PathOpener.app"
```

## Project Structure

```
PathOpener/
├── PathOpener.xcodeproj/
│   └── project.pbxproj           # Xcode project file
└── PathOpener/
    ├── PathOpenerApp.swift       # Main app entry point
    ├── Models.swift              # Data models (AppInfo, PathRule)
    ├── AppManager.swift          # Application and rule management
    ├── SettingsView.swift        # Settings panel UI
    ├── AppSelectorView.swift     # App selection UI
    ├── Info.plist               # App configuration
    └── PathOpener.entitlements  # Security entitlements
```

## Architecture

### Components

- **PathOpenerApp**: Main app entry point that handles command-line arguments and window management
- **AppManager**: Singleton that manages the list of applications and their rules, with persistence
- **Models**: Data structures for applications (`AppInfo`) and glob rules (`PathRule`)
- **SettingsView**: UI for managing applications and their rules
- **AppSelectorView**: UI for selecting an application when no rule matches

### Data Persistence

Application configurations and rules are stored in `UserDefaults` and persist across launches.

### Glob Pattern Matching

PathRule converts glob patterns to regex patterns for matching:
- `*` matches any characters except `/`
- `**` matches any number of directories
- `?` matches a single character
- Character classes like `[abc]` and `{js,ts}` are supported

## Example Workflows

### Workflow 1: JavaScript Developer

```
Applications:
- VSCode (/Applications/Visual Studio Code.app)
  Rules:
  - **/*.js
  - **/*.jsx
  - **/*.json

- WebStorm (/Applications/WebStorm.app)
  Rules:
  - **/package.json
  - **/tsconfig.json
```

### Workflow 2: Media Files

```
Applications:
- VLC (/Applications/VLC.app)
  Rules:
  - **/*.{mp4,mkv,avi,mov}

- QuickTime (/System/Applications/QuickTime Player.app)
  Rules:
  - **/*.{m4v,mp3}
```

### Workflow 3: Scripts and Automation

```
Applications:
- Custom Script (/Users/me/scripts/process.sh)
  Rules:
  - /Users/me/Downloads/**/*.csv
  - /tmp/data/**
```

## License

MIT License - Feel free to use and modify as needed.