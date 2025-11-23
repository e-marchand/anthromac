#pragma once

#include <string>
#include <map>
#include <vector>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <algorithm>
#include <cctype>
#include <cstdlib>

namespace config {

// Exception type
class ConfigError : public std::runtime_error {
public:
    explicit ConfigError(const std::string& msg) : std::runtime_error(msg) {}
};

// Configuration format
enum class Format {
    INI,
    TOML,
    YAML,
    Auto
};

// Configuration class
class Config {
public:
    Config() = default;

    // Get value with type conversion
    template<typename T>
    T get(const std::string& key) const {
        if (!has(key)) {
            throw ConfigError("Key not found: " + key);
        }
        return convert<T>(data_.at(key));
    }

    template<typename T>
    T get(const std::string& key, const T& default_value) const {
        if (!has(key)) {
            return default_value;
        }
        try {
            return convert<T>(data_.at(key));
        } catch (...) {
            return default_value;
        }
    }

    bool has(const std::string& key) const {
        return data_.find(key) != data_.end();
    }

    // Set value
    template<typename T>
    void set(const std::string& key, const T& value) {
        if constexpr (std::is_same_v<T, std::string>) {
            data_[key] = value;
        } else if constexpr (std::is_same_v<T, bool>) {
            data_[key] = value ? "true" : "false";
        } else {
            data_[key] = std::to_string(value);
        }
    }

    void remove(const std::string& key) {
        data_.erase(key);
    }

    // Section access
    Config section(const std::string& prefix) const {
        Config result;
        std::string search = prefix + ".";

        for (const auto& [key, value] : data_) {
            if (key.find(search) == 0) {
                std::string local_key = key.substr(search.size());
                result.data_[local_key] = value;
            }
        }

        return result;
    }

    std::vector<std::string> sections() const {
        std::vector<std::string> result;

        for (const auto& [key, value] : data_) {
            size_t dot_pos = key.find('.');
            if (dot_pos != std::string::npos) {
                std::string section = key.substr(0, dot_pos);
                if (std::find(result.begin(), result.end(), section) == result.end()) {
                    result.push_back(section);
                }
            }
        }

        return result;
    }

    const std::map<std::string, std::string>& all() const {
        return data_;
    }

    void expand_env_vars() {
        for (auto& [key, value] : data_) {
            value = expand_env(value);
        }
    }

private:
    friend class ConfigParser;
    std::map<std::string, std::string> data_;

    template<typename T>
    T convert(const std::string& value) const {
        if constexpr (std::is_same_v<T, std::string>) {
            return value;
        } else if constexpr (std::is_same_v<T, int>) {
            return std::stoi(value);
        } else if constexpr (std::is_same_v<T, long>) {
            return std::stol(value);
        } else if constexpr (std::is_same_v<T, long long>) {
            return std::stoll(value);
        } else if constexpr (std::is_same_v<T, float>) {
            return std::stof(value);
        } else if constexpr (std::is_same_v<T, double>) {
            return std::stod(value);
        } else if constexpr (std::is_same_v<T, bool>) {
            std::string lower = value;
            std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
            return lower == "true" || lower == "1" || lower == "yes" || lower == "on";
        } else {
            static_assert(sizeof(T) == 0, "Unsupported type for config conversion");
        }
    }

    std::string expand_env(const std::string& value) const {
        std::string result = value;
        size_t pos = 0;

        while ((pos = result.find('$', pos)) != std::string::npos) {
            size_t start = pos;
            size_t end = pos + 1;

            // Check for ${VAR} or $VAR
            bool braced = (end < result.size() && result[end] == '{');
            if (braced) {
                end++;
                while (end < result.size() && result[end] != '}') {
                    end++;
                }
                if (end >= result.size()) break;
            } else {
                while (end < result.size() &&
                       (std::isalnum(result[end]) || result[end] == '_')) {
                    end++;
                }
            }

            size_t var_start = braced ? start + 2 : start + 1;
            size_t var_len = braced ? end - var_start : end - var_start;
            std::string var_name = result.substr(var_start, var_len);

            const char* env_value = std::getenv(var_name.c_str());
            std::string replacement = env_value ? env_value : "";

            size_t replace_len = braced ? end - start + 1 : end - start;
            result.replace(start, replace_len, replacement);

            pos = start + replacement.size();
        }

        return result;
    }
};

// INI parser
class INIParser {
public:
    static Config parse(const std::string& content) {
        Config cfg;
        std::istringstream stream(content);
        std::string line;
        std::string current_section;

        while (std::getline(stream, line)) {
            line = trim(remove_comment(line));
            if (line.empty()) continue;

            // Section header
            if (line.front() == '[' && line.back() == ']') {
                current_section = line.substr(1, line.size() - 2);
                continue;
            }

            // Key-value pair
            size_t eq_pos = line.find('=');
            if (eq_pos != std::string::npos) {
                std::string key = trim(line.substr(0, eq_pos));
                std::string value = trim(line.substr(eq_pos + 1));

                // Remove quotes from value
                if (value.size() >= 2 &&
                    ((value.front() == '"' && value.back() == '"') ||
                     (value.front() == '\'' && value.back() == '\''))) {
                    value = value.substr(1, value.size() - 2);
                }

                std::string full_key = current_section.empty() ? key : current_section + "." + key;
                cfg.data_[full_key] = value;
            }
        }

        return cfg;
    }

