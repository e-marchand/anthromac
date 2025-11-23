# AI Web App Hub - Project Overview

## What This App Does

AI Web App Hub is a macOS desktop application that consolidates multiple AI web services into a single window with a sidebar for easy navigation. Think of it as a browser specifically designed for AI services, where each service maintains its own session independently.

## Key Features

### 1. Sidebar Navigation
- Clean, modern sidebar with icons for each AI service
- Single click to switch between services
- Right-click context menu for additional options

### 2. Persistent WebViews
Each service gets its own dedicated WebView that stays in memory. This means:
- No reloading when switching between services
- Login sessions persist
- Your work is exactly where you left it
- Each service has its own isolated cookies and cache

### 3. Download Support
- Full support for file downloads from any service
- Native macOS save dialog integration
- No download limitations

### 4. Authentication Management
- Automatic cookie persistence
- Support for OAuth and SSO flows
- New window handling for authentication popups
- Each service maintains separate authentication state

### 5. Native App Integration
Right-click on any service to:
- Open in native app (if installed, e.g., ChatGPT or Claude desktop apps)
- Reload the current page
- Clear all cookies and cache for that service

## Technical Implementation

### Architecture

```
┌─────────────────────────────────────────┐
│         AIWebAppHubApp (Main)           │
│              AppState                   │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼─────────┐
│  SidebarView   │    │  WebViewContainer│
│  - Service List│    │  - Navigation    │
│  - Selection   │    │  - WebView       │
│  - Context Menu│    │  - WebViewStore  │
└────────────────┘    └──────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
          ┌─────────▼────────┐  ┌───────▼──────────┐
          │ DownloadCoordinator│  │  WKWebView       │
          │ - File Handling   │  │  - Web Rendering │
          └───────────────────┘  └──────────────────┘
```

### Key Components

#### 1. Models
- **WebService**: Defines each web service (URL, name, icon, native app info)
- **ServiceInstance**: Allows multiple instances of the same service (for multiple accounts)

#### 2. Views
- **ContentView**: Main container using NavigationSplitView
- **SidebarView**: Service list with icons and context menus
- **WebViewContainer**: WebView wrapper with navigation controls
- **ServiceRow**: Individual sidebar item with icon and label

#### 3. WebView Management
- **WebViewStore**: ObservableObject that manages:
  - WKWebView instance and configuration
  - Navigation state (loading, canGoBack, canGoForward)
  - Notifications for reload and data clearing
  - Navigation delegation
  - UI delegation for popups and alerts

#### 4. Download Handling
- **DownloadCoordinator**: Manages file downloads:
  - JavaScript injection to intercept download links
  - Message handler for download requests
  - Native save panel integration
  - URLSession download task management

### WebView Configuration

Each WebView is configured with:
- Persistent data store (WKWebsiteDataStore.default())
- Custom user agent for compatibility
- JavaScript enabled
- Popup windows support
- Back/forward gesture navigation

### Data Isolation

Each service maintains:
- Separate cookies
- Separate cache
- Separate local storage
- Separate session storage

This is achieved through unique WKWebsiteDataStore instances per service instance.

## Security Considerations

### App Sandbox
The app runs in macOS App Sandbox with minimal permissions:
- **Network Client**: Required for web requests
- **User Selected Files**: For download functionality only

### No Tracking
- No analytics
- No data collection
- All data stays local
- Cookies only sent to their respective services

### Privacy
- Each service's data is isolated
- No cross-service cookie sharing
- Downloads require explicit user approval
- All network traffic is HTTPS

## Supported Services

### Currently Included

