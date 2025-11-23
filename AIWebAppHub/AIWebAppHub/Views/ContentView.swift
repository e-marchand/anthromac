import SwiftUI

struct ContentView: View {
    @EnvironmentObject var appState: AppState
    @StateObject private var webViewManager = WebViewManager()

    var body: some View {
        NavigationSplitView {
            SidebarView()
        } detail: {
            if let service = appState.selectedService {
                MultiWebViewContainer(selectedService: service, manager: webViewManager)
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

                VStack(spacing: 0) {
                    // Navigation bar
                    HStack {
                        Button(action: { store.goBack() }) {
                            Image(systemName: "chevron.left")
                        }
                        .disabled(!store.canGoBack)

                        Button(action: { store.goForward() }) {
                            Image(systemName: "chevron.right")
                        }
                        .disabled(!store.canGoForward)

                        Button(action: { store.reload() }) {
                            Image(systemName: "arrow.clockwise")
                        }

                        Spacer()

                        if store.isLoading {
                            ProgressView()
                                .scaleEffect(0.7)
                        }

                        Text(service.name)
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(.secondary)

                        Spacer()
                    }
                    .padding(8)
                    .background(Color(NSColor.windowBackgroundColor))

                    // WebView
                    WebView(webViewStore: store)
                }
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
