# Quick Setup Guide

## Step-by-Step Instructions

### 1. Open Xcode

Launch Xcode on your Mac.

### 2. Create New Project

1. Select **File** → **New** → **Project**
2. Choose **macOS** → **App**
3. Click **Next**

### 3. Configure Project

Fill in the following details:

- **Product Name**: `AIWebAppHub`
- **Team**: Select your development team
- **Organization Identifier**: `com.yourname` (or your preferred identifier)
- **Bundle Identifier**: Will auto-populate as `com.yourname.AIWebAppHub`
- **Interface**: **SwiftUI**
- **Language**: **Swift**
- **Use Core Data**: Unchecked
- **Include Tests**: Optional (you can check if you want)

Click **Next**

### 4. Save Location

1. Navigate to this repository directory (`anthromac/`)
2. Click **Create**

### 5. Add Source Files

1. In Xcode's Project Navigator (left sidebar), you'll see the `AIWebAppHub` folder
2. Delete the default files:
   - Right-click `AIWebAppHubApp.swift` → Delete → Move to Trash
   - Right-click `ContentView.swift` → Delete → Move to Trash
3. Add our source files:
   - Right-click the `AIWebAppHub` folder → **Add Files to "AIWebAppHub"**
   - Navigate to `AIWebAppHub/AIWebAppHub/` directory
   - Select ALL files and folders
   - Make sure **Copy items if needed** is UNCHECKED
   - Make sure **Create groups** is selected
   - Click **Add**

### 6. Configure Entitlements

1. Click on the blue `AIWebAppHub` project icon at the top of the Project Navigator
2. Select the `AIWebAppHub` target
3. Go to the **Signing & Capabilities** tab
4. Click **+ Capability**
5. Add **App Sandbox**
6. Configure the sandbox:
   - Under **Network**: Check **Outgoing Connections (Client)**
   - Under **File Access**: Check **User Selected File** (Read/Write)

### 7. Set Info.plist

1. In the **Info** tab of your target
2. Click **+** to add a new key
3. Add `NSAppTransportSecurity` → Dictionary
4. Inside it, add `NSAllowsArbitraryLoads` → Boolean → YES
   - This allows loading of the web services (they all use HTTPS but this prevents issues)

### 8. Set Deployment Target

1. In the **General** tab
2. Set **Minimum Deployments** to **macOS 13.0** or later

### 9. Build and Run

1. Select a destination: **My Mac** (or **My Mac (Designed for iPad)** if needed)
2. Press **⌘R** or click the **Play** button
3. The app should build and launch

## First Run

When the app launches for the first time:

1. You'll see the sidebar with all AI services listed
2. Click on any service to load it
3. Sign in to each service you want to use
4. Your sessions will be preserved between app launches

## Testing Downloads

1. Navigate to any service
2. Try downloading a file (e.g., export a conversation from ChatGPT)
3. The macOS save panel should appear
4. Select a location and save

## Testing Right-Click Menu

1. Right-click on any service in the sidebar
2. You should see:
   - **Open in [App]** (only if the native app is installed)
   - **Reload**
   - **Clear Cookies & Cache**

## Troubleshooting Setup

### "Cannot find X in scope"

- Make sure all Swift files are added to the target
- Check Project Navigator → Select a file → File Inspector (right panel) → Target Membership

### Sandbox Issues

- Ensure App Sandbox is properly configured with network client access
- Check entitlements file is linked to the target

### WebView not loading

- Check Info.plist has NSAppTransportSecurity configured
- Verify network entitlements are enabled

### Code signing errors

- Select a development team in **Signing & Capabilities**
- You may need to create a free Apple Developer account if you don't have one

## Next Steps

After successful setup:

1. Customize the services in `Models/WebService.swift`
2. Add custom icons to the asset catalog
3. Customize the UI colors and styles
4. Add more services as needed

## Need Help?

If you encounter issues:

1. Clean build folder: **Product** → **Clean Build Folder** (⌘⇧K)
2. Restart Xcode
3. Check that all files are properly added to the target
4. Verify your macOS and Xcode versions meet the requirements
