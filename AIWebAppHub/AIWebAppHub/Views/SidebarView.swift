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
            // Service icon with modern styling
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

            Text(service.name)
                .font(.system(size: 13, weight: .medium))
        }
        .padding(.vertical, 4)
    }

    private func iconForService(_ name: String) -> String {
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
