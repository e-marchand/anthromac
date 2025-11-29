import SwiftUI

// Helper function to open paths with apps
func openPath(_ path: String, withApp app: AppInfo) {
    let url = URL(fileURLWithPath: path)
    let appURL = URL(fileURLWithPath: app.path)
    NSWorkspace.shared.open([url], withApplicationAt: appURL, configuration: NSWorkspace.OpenConfiguration())
}

// App state management
class AppState: ObservableObject {
    @Published var currentView: ViewMode = .settings
    @Published var pathToOpen: String?

    enum ViewMode {
        case main
        case settings
        case appSelector
    }

    init() {
        // Handle command line arguments for opening paths
        let args = CommandLine.arguments
        if args.count > 1 {
            let path = args[1]
            self.pathToOpen = path

            // Check if path matches any rule
            if let matchingApp = AppManager.shared.findMatchingApp(for: path) {
                // Open with matching app and quit
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    openPath(path, withApp: matchingApp)
                    NSApplication.shared.terminate(nil)
                }
            } else {
                // Show app selector
                self.currentView = .appSelector
            }
        } else {
            // No path provided, show settings
            self.currentView = .settings
        }
    }
}

@main
struct PathOpenerApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            MainView()
                .environmentObject(appState)
        }
        .commands {
            CommandGroup(after: .appSettings) {
                Button("Settings...") {
                    appState.currentView = .settings
                }
                .keyboardShortcut(",", modifiers: .command)
            }
        }
    }
}

struct MainView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        Group {
            switch appState.currentView {
            case .settings:
                SettingsView()
                    .frame(minWidth: 600, minHeight: 400)
            case .appSelector:
                if let path = appState.pathToOpen {
                    AppSelectorView(path: path, onAppSelected: { app in
                        openPath(path, withApp: app)
                        NSApplication.shared.terminate(nil)
                    })
                    .frame(minWidth: 400, minHeight: 300)
                }
            case .main:
                ContentView()
                    .frame(width: 300, height: 200)
            }
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var appState: AppState

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
                appState.currentView = .settings
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
        let currentAppState = appState

        provider.loadItem(forTypeIdentifier: "public.file-url", options: nil) { item, error in
            guard let data = item as? Data,
                  let url = URL(dataRepresentation: data, relativeTo: nil) else { return }

            DispatchQueue.main.async {
                let path = url.path
                if let matchingApp = AppManager.shared.findMatchingApp(for: path) {
                    openPath(path, withApp: matchingApp)
                } else {
                    // Show app selector in the same window
                    currentAppState.pathToOpen = path
                    currentAppState.currentView = .appSelector
                }
            }
        }
    }
}
