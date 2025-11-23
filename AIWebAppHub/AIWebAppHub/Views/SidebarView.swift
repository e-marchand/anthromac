import SwiftUI
import AppKit

struct SidebarView: View {
    @EnvironmentObject var appState: AppState
    @AppStorage("showServiceNames") private var showServiceNames = true

    var body: some View {
        List(WebService.allServices, selection: $appState.selectedService) { service in
            ServiceRow(service: service, showName: showServiceNames)
                .tag(service)
                .contextMenu {
                    if let bundleID = service.nativeAppBundleID,
                       let appName = service.nativeAppName,
                       isNativeAppInstalled(bundleID: bundleID) {
                        Button("Open in \(appName)") {
                            openNativeApp(bundleID: bundleID)
                        }
                    }

                    Button("Reload") {
                        NotificationCenter.default.post(
                            name: .reloadWebView,
                            object: nil,
                            userInfo: ["serviceID": service.id.uuidString]
                        )
                    }

                    Button("Clear Cookies & Cache") {
                        NotificationCenter.default.post(
                            name: .clearWebViewData,
                            object: nil,
                            userInfo: ["serviceID": service.id.uuidString]
                        )
                    }

                    Divider()

                    Button(showServiceNames ? "Hide Service Names" : "Show Service Names") {
                        showServiceNames.toggle()
                    }
                }
        }
        .listStyle(.sidebar)
        .safeAreaInset(edge: .top) {
            Color.clear.frame(height: 8)
        }
        .frame(minWidth: showServiceNames ? 200 : 60, idealWidth: showServiceNames ? 240 : 60)
    }

    private func isNativeAppInstalled(bundleID: String) -> Bool {
        let path = NSWorkspace.shared.urlForApplication(withBundleIdentifier: bundleID)
        return path != nil
    }

    private func openNativeApp(bundleID: String) {
        if let url = NSWorkspace.shared.urlForApplication(withBundleIdentifier: bundleID) {
            NSWorkspace.shared.open(url)
        }
    }
}

struct ServiceRow: View {
    let service: WebService
    let showName: Bool
    @State private var hasAssetIcon = false

    var body: some View {
        HStack(spacing: 12) {
            // Service icon - tries asset first, falls back to SF Symbol
            Group {
                if let assetName = iconAssetName(for: service.name), hasAssetIcon {
                    // Use custom asset icon
                    Image(assetName)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: 36, height: 36)
                        .cornerRadius(8)
                } else {
                    // Fallback to styled SF Symbol
                    ZStack {
                        RoundedRectangle(cornerRadius: 8)
                            .fill(
                                LinearGradient(
                                    colors: [service.color.opacity(0.3), service.color.opacity(0.15)],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                            .frame(width: 36, height: 36)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(service.color.opacity(0.3), lineWidth: 1)
                            )

                        Image(systemName: iconForService(service.name))
                            .foregroundStyle(service.color)
                            .font(.system(size: 18, weight: .semibold))
                            .symbolRenderingMode(.hierarchical)
                    }
                }
            }
            .onAppear {
                checkAssetAvailability()
            }

            if showName {
                Text(service.name)
                    .font(.system(size: 13, weight: .medium))
            }
        }
        .padding(.vertical, 4)
        .frame(maxWidth: .infinity, alignment: showName ? .leading : .center)
    }

    private func iconAssetName(for serviceName: String) -> String? {
        switch serviceName {
        case "ChatGPT": return "chatgpt"
        case "Claude", "Claude Code": return "claude"
        case "Gemini": return "gemini"
        case "Grok": return "grok"
        case "GitHub Copilot": return "github"
        default: return nil
        }
    }

    private func checkAssetAvailability() {
        if let assetName = iconAssetName(for: service.name) {
            // Check if the asset exists by trying to load it
            if NSImage(named: assetName) != nil {
                hasAssetIcon = true
            }
        }
    }

    private func iconForService(_ name: String) -> String {
        // Fallback SF Symbols
        switch name {
        case "ChatGPT": return "message.badge.filled.fill"
        case "Claude": return "brain.head.profile"
        case "Claude Code": return "curlybraces.square.fill"
        case "Gemini": return "sparkles.square.filled.on.square"
        case "Grok": return "bolt.shield.fill"
        case "GitHub Copilot": return "chevron.left.forwardslash.chevron.right"
        default: return "globe"
        }
    }
}

extension Notification.Name {
    static let reloadWebView = Notification.Name("reloadWebView")
    static let clearWebViewData = Notification.Name("clearWebViewData")
}

#Preview {
    SidebarView()
        .environmentObject(AppState())
        .frame(width: 200, height: 600)
}
