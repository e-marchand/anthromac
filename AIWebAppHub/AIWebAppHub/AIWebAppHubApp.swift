import SwiftUI

@main
struct AIWebAppHubApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(appState)
                .frame(minWidth: 1000, minHeight: 600)
        }
        // Use a compact unified toolbar so the top bar is not too tall.
        .windowToolbarStyle(.unifiedCompact)
        // Keep the title bar visible so the toolbar can appear.
        // Remove the hidden title bar style that would hide the toolbar area.
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}

class AppState: ObservableObject {
    @Published var selectedService: WebService?

    init() {
        // Select first service by default
        self.selectedService = WebService.allServices.first
    }
}
