import SwiftUI

// Helper function to open paths with apps
func openPath(_ path: String, withApp app: AppInfo) {
    // If commandLine is specified, use Process to execute it
    if let commandLine = app.commandLine, !commandLine.isEmpty {
        executeCommandLine(commandLine, path: path, app: app)
    } else {
        // Use NSWorkspace for .app bundles
        let url = URL(fileURLWithPath: path)
        let appURL = URL(fileURLWithPath: app.path)

        // Check if app has custom command line arguments
        if let args = app.resolveCommandLineArgs(forPath: path) {
            // Launch with command line arguments
            let config = NSWorkspace.OpenConfiguration()
            config.arguments = args
            NSWorkspace.shared.open([url], withApplicationAt: appURL, configuration: config)
        } else {
            // Launch normally without arguments
            NSWorkspace.shared.open([url], withApplicationAt: appURL, configuration: NSWorkspace.OpenConfiguration())
        }
    }
}

// Execute command line with Process
func executeCommandLine(_ commandLine: String, path: String, app: AppInfo) {
    let process = Process()

    // Resolve the command line by replacing variables
    let resolvedCommand = commandLine
        .replacingOccurrences(of: "{FOLDER}", with: path)
        .replacingOccurrences(of: "{FILE}", with: path)

    // Parse the command line to get executable and arguments
    var components = parseCommandLineArgs(resolvedCommand)

    guard !components.isEmpty else { return }

    let executable = components.removeFirst()

    // Check if executable is a full path or needs to be resolved
    let executablePath: String
    if executable.hasPrefix("/") {
        executablePath = executable
    } else {
        // Try to find in PATH
        executablePath = findInPath(executable) ?? executable
    }

    process.executableURL = URL(fileURLWithPath: executablePath)

    // Add path as argument
    var args = components

    // Add custom arguments if specified
    if let customArgs = app.resolveCommandLineArgs(forPath: path) {
        args.append(contentsOf: customArgs)
    } else {
        // If no custom args, just add the path
        args.append(path)
    }

    process.arguments = args

    do {
        try process.run()
    } catch {
        print("Failed to execute command: \(error)")
    }
}

// Find executable in PATH
func findInPath(_ executable: String) -> String? {
    let paths = ProcessInfo.processInfo.environment["PATH"]?.split(separator: ":") ?? []

    for pathDir in paths {
        let fullPath = "\(pathDir)/\(executable)"
        if FileManager.default.isExecutableFile(atPath: fullPath) {
            return fullPath
        }
    }

    return nil
}

// Parse command line arguments (same logic as in AppInfo)
func parseCommandLineArgs(_ args: String) -> [String] {
    var result: [String] = []
    var current = ""
    var inQuotes = false

    for char in args {
        if char == "\"" {
            inQuotes.toggle()
        } else if char == " " && !inQuotes {
            if !current.isEmpty {
                result.append(current)
                current = ""
            }
        } else {
            current.append(char)
        }
    }

    if !current.isEmpty {
        result.append(current)
    }

    return result
}

// App state management
class AppState: ObservableObject {
    @Published var currentView: ViewMode = .main
    @Published var pathToOpen: String?

    enum ViewMode {
        case main
        case settings
        case appSelector
    }

    init() {
        // Handle command line arguments for opening paths
        // Filter out debug flags (arguments starting with "-")
        let pathArgs = CommandLine.arguments.dropFirst().filter { !$0.hasPrefix("-") }

        // Find the first valid file or directory path
        if let validPath = pathArgs.first(where: { FileManager.default.fileExists(atPath: $0) }) {
            self.pathToOpen = validPath

            // Check if path matches any rule
            if let matchingApp = AppManager.shared.findMatchingApp(for: validPath) {
                // Open with matching app and quit
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    openPath(validPath, withApp: matchingApp)
                    NSApplication.shared.terminate(nil)
                }
            } else {
                // Show app selector
                self.currentView = .appSelector
            }
        }
        // else: No valid path provided, show main view (default)
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
