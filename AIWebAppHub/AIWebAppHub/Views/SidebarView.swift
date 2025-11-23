import SwiftUI
import AppKit

struct SidebarView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        List(WebService.allServices, selection: $appState.selectedService) { service in
            ServiceRow(service: service)
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
                }
        }
        .listStyle(.sidebar)
        .frame(minWidth: 200)
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

    var body: some View {
        HStack(spacing: 12) {
            // Service icon
            if let iconName = iconAssetName(for: service.name) {
                Image(iconName)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(width: 32, height: 32)
                    .cornerRadius(6)
            } else {
                // Fallback to SF Symbol if icon not found
                ZStack {
                    Circle()
                        .fill(service.color.opacity(0.2))
                        .frame(width: 32, height: 32)

                    Image(systemName: iconForService(service.name))
                        .foregroundColor(service.color)
                        .font(.system(size: 16, weight: .semibold))
                }
            }

            Text(service.name)
                .font(.system(size: 13))
        }
        .padding(.vertical, 4)
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

    private func iconForService(_ name: String) -> String {
        // Fallback SF Symbols
        switch name {
        case "ChatGPT": return "message.circle.fill"
        case "Claude", "Claude Code": return "brain.fill"
        case "Gemini": return "sparkles"
        case "Grok": return "bolt.circle.fill"
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
