import SwiftUI
import AppKit

struct SettingsView: View {
    @StateObject private var appManager = AppManager.shared
    @State private var selectedApp: AppInfo?
    @State private var newRulePattern: String = ""
    @State private var showingFilePicker = false

    var body: some View {
        HSplitView {
            // Left side: App list
            VStack(alignment: .leading, spacing: 0) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Applications")
                        .font(.headline)
                    Text("Drag to reorder • First match wins")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding()

                List(selection: $selectedApp) {
                    ForEach(appManager.apps) { app in
                        AppRow(app: app)
                            .tag(app)
                            .contextMenu {
                                Button("Remove") {
                                    appManager.removeApp(app)
                                    if selectedApp?.id == app.id {
                                        selectedApp = nil
                                    }
                                }
                            }
                    }
                    .onMove { source, destination in
                        appManager.moveApp(from: source, to: destination)
                    }
                }
                .listStyle(.sidebar)

                HStack {
                    Button(action: addApplication) {
                        Image(systemName: "plus")
                    }
                    .buttonStyle(.borderless)
                    .help("Add application or script")

                    Spacer()
                }
                .padding(8)
            }
            .frame(minWidth: 250)

            // Right side: Rules editor
            if let app = selectedApp {
                RulesEditor(app: binding(for: app))
            } else {
                VStack {
                    Text("Select an application to configure rules")
                        .foregroundColor(.secondary)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }

    private func binding(for app: AppInfo) -> Binding<AppInfo> {
        Binding(
            get: { appManager.apps.first(where: { $0.id == app.id }) ?? app },
            set: { appManager.updateApp($0) }
        )
    }

    private func addApplication() {
        let panel = NSOpenPanel()
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        panel.canChooseFiles = true
        panel.allowedContentTypes = [.application, .executable, .shellScript]
        panel.message = "Select an application or script"

        panel.begin { response in
            guard response == .OK, let url = panel.url else { return }

            let path = url.path
            if path.hasSuffix(".app") {
                appManager.addApp(at: path)
            } else {
                // It's a script - ask for a name
                let alert = NSAlert()
                alert.messageText = "Script Name"
                alert.informativeText = "Enter a name for this script:"
                alert.alertStyle = .informational
                alert.addButton(withTitle: "OK")
                alert.addButton(withTitle: "Cancel")

                let inputField = NSTextField(frame: NSRect(x: 0, y: 0, width: 200, height: 24))
                inputField.stringValue = url.lastPathComponent
                alert.accessoryView = inputField

                let response = alert.runModal()
                if response == .alertFirstButtonReturn {
                    let name = inputField.stringValue.isEmpty ? url.lastPathComponent : inputField.stringValue
                    appManager.addScript(at: path, name: name)
                }
            }
        }
    }
}

struct AppRow: View {
    let app: AppInfo

    var body: some View {
        HStack(spacing: 12) {
            if let icon = app.icon {
                Image(nsImage: icon)
                    .resizable()
                    .frame(width: 32, height: 32)
            } else {
                Image(systemName: "app")
                    .font(.title2)
                    .frame(width: 32, height: 32)
            }

            Text(app.name)
                .font(.body)
        }
        .padding(.vertical, 4)
    }
}

struct RulesEditor: View {
    @Binding var app: AppInfo
    @StateObject private var appManager = AppManager.shared
    @State private var newRulePattern: String = ""

    var body: some View {
        ScrollView(.vertical, showsIndicators: true) {
            VStack(alignment: .leading, spacing: 0) {
                // Header
            HStack {
                if let icon = app.icon {
                    Image(nsImage: icon)
                        .resizable()
                        .frame(width: 48, height: 48)
                }

                VStack(alignment: .leading) {
                    Text(app.name)
                        .font(.title2)
                        .fontWeight(.semibold)
                    Text(app.path)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Spacer()
            }
            .padding()

            Divider()

            // Command Line Arguments section
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Command Line Arguments")
                        .font(.headline)

                    Spacer()

                    Text("Optional arguments to pass when launching")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Text("Use {FOLDER} or {FILE} as placeholders for the target path")
                    .font(.caption)
                    .foregroundColor(.secondary)

                TextField("e.g., --new-window {FILE}", text: Binding(
                    get: { app.commandLineArgs ?? "" },
                    set: { newValue in
                        var updatedApp = app
                        updatedApp.commandLineArgs = newValue.isEmpty ? nil : newValue
                        appManager.updateApp(updatedApp)
                    }
                ))
                .textFieldStyle(.roundedBorder)
            }
            .padding()

            Divider()

            // Rules section
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Path Rules")
                        .font(.headline)

                    Spacer()

                    Text("Glob patterns to match paths")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }

                Text("Examples: **/*.js, /Users/*/Documents/**, *.pdf")
                    .font(.caption)
                    .foregroundColor(.secondary)

                // Rule list
                if app.rules.isEmpty {
                    Text("No rules defined. Add a glob pattern to automatically open matching paths.")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding()
                } else {
                    VStack(spacing: 4) {
                        ForEach(app.rules) { rule in
                            RuleRow(
                                app: app,
                                rule: rule,
                                onToggle: {
                                    appManager.toggleRule(in: app, rule: rule)
                                },
                                onDelete: {
                                    appManager.removeRule(from: app, rule: rule)
                                }
                            )
                            Divider()
                        }
                    }
                    .padding(.vertical, 4)
                }

                // Add rule input
                HStack {
                    TextField("Enter glob pattern (e.g., **/*.js)", text: $newRulePattern)
                        .textFieldStyle(.roundedBorder)
                        .onSubmit(addRule)

                    Button("Add Rule") {
                        addRule()
                    }
                    .disabled(newRulePattern.isEmpty)
                }
            }
            .padding()
            }
            .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func addRule() {
        guard !newRulePattern.isEmpty else { return }

        appManager.addRule(to: app, pattern: newRulePattern)
        newRulePattern = ""
    }
}

struct RuleRow: View {
    let app: AppInfo
    let rule: PathRule
    let onToggle: () -> Void
    let onDelete: () -> Void

    var body: some View {
        HStack {
            Toggle("", isOn: Binding(
                get: { rule.isEnabled },
                set: { _ in onToggle() }
            ))
            .toggleStyle(.checkbox)

            Text(rule.pattern)
                .font(.body)
                .foregroundColor(rule.isEnabled ? .primary : .secondary)

            Spacer()

            Button(action: onDelete) {
                Image(systemName: "trash")
                    .foregroundColor(.red)
            }
            .buttonStyle(.borderless)
            .help("Delete rule")
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    SettingsView()
        .frame(width: 800, height: 600)
}
