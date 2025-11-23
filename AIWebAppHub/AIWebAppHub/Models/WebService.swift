import Foundation
import SwiftUI

struct WebService: Identifiable, Equatable, Hashable {
    let id = UUID()
    let name: String
    let url: URL
    let iconName: String
    let nativeAppBundleID: String?
    let nativeAppName: String?
    let color: Color

    static func == (lhs: WebService, rhs: WebService) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static let allServices: [WebService] = [
        WebService(
            name: "ChatGPT",
            url: URL(string: "https://chatgpt.com/")!,
            iconName: "chatgpt",
            nativeAppBundleID: "com.openai.chat",
            nativeAppName: "ChatGPT",
            color: .green
        ),
        WebService(
            name: "Claude",
            url: URL(string: "https://claude.ai/")!,
            iconName: "claude",
            nativeAppBundleID: "com.anthropic.claude",
            nativeAppName: "Claude",
            color: .orange
        ),
        WebService(
            name: "Claude Code",
            url: URL(string: "https://claude.ai/code")!,
            iconName: "claude-code",
            nativeAppBundleID: nil,
            nativeAppName: nil,
            color: .purple
        ),
        WebService(
            name: "Gemini",
            url: URL(string: "https://gemini.google.com/app")!,
            iconName: "gemini",
            nativeAppBundleID: nil,
            nativeAppName: nil,
            color: .blue
        ),
        WebService(
            name: "Grok",
            url: URL(string: "https://grok.com/")!,
            iconName: "grok",
            nativeAppBundleID: nil,
            nativeAppName: nil,
            color: .gray
        ),
        WebService(
            name: "GitHub Copilot",
            url: URL(string: "https://github.com/copilot")!,
            iconName: "copilot",
            nativeAppBundleID: nil,
            nativeAppName: nil,
            color: .indigo
        )
    ]
}
