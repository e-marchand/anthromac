# Quick Setup Guide

The Xcode project is already configured and ready to use! Just follow these simple steps:

## Step-by-Step Instructions

### 1. Open the Project

1. Navigate to the `AIWebAppHub` folder
2. Double-click `AIWebAppHub.xcodeproj` to open it in Xcode

**Alternative:** In Finder, navigate to the repository and double-click `AIWebAppHub/AIWebAppHub.xcodeproj`

### 2. Configure Code Signing

1. In Xcode, select the blue `AIWebAppHub` project icon in the Project Navigator (left sidebar)
2. Select the `AIWebAppHub` target
3. Go to the **Signing & Capabilities** tab
4. Under **Signing**, select your **Team** from the dropdown
   - If you don't have a team, you can use a free Apple ID
   - You may need to sign in with your Apple ID in Xcode Preferences

### 3. Verify Entitlements (Already Configured)

The following should already be set up:
- ✅ App Sandbox enabled
- ✅ Network: Outgoing Connections (Client)
- ✅ File Access: User Selected File (Read/Write)

### 4. Build and Run

1. Select **My Mac** as the destination (top toolbar)
2. Press **⌘R** or click the **Play** button
3. The app should build and launch automatically

**That's it!** The project is fully configured with all source files, entitlements, and build settings.

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
