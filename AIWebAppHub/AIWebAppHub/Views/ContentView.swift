import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        NavigationSplitView {
            SidebarView()
        } detail: {
            if let service = appState.selectedService {
                WebViewContainer(service: service)
            } else {
                Text("Select a service from the sidebar")
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(AppState())
}
