import Foundation
import AppKit

class AppManager: ObservableObject {
    static let shared = AppManager()

    @Published var apps: [AppInfo] = []

    private let userDefaultsKey = "configuredApps"

    init() {
        loadApps()
    }

    func addApp(at path: String) {
        let fileManager = FileManager.default

        // Verify the path exists
        guard fileManager.fileExists(atPath: path) else {
            print("App not found at path: \(path)")
            return
        }

        // Get app name
        let name = (path as NSString).lastPathComponent.replacingOccurrences(of: ".app", with: "")

        // Get app icon
        let icon = NSWorkspace.shared.icon(forFile: path)
        let iconData = icon.tiffRepresentation

        let newApp = AppInfo(name: name, path: path, iconData: iconData, rules: [])
        apps.append(newApp)
        saveApps()
    }

    func addScript(at path: String, name: String) {
        let fileManager = FileManager.default

        guard fileManager.fileExists(atPath: path) else {
            print("Script not found at path: \(path)")
            return
        }

        // Use generic script icon
        let icon = NSWorkspace.shared.icon(forFileType: "public.script")
        let iconData = icon.tiffRepresentation

        let newApp = AppInfo(name: name, path: path, iconData: iconData, rules: [])
        apps.append(newApp)
        saveApps()
    }

    func removeApp(_ app: AppInfo) {
        apps.removeAll { $0.id == app.id }
        saveApps()
    }

    func updateApp(_ app: AppInfo) {
        if let index = apps.firstIndex(where: { $0.id == app.id }) {
            apps[index] = app
            saveApps()
        }
    }

    func addRule(to app: AppInfo, pattern: String) {
        guard var updatedApp = apps.first(where: { $0.id == app.id }) else { return }

        let newRule = PathRule(pattern: pattern)
        updatedApp.rules.append(newRule)
        updateApp(updatedApp)
    }

    func removeRule(from app: AppInfo, rule: PathRule) {
        guard var updatedApp = apps.first(where: { $0.id == app.id }) else { return }

        updatedApp.rules.removeAll { $0.id == rule.id }
        updateApp(updatedApp)
    }

    func toggleRule(in app: AppInfo, rule: PathRule) {
        guard var updatedApp = apps.first(where: { $0.id == app.id }) else { return }

        if let ruleIndex = updatedApp.rules.firstIndex(where: { $0.id == rule.id }) {
            updatedApp.rules[ruleIndex].isEnabled.toggle()
            updateApp(updatedApp)
        }
    }

    func findMatchingApp(for path: String) -> AppInfo? {
        for app in apps {
            for rule in app.rules where rule.isEnabled {
                if rule.matches(path) {
                    return app
                }
            }
        }
        return nil
    }

    func moveApp(from source: IndexSet, to destination: Int) {
        apps.move(fromOffsets: source, toOffset: destination)
        saveApps()
    }

    private func saveApps() {
        do {
            let data = try JSONEncoder().encode(apps)
            UserDefaults.standard.set(data, forKey: userDefaultsKey)
        } catch {
            print("Failed to save apps: \(error)")
        }
    }

    private func loadApps() {
        guard let data = UserDefaults.standard.data(forKey: userDefaultsKey) else {
            apps = []
            return
        }

        do {
            apps = try JSONDecoder().decode([AppInfo].self, from: data)
        } catch {
            print("Failed to load apps: \(error)")
            apps = []
        }
    }
}
