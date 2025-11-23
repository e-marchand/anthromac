# AI Web App Hub

A modern macOS application that provides a unified interface for accessing multiple AI web services through a sidebar navigation.

## Features

- **Sidebar Navigation**: Quick access to multiple AI services
- **Persistent Sessions**: Each web app maintains its own WebView, so switching between services doesn't lose your place
- **Download Support**: Full file download functionality for each service
- **Authentication Handling**: Proper cookie and session management for staying logged in
- **Native App Integration**: Right-click context menu to open services in their native macOS apps (if installed)
- **Modern UI**: Clean, native macOS interface using SwiftUI

## Included Services

- **ChatGPT** (https://chatgpt.com/)
- **Claude** (https://claude.ai/)
- **Claude Code** (https://claude.ai/code)
- **Gemini** (https://gemini.google.com/app)
- **Grok** (https://grok.com/)
- **GitHub Copilot** (https://github.com/copilot)

## Project Structure

```
AIWebAppHub/
├── AIWebAppHub/
│   ├── AIWebAppHubApp.swift          # Main app entry point
│   ├── Models/
│   │   └── WebService.swift           # Service configuration models
│   ├── Views/
│   │   ├── ContentView.swift          # Main container view
│   │   ├── SidebarView.swift          # Sidebar with service list
│   │   └── WebViewContainer.swift     # WebView wrapper with navigation
│   ├── Utilities/
│   │   └── DownloadCoordinator.swift  # File download handler
│   └── Resources/
│       ├── Info.plist
│       └── Assets.xcassets/
└── AIWebAppHub.entitlements           # App sandbox entitlements
```

## Quick Start

See [SETUP.md](SETUP.md) for detailed step-by-step instructions.

### TL;DR

1. Open Xcode → Create new macOS App project named "AIWebAppHub"
2. Add all files from `AIWebAppHub/AIWebAppHub/` to your project
3. Configure App Sandbox with network client access
4. Set minimum deployment to macOS 13.0+
5. Build and run (⌘R)

## Usage

### Basic Navigation

- Click on any service in the sidebar to switch to that web app
- Use the back/forward buttons to navigate within each service
- Click the reload button to refresh the current page
- Loading indicator shows when pages are loading

### Context Menu Features

Right-click on any service in the sidebar to access:

- **Open in [Native App]**: Opens the service in its native macOS app (if installed)
- **Reload**: Refresh the current page
- **Clear Cookies & Cache**: Clear all data for that service and reload

### File Downloads

- Click any download link in the web apps
- A save dialog will appear to choose the download location
- Downloads are handled natively by macOS

### Authentication

- Sign in to each service normally through the web interface
- Cookies and sessions are preserved between app launches
- Each service has its own isolated cookie store
- OAuth and SSO flows are fully supported

## Adding More Services

To add additional services, edit `AIWebAppHub/Models/WebService.swift`:

```swift
WebService(
    name: "Service Name",
    url: URL(string: "https://example.com/")!,
    iconName: "service-icon",
    nativeAppBundleID: "com.example.app",  // Optional
    nativeAppName: "Example App",           // Optional
    color: .blue
)
```

## Requirements

- macOS 13.0 (Ventura) or later
- Xcode 15.0 or later (for development)

## Architecture

### WebView Management

Each service gets its own `WKWebView` instance that persists in memory. This means:
- Switching between services is instant
- Login sessions are maintained
- Form data and scroll positions are preserved

### Download Handling

Downloads are intercepted using:
1. JavaScript message handlers for `download` attribute links
2. WKNavigationDelegate for binary file responses
3. Native macOS save panel for user-friendly file management

### Authentication

- Uses WKWebsiteDataStore for cookie persistence
- Supports OAuth flows through popup handling
- Custom URL schemes can be registered for deep linking

## Security

The app uses macOS App Sandbox with minimal permissions:
- Network access for web requests
- User-selected file access for downloads only
- No access to system resources or user files beyond downloads

## Troubleshooting

### Services not loading

- Check your internet connection
- Try clearing cookies & cache for that service
- Ensure macOS firewall isn't blocking the app

### Authentication issues

- Some services may require specific user agents
- Try clearing cookies & cache and signing in again
- Check if the service supports web-based authentication

### Downloads not working

- Ensure the app has permission to access the Downloads folder
- Check macOS Privacy & Security settings

## Customization

### Changing Icons

Replace the SF Symbol icons in `SidebarView.swift`:

```swift
private func iconForService(_ name: String) -> String {
    switch name {
    case "ChatGPT": return "message.circle.fill"
    // Add your custom mappings
    }
}
```

### Custom User Agent

Modify the user agent in `WebViewContainer.swift`:

```swift
self.webView.customUserAgent = "Your custom user agent"
```

## Contributing

Feel free to submit issues or pull requests to improve the app.

## License

This project is provided as-is for personal use.