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
                    // Compact navigation bar
                    HStack(spacing: 8) {
                        Button(action: { store.goBack() }) {
                            Image(systemName: "chevron.left")
                                .font(.system(size: 11, weight: .medium))
                        }
                        .buttonStyle(.plain)
                        .disabled(!store.canGoBack)
                        .opacity(store.canGoBack ? 1.0 : 0.3)

                        Button(action: { store.goForward() }) {
                            Image(systemName: "chevron.right")
                                .font(.system(size: 11, weight: .medium))
                        }
                        .buttonStyle(.plain)
                        .disabled(!store.canGoForward)
                        .opacity(store.canGoForward ? 1.0 : 0.3)

                        Button(action: { store.reload() }) {
                            Image(systemName: "arrow.clockwise")
                                .font(.system(size: 11, weight: .medium))
                        }
                        .buttonStyle(.plain)

                        if store.isLoading {
                            ProgressView()
                                .controlSize(.small)
                                .scaleEffect(0.6)
                        }

                        Spacer()
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color(NSColor.windowBackgroundColor).opacity(0.5))

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