    static std::string generate(const Config& cfg) {
        std::ostringstream ss;
        std::map<std::string, std::vector<std::pair<std::string, std::string>>> sections;

        // Group by section
        for (const auto& [key, value] : cfg.all()) {
            size_t dot_pos = key.find('.');
            if (dot_pos != std::string::npos) {
                std::string section = key.substr(0, dot_pos);
                std::string local_key = key.substr(dot_pos + 1);
                sections[section].emplace_back(local_key, value);
            } else {
                sections[""].emplace_back(key, value);
            }
        }

        // Write global section first
        if (sections.count("")) {
            for (const auto& [key, value] : sections[""]) {
                ss << key << " = " << value << "\n";
            }
            ss << "\n";
        }

        // Write other sections
        for (const auto& [section, pairs] : sections) {
            if (section.empty()) continue;

            ss << "[" << section << "]\n";
            for (const auto& [key, value] : pairs) {
                ss << key << " = " << value << "\n";
            }
            ss << "\n";
        }

        return ss.str();
    }

private:
    static std::string trim(const std::string& str) {
        auto start = str.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) return "";
        auto end = str.find_last_not_of(" \t\r\n");
        return str.substr(start, end - start + 1);
    }

    static std::string remove_comment(const std::string& line) {
        size_t pos = line.find('#');
        if (pos == std::string::npos) {
            pos = line.find(';');
        }
        if (pos != std::string::npos) {
            return line.substr(0, pos);
        }
        return line;
    }
};

// TOML parser (simplified subset)
class TOMLParser {
public:
    static Config parse(const std::string& content) {
        Config cfg;
        std::istringstream stream(content);
        std::string line;
        std::string current_section;

        while (std::getline(stream, line)) {
            line = trim(remove_comment(line));
            if (line.empty()) continue;

            // Table header
            if (line.front() == '[' && line.back() == ']') {
                current_section = line.substr(1, line.size() - 2);
                continue;
            }

            // Key-value pair
            size_t eq_pos = line.find('=');
            if (eq_pos != std::string::npos) {
                std::string key = trim(line.substr(0, eq_pos));
                std::string value = trim(line.substr(eq_pos + 1));

                // Remove quotes
                if (value.size() >= 2 && value.front() == '"' && value.back() == '"') {
                    value = value.substr(1, value.size() - 2);
                }

                std::string full_key = current_section.empty() ? key : current_section + "." + key;
                cfg.data_[full_key] = value;
            }
        }

        return cfg;
    }

    static std::string generate(const Config& cfg) {
        std::ostringstream ss;
        std::map<std::string, std::vector<std::pair<std::string, std::string>>> sections;

        // Group by section
        for (const auto& [key, value] : cfg.all()) {
            size_t dot_pos = key.find('.');
            if (dot_pos != std::string::npos) {
                std::string section = key.substr(0, dot_pos);
                std::string local_key = key.substr(dot_pos + 1);
                sections[section].emplace_back(local_key, value);
            } else {
                sections[""].emplace_back(key, value);
            }
        }

        // Write sections
        for (const auto& [section, pairs] : sections) {
            if (!section.empty()) {
                ss << "[" << section << "]\n";
            }
            for (const auto& [key, value] : pairs) {
                ss << key << " = ";
                // Quote strings that aren't numbers or booleans
                if (value == "true" || value == "false" ||
                    (!value.empty() && (std::isdigit(value[0]) || value[0] == '-'))) {
                    ss << value;
                } else {
                    ss << "\"" << value << "\"";
                }
                ss << "\n";
            }
            ss << "\n";
        }

        return ss.str();
    }

private:
    static std::string trim(const std::string& str) {
        auto start = str.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) return "";
        auto end = str.find_last_not_of(" \t\r\n");
        return str.substr(start, end - start + 1);
    }

    static std::string remove_comment(const std::string& line) {
        size_t pos = line.find('#');
        if (pos != std::string::npos) {
            return line.substr(0, pos);
        }
        return line;
    }
};

