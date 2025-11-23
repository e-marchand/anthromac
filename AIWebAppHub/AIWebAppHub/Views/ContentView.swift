import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var webViewManager = WebViewManager()

    var body: some View {
        NavigationSplitView {
            SidebarView()
        } detail: {
            if let service = appState.selectedService {
                let store = webViewManager.getOrCreateWebViewStore(for: service)

                MultiWebViewContainer(selectedService: service, manager: webViewManager)
                    .id(service.id) // ensure toolbar state refreshes when selection changes
                    .toolbar {
                        // Back/Forward on the leading side (navigation placement)
                        ToolbarItemGroup(placement: .navigation) {
                            Button(action: { store.goBack() }) {
                                Image(systemName: "chevron.left")
                            }
                            .controlSize(.small)
                            .help("Back")
                            .disabled(!store.canGoBack)

                            Button(action: { store.goForward() }) {
                                Image(systemName: "chevron.right")
                            }
                            .controlSize(.small)
                            .help("Forward")
                            .disabled(!store.canGoForward)
                        }

                        // Reload
                        ToolbarItem(placement: .automatic) {
                            Button(action: { store.reload() }) {
                                Image(systemName: "arrow.clockwise")
                            }
                            .controlSize(.small)
                            .help("Reload")
                        }
                        
                        // Home
                        ToolbarItem(placement: .automatic) {
                            Button(action: { store.resetToHome() }) {
                                Image(systemName: "house")
                            }
                            .controlSize(.small)
                            .help("Go to home page")
                        }

                        // Loading indicator on the trailing/status area
                        ToolbarItem(placement: .status) {
                            if store.isLoading {
                                ProgressView()
                                    .controlSize(.small)
                            }
                        }

                        // Title in the center
                        ToolbarItem(placement: .principal) {
                            Text(service.name)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                                .lineLimit(1)
                                .truncationMode(.tail)
                        }
                    }
            } else {
                Text("Select a service from the sidebar")
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }
}

// Manager to maintain all WebView instances
class WebViewManager: ObservableObject {
    @Published var webViewStores: [UUID: WebViewStore] = [:]

    func getOrCreateWebViewStore(for service: WebService) -> WebViewStore {
        if let existing = webViewStores[service.id] {
            return existing
        }

        let newStore = WebViewStore(service: service)
        webViewStores[service.id] = newStore
        return newStore
    }
}

// Container that shows all WebViews but only displays the selected one
struct MultiWebViewContainer: View {
    let selectedService: WebService
    @ObservedObject var manager: WebViewManager

    var body: some View {
        ZStack {
            // Create WebViews for all services, but only show the selected one
            ForEach(WebService.allServices, id: \.id) { service in
                let store = manager.getOrCreateWebViewStore(for: service)

                // Only the WebView; toolbar lives in ContentView
                WebView(webViewStore: store)
                    .opacity(service.id == selectedService.id ? 1 : 0)
                    .allowsHitTesting(service.id == selectedService.id)
            }
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(AppState())
}
