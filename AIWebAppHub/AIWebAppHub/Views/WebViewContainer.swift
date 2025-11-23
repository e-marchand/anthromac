import SwiftUI
import WebKit

struct WebViewContainer: View {
    let service: WebService
    @StateObject private var webViewStore: WebViewStore

    init(service: WebService) {
        self.service = service
        _webViewStore = StateObject(wrappedValue: WebViewStore(service: service))
    }

    var body: some View {
        VStack(spacing: 0) {
            // Navigation bar
            HStack {
                Button(action: { webViewStore.goBack() }) {
                    Image(systemName: "chevron.left")
                }
                .disabled(!webViewStore.canGoBack)

                Button(action: { webViewStore.goForward() }) {
                    Image(systemName: "chevron.right")
                }
                .disabled(!webViewStore.canGoForward)

                Button(action: { webViewStore.reload() }) {
                    Image(systemName: "arrow.clockwise")
                }

                Spacer()

                if webViewStore.isLoading {
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
            WebView(webViewStore: webViewStore)
        }
    }
}

struct WebView: NSViewRepresentable {
    @ObservedObject var webViewStore: WebViewStore

    func makeNSView(context: Context) -> WKWebView {
        return webViewStore.webView
    }

    func updateNSView(_ nsView: WKWebView, context: Context) {
        // Updates handled by WebViewStore
    }
}

class WebViewStore: NSObject, ObservableObject {
    let service: WebService
    let webView: WKWebView
    private var downloadCoordinator: DownloadCoordinator?

    @Published var isLoading: Bool = false
    @Published var canGoBack: Bool = false
    @Published var canGoForward: Bool = false

    init(service: WebService) {
        self.service = service

        // Configure WebView
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = WKWebsiteDataStore.default()

        // Enable features for better web app compatibility
        configuration.preferences.setValue(true, forKey: "allowFileAccessFromFileURLs")
        configuration.preferences.javaScriptCanOpenWindowsAutomatically = true

        self.webView = WKWebView(frame: .zero, configuration: configuration)
        self.webView.allowsBackForwardNavigationGestures = true
        self.webView.customUserAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"

        super.init()

        self.webView.navigationDelegate = self
        self.webView.uiDelegate = self
        self.downloadCoordinator = DownloadCoordinator(webView: webView)

        // Load the service URL
        webView.load(URLRequest(url: service.url))

        // Setup observers
        setupObservers()
        setupNotifications()
    }

    private func setupObservers() {
        webView.addObserver(self, forKeyPath: #keyPath(WKWebView.isLoading), options: .new, context: nil)
        webView.addObserver(self, forKeyPath: #keyPath(WKWebView.canGoBack), options: .new, context: nil)
        webView.addObserver(self, forKeyPath: #keyPath(WKWebView.canGoForward), options: .new, context: nil)
    }

    private func setupNotifications() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleReload),
            name: .reloadWebView,
            object: nil
        )

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleClearData),
            name: .clearWebViewData,
            object: nil
        )
    }

    @objc private func handleReload(notification: Notification) {
        if let serviceID = notification.userInfo?["serviceID"] as? String,
           serviceID == service.id.uuidString {
            reload()
        }
    }

    @objc private func handleClearData(notification: Notification) {
        if let serviceID = notification.userInfo?["serviceID"] as? String,
           serviceID == service.id.uuidString {
            clearData()
        }
    }

    override func observeValue(forKeyPath keyPath: String?, of object: Any?, change: [NSKeyValueChangeKey : Any]?, context: UnsafeMutableRawPointer?) {
        if keyPath == #keyPath(WKWebView.isLoading) {
            isLoading = webView.isLoading
        } else if keyPath == #keyPath(WKWebView.canGoBack) {
            canGoBack = webView.canGoBack
        } else if keyPath == #keyPath(WKWebView.canGoForward) {
            canGoForward = webView.canGoForward
        }
    }

    func goBack() {
        webView.goBack()
    }

    func goForward() {
        webView.goForward()
    }

    func reload() {
        webView.reload()
    }

    func clearData() {
        let dataStore = WKWebsiteDataStore.default()
        let dataTypes = WKWebsiteDataStore.allWebsiteDataTypes()
        let date = Date(timeIntervalSince1970: 0)

        dataStore.removeData(ofTypes: dataTypes, modifiedSince: date) { [weak self] in
            DispatchQueue.main.async {
                self?.reload()
            }
        }
    }

    deinit {
        webView.removeObserver(self, forKeyPath: #keyPath(WKWebView.isLoading))
        webView.removeObserver(self, forKeyPath: #keyPath(WKWebView.canGoBack))
        webView.removeObserver(self, forKeyPath: #keyPath(WKWebView.canGoForward))
        NotificationCenter.default.removeObserver(self)
    }
}

extension WebViewStore: WKNavigationDelegate {
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        // Handle URL schemes that might require special handling
        if let url = navigationAction.request.url {
            // Allow navigation for auth flows
            if url.scheme == "https" || url.scheme == "http" {
                decisionHandler(.allow)
                return
            }

            // Handle custom URL schemes (e.g., for OAuth)
            if let scheme = url.scheme, !["http", "https"].contains(scheme) {
                NSWorkspace.shared.open(url)
                decisionHandler(.cancel)
                return
            }
        }

        decisionHandler(.allow)
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationResponse: WKNavigationResponse, decisionHandler: @escaping (WKNavigationResponsePolicy) -> Void) {
        decisionHandler(.allow)
    }
}

extension WebViewStore: WKUIDelegate {
    // Handle new window requests (for OAuth popups, etc.)
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration, for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        // If it's a popup/new window request, load it in the same webview
        if let url = navigationAction.request.url {
            // For auth flows, we might want to open in the same view
            webView.load(URLRequest(url: url))
        }
        return nil
    }

    // Handle JavaScript alerts
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alert = NSAlert()
        alert.messageText = "Alert"
        alert.informativeText = message
        alert.addButton(withTitle: "OK")
        alert.runModal()
        completionHandler()
    }

    // Handle JavaScript confirms
    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let alert = NSAlert()
        alert.messageText = "Confirm"
        alert.informativeText = message
        alert.addButton(withTitle: "OK")
        alert.addButton(withTitle: "Cancel")
        let response = alert.runModal()
        completionHandler(response == .alertFirstButtonReturn)
    }
}

#Preview {
    WebViewContainer(service: WebService.allServices[0])
        .frame(width: 800, height: 600)
}