// YAML parser (simplified subset)
class YAMLParser {
public:
    static Config parse(const std::string& content) {
        Config cfg;
        std::istringstream stream(content);
        std::string line;
        std::vector<std::pair<int, std::string>> section_stack;

        while (std::getline(stream, line)) {
            if (line.empty() || line.find_first_not_of(" \t") == std::string::npos) {
                continue;
            }

            // Skip comments
            size_t comment_pos = line.find('#');
            if (comment_pos != std::string::npos) {
                line = line.substr(0, comment_pos);
            }

            // Get indentation level
            size_t indent = 0;
            while (indent < line.size() && line[indent] == ' ') {
                indent++;
            }

            std::string trimmed = trim(line);
            if (trimmed.empty()) continue;

            // Parse key-value
            size_t colon_pos = trimmed.find(':');
            if (colon_pos != std::string::npos) {
                std::string key = trim(trimmed.substr(0, colon_pos));
                std::string value = trim(trimmed.substr(colon_pos + 1));

                // Pop sections with greater or equal indentation
                while (!section_stack.empty() && section_stack.back().first >= static_cast<int>(indent)) {
                    section_stack.pop_back();
                }

                // Build full key
                std::string full_key = key;
                for (const auto& [ind, sec] : section_stack) {
                    full_key = sec + "." + full_key;
                }

                if (value.empty()) {
                    // This is a section
                    section_stack.emplace_back(indent, key);
                } else {
                    // This is a key-value pair
                    cfg.data_[full_key] = value;
                }
            }
        }

        return cfg;
    }

    static std::string generate(const Config& cfg) {
        std::ostringstream ss;
        std::map<std::string, std::map<std::string, std::string>> tree;

        // Build tree structure
        for (const auto& [key, value] : cfg.all()) {
            std::vector<std::string> parts = split(key, '.');
            if (parts.size() == 1) {
                tree[""][key] = value;
            } else {
                std::string section = parts[0];
                std::string local_key = key.substr(section.size() + 1);
                tree[section][local_key] = value;
            }
        }

        // Write YAML
        int indent = 0;
        write_yaml_tree(ss, tree, "", indent);

        return ss.str();
    }

private:
    static std::string trim(const std::string& str) {
        auto start = str.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) return "";
        auto end = str.find_last_not_of(" \t\r\n");
        return str.substr(start, end - start + 1);
    }

    static std::vector<std::string> split(const std::string& str, char delim) {
        std::vector<std::string> result;
        std::istringstream stream(str);
        std::string item;
        while (std::getline(stream, item, delim)) {
            result.push_back(item);
        }
        return result;
    }

    static void write_yaml_tree(std::ostringstream& ss,
                                const std::map<std::string, std::map<std::string, std::string>>& tree,
                                const std::string& prefix,
                                int indent) {
        for (const auto& [section, values] : tree) {
            if (section.empty()) {
                for (const auto& [key, value] : values) {
                    ss << std::string(indent, ' ') << key << ": " << value << "\n";
                }
            } else {
                ss << std::string(indent, ' ') << section << ":\n";
                for (const auto& [key, value] : values) {
                    size_t dot_pos = key.find('.');
                    if (dot_pos == std::string::npos) {
                        ss << std::string(indent + 2, ' ') << key << ": " << value << "\n";
                    }
                }
            }
        }
    }
};

// Main ConfigParser class
class ConfigParser {
public:
    static Config parse_file(const std::string& filename, Format format = Format::Auto) {
        std::ifstream file(filename);
        if (!file.is_open()) {
            throw ConfigError("Cannot open file: " + filename);
        }

        std::string content((std::istreambuf_iterator<char>(file)),
                           std::istreambuf_iterator<char>());

        if (format == Format::Auto) {
            format = detect_format(filename);
        }

        return parse_string(content, format);
    }

    static Config parse_ini(const std::string& filename) {
        return parse_file(filename, Format::INI);
    }

    static Config parse_toml(const std::string& filename) {
        return parse_file(filename, Format::TOML);
    }

    static Config parse_yaml(const std::string& filename) {
        return parse_file(filename, Format::YAML);
    }

    static Config parse_string(const std::string& content, Format format) {
        switch (format) {
            case Format::INI:
                return INIParser::parse(content);
            case Format::TOML:
                return TOMLParser::parse(content);
            case Format::YAML:
                return YAMLParser::parse(content);
            default:
                throw ConfigError("Unknown format");
        }
    }

    static void write_file(const Config& cfg, const std::string& filename, Format format) {
        std::ofstream file(filename);
        if (!file.is_open()) {
            throw ConfigError("Cannot create file: " + filename);
        }

        file << to_string(cfg, format);
    }

    static std::string to_string(const Config& cfg, Format format) {
        switch (format) {
            case Format::INI:
                return INIParser::generate(cfg);
            case Format::TOML:
                return TOMLParser::generate(cfg);
            case Format::YAML:
                return YAMLParser::generate(cfg);
            default:
                throw ConfigError("Unknown format");
        }
    }

private:
    static Format detect_format(const std::string& filename) {
        if (filename.ends_with(".ini")) return Format::INI;
        if (filename.ends_with(".toml")) return Format::TOML;
        if (filename.ends_with(".yaml") || filename.ends_with(".yml")) return Format::YAML;
        return Format::INI;  // Default
    }
};

} // namespace config
