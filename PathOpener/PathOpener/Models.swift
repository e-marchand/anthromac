import Foundation
import AppKit

struct AppInfo: Identifiable, Codable, Equatable, Hashable {
    let id: UUID
    var name: String
    var path: String
    var iconData: Data?
    var rules: [PathRule]

    init(id: UUID = UUID(), name: String, path: String, iconData: Data? = nil, rules: [PathRule] = []) {
        self.id = id
        self.name = name
        self.path = path
        self.iconData = iconData
        self.rules = rules
    }

    var icon: NSImage? {
        if let data = iconData {
            return NSImage(data: data)
        }
        return NSWorkspace.shared.icon(forFile: path)
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: AppInfo, rhs: AppInfo) -> Bool {
        lhs.id == rhs.id
    }
}

struct PathRule: Identifiable, Codable, Equatable, Hashable {
    let id: UUID
    var pattern: String
    var isEnabled: Bool

    init(id: UUID = UUID(), pattern: String, isEnabled: Bool = true) {
        self.id = id
        self.pattern = pattern
        self.isEnabled = isEnabled
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: PathRule, rhs: PathRule) -> Bool {
        lhs.id == rhs.id
    }

    func matches(_ path: String) -> Bool {
        guard isEnabled else { return false }

        // Convert glob pattern to regex
        let regexPattern = globToRegex(pattern)

        do {
            let regex = try NSRegularExpression(pattern: regexPattern, options: [])
            let range = NSRange(path.startIndex..<path.endIndex, in: path)
            return regex.firstMatch(in: path, options: [], range: range) != nil
        } catch {
            print("Invalid regex pattern: \(error)")
            return false
        }
    }

    private func globToRegex(_ glob: String) -> String {
        var regex = "^"
        var i = glob.startIndex

        while i < glob.endIndex {
            let char = glob[i]

            switch char {
            case "*":
                if i < glob.index(before: glob.endIndex) && glob[glob.index(after: i)] == "*" {
                    // ** matches any number of directories
                    regex += ".*"
                    i = glob.index(after: i)
                } else {
                    // * matches anything except /
                    regex += "[^/]*"
                }
            case "?":
                regex += "[^/]"
            case ".":
                regex += "\\."
            case "[", "]", "(", ")", "{", "}", "+", "^", "$", "|", "\\":
                regex += "\\\(char)"
            default:
                regex += String(char)
            }

            i = glob.index(after: i)
        }

        regex += "$"
        return regex
    }
}
