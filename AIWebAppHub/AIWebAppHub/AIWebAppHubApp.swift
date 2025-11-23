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
        .windowStyle(.hiddenTitleBar)
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