1. **ChatGPT** (https://chatgpt.com/)
   - Native app: Yes (com.openai.chat)
   - OAuth: Supported

2. **Claude** (https://claude.ai/)
   - Native app: Yes (com.anthropic.claude)
   - OAuth: Supported

3. **Claude Code** (https://claude.ai/code)
   - Native app: No (uses Claude app)
   - OAuth: Supported (shared with Claude)

4. **Gemini** (https://gemini.google.com/app)
   - Native app: No
   - OAuth: Supported (Google SSO)

5. **Grok** (https://grok.com/)
   - Native app: No
   - OAuth: Supported (X/Twitter SSO)

6. **GitHub Copilot** (https://github.com/copilot)
   - Native app: No
   - OAuth: Supported (GitHub SSO)
   - Multi-instance: Yes (for multiple GitHub accounts)

### Adding New Services

Edit `WebService.swift` and add a new entry:

```swift
WebService(
    name: "Your Service",
    url: URL(string: "https://yourservice.com/")!,
    iconName: "icon-name",
    nativeAppBundleID: "com.yourservice.app", // Optional
    nativeAppName: "YourService",              // Optional
    color: .yourColor
)
```

## Future Enhancements

### Potential Features
- [ ] Custom service profiles (save/load service configurations)
- [ ] Keyboard shortcuts for service switching
- [ ] Tab groups (organize services into categories)
- [ ] Service-specific user agent strings
- [ ] URL scheme handling (deep links)
- [ ] Extension support (custom JavaScript injection)
- [ ] Session export/import
- [ ] Window state persistence
- [ ] Multiple windows support
- [ ] Service usage statistics
- [ ] Dark mode forcing for services that don't support it
- [ ] Custom CSS injection per service
- [ ] Notification support

### Multiple Account Support
The ServiceManager class provides infrastructure for multiple instances:
- Duplicate any service with a custom name
- Each instance gets separate cookies/cache
- Useful for managing multiple accounts

## Development Notes

### Requirements
- macOS 13.0+ (Ventura)
- Xcode 15.0+
- Swift 5.9+
- SwiftUI

### Project Setup
See [SETUP.md](SETUP.md) for complete setup instructions.

### Building
1. Open project in Xcode
2. Select "My Mac" as the destination
3. Product → Build (⌘B)
4. Product → Run (⌘R)

### Code Style
- SwiftUI for all UI
- MVVM architecture
- ObservableObject for state management
- Combine for reactive updates

### Testing
- Test each service for login/logout
- Test file downloads
- Test OAuth flows
- Test context menu actions
- Test multiple account support

## Troubleshooting

### Common Issues

**WebView blank/won't load:**
- Check Info.plist has NSAppTransportSecurity configured
- Verify network entitlements
- Check firewall settings

**Authentication fails:**
- Clear cookies and cache for that service
- Some services may block WebViews - try different user agent
- Check if service requires app-specific authentication

**Downloads don't work:**
- Verify App Sandbox file access entitlements
- Check download coordinator is properly initialized
- Ensure user has write permissions to selected folder

**Native app option doesn't appear:**
- Verify app is actually installed
- Check bundle ID matches installed app
- Try restarting the Hub app

### Debug Mode

To enable debug logging, add to WebViewStore init:

```swift
webView.configuration.preferences.setValue(true, forKey: "developerExtrasEnabled")
```

Then right-click in any WebView → Inspect Element

## File Structure

```
AIWebAppHub/
├── AIWebAppHub/
│   ├── AIWebAppHubApp.swift              # App entry point
│   ├── Models/
│   │   └── WebService.swift               # Service definitions
│   ├── Views/
│   │   ├── ContentView.swift              # Main container
│   │   ├── SidebarView.swift              # Sidebar UI
│   │   └── WebViewContainer.swift         # WebView + controls
│   ├── Utilities/
│   │   ├── DownloadCoordinator.swift      # Download handling
│   │   └── ServiceManager.swift           # Multiple instance support
│   └── Resources/
│       ├── Info.plist                     # App configuration
│       └── Assets.xcassets/               # Icons and assets
├── AIWebAppHub.entitlements               # Sandbox config
├── README.md                               # User documentation
├── SETUP.md                                # Setup instructions
└── PROJECT_OVERVIEW.md                     # This file
```

## Contributing

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for personal use.

---

**Built with ❤️ using SwiftUI and WebKit**
