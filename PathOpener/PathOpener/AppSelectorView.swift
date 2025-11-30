import SwiftUI
import AppKit

struct AppSelectorView: View {
    let path: String
    let onAppSelected: (AppInfo) -> Void

    @StateObject private var appManager = AppManager.shared
    @EnvironmentObject var appState: AppState
    @State private var searchText: String = ""

    var filteredApps: [AppInfo] {
        if searchText.isEmpty {
            return appManager.apps
        } else {
            return appManager.apps.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
    }

    var body: some View {
        VStack(spacing: 0) {
            // Header
            VStack(alignment: .leading, spacing: 8) {
                Text("Select Application")
                    .font(.title2)
                    .fontWeight(.semibold)

                HStack {
                    Image(systemName: "doc")
                        .foregroundColor(.secondary)
                    Text(path)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                        .truncationMode(.middle)
                }

                Text("No rule matches this path. Choose an application to open it.")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)

            Divider()

            // Search bar
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundColor(.secondary)
                TextField("Search applications...", text: $searchText)
                    .textFieldStyle(.plain)

                if !searchText.isEmpty {
                    Button(action: { searchText = "" }) {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundColor(.secondary)
                    }
                    .buttonStyle(.borderless)
                }
            }
            .padding(8)
            .background(Color(NSColor.controlBackgroundColor))

            Divider()

            // App list
            if filteredApps.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "app.dashed")
                        .font(.system(size: 48))
                        .foregroundColor(.secondary)

                    if appManager.apps.isEmpty {
                        Text("No applications configured")
                            .font(.headline)
                        Text("Go to Settings to add applications")
                            .font(.caption)
                            .foregroundColor(.secondary)

                        Button("Open Settings") {
                            appState.currentView = .settings
                        }
                        .buttonStyle(.borderedProminent)
                    } else {
                        Text("No applications match '\(searchText)'")
                            .font(.headline)
                        Text("Try a different search term")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 0) {
                        ForEach(filteredApps) { app in
                            AppSelectionRow(app: app) {
                                onAppSelected(app)
                            }
                            .padding(.horizontal)
                            .padding(.vertical, 4)

                            if app.id != filteredApps.last?.id {
                                Divider()
                                    .padding(.horizontal)
                            }
                        }
                    }
                    .padding(.vertical, 8)
                }
            }

            Divider()

            // Footer
            HStack {
                Button("Cancel") {
                    appState.currentView = .main
                }

                Spacer()

                Text("\(filteredApps.count) application\(filteredApps.count == 1 ? "" : "s")")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            .padding()
        }
    }
}

struct AppSelectionRow: View {
    let app: AppInfo
    let onSelect: () -> Void

    @State private var isHovered = false

    var body: some View {
        Button(action: onSelect) {
            HStack(spacing: 12) {
                if let icon = app.icon {
                    Image(nsImage: icon)
                        .resizable()
                        .frame(width: 48, height: 48)
                } else {
                    Image(systemName: "app")
                        .font(.system(size: 32))
                        .frame(width: 48, height: 48)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text(app.name)
                        .font(.body)
                        .fontWeight(.medium)

                    Text(app.path)
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                        .truncationMode(.middle)

                    if !app.rules.isEmpty {
                        HStack(spacing: 4) {
                            Image(systemName: "list.bullet")
                                .font(.caption)
                            Text("\(app.rules.count) rule\(app.rules.count == 1 ? "" : "s")")
                                .font(.caption)
                        }
                        .foregroundColor(.blue)
                    }
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .foregroundColor(.secondary)
                    .opacity(isHovered ? 1 : 0)
            }
            .padding(8)
            .background(isHovered ? Color.blue.opacity(0.1) : Color.clear)
            .cornerRadius(8)
        }
        .buttonStyle(.plain)
        .onHover { hovering in
            isHovered = hovering
        }
    }
}

#Preview {
    AppSelectorView(path: "/Users/test/Documents/example.pdf") { app in
        print("Selected: \(app.name)")
    }
    .environmentObject(AppState())
    .frame(width: 500, height: 400)
}
