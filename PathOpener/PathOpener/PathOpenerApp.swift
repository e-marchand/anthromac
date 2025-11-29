import SwiftUI

// Helper function to open paths with apps
func openPath(_ path: String, withApp app: AppInfo) {
    let url = URL(fileURLWithPath: path)
    let appURL = URL(fileURLWithPath: app.path)
    NSWorkspace.shared.open([url], withApplicationAt: appURL, configuration: NSWorkspace.OpenConfiguration())
}

@main
struct PathOpenerApp: App {
    @StateObject private var appManager = AppManager.shared
    @State private var pathToOpen: String?
    @State private var showSettings = false
    @State private var showAppSelector = false

    var body: some Scene {
        WindowGroup {
            if showSettings {
                SettingsView()
                    .frame(minWidth: 600, minHeight: 400)
            } else if showAppSelector, let path = pathToOpen {
                AppSelectorView(path: path, onAppSelected: { app in
                    openPath(path, withApp: app)
                    NSApplication.shared.terminate(nil)
                })
                .frame(minWidth: 400, minHeight: 300)
            } else {
                ContentView(onShowSettings: {
                    showSettings = true
                })
                .frame(width: 300, height: 200)
            }
        }
        .commands {
            CommandGroup(after: .appSettings) {
                Button("Settings...") {
                    showSettings = true
                }
                .keyboardShortcut(",", modifiers: .command)
            }
        }
    }

    init() {
        // Handle command line arguments for opening paths
        let args = CommandLine.arguments
        if args.count > 1 {
            let path = args[1]
            _pathToOpen = State(initialValue: path)

            // Check if path matches any rule
            if let matchingApp = appManager.findMatchingApp(for: path) {
                // Open with matching app and quit
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    openPath(path, withApp: matchingApp)
                    NSApplication.shared.terminate(nil)
                }
            } else {
                // Show app selector
                _showAppSelector = State(initialValue: true)
            }
        } else {
            // No path provided, show settings
            _showSettings = State(initialValue: true)
        }
    }
}

struct ContentView: View {
    let onShowSettings: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "folder.badge.gearshape")
                .font(.system(size: 60))
                .foregroundColor(.blue)

            Text("PathOpener")
                .font(.title)
                .fontWeight(.bold)

            Text("Drop a file or folder to open with configured apps")
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            Button("Open Settings") {
                onShowSettings()
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .onDrop(of: [.fileURL], isTargeted: nil) { providers in
            handleDrop(providers: providers)
            return true
        }
    }

    private func handleDrop(providers: [NSItemProvider]) {
        guard let provider = providers.first else { return }

        provider.loadItem(forTypeIdentifier: "public.file-url", options: nil) { item, error in
            guard let data = item as? Data,
                  let url = URL(dataRepresentation: data, relativeTo: nil) else { return }

            DispatchQueue.main.async {
                let path = url.path
                if let matchingApp = AppManager.shared.findMatchingApp(for: path) {
                    NSWorkspace.shared.open([url], withApplicationAt: URL(fileURLWithPath: matchingApp.path), configuration: NSWorkspace.OpenConfiguration())
                } else {
                    // Show app selector window
                    if let window = NSApplication.shared.windows.first {
                        let selectorView = AppSelectorView(path: path, onAppSelected: { app in
                            NSWorkspace.shared.open([url], withApplicationAt: URL(fileURLWithPath: app.path), configuration: NSWorkspace.OpenConfiguration())
                        })

                        let hostingController = NSHostingController(rootView: selectorView)
                        let newWindow = NSWindow(contentViewController: hostingController)
                        newWindow.title = "Select App"
                        newWindow.setContentSize(NSSize(width: 400, height: 300))
                        newWindow.makeKeyAndOrderFront(nil)
                    }
                }
            }
        }
    }
}
