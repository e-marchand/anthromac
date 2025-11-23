#pragma once

#include <string>
#include <map>
#include <vector>
#include <functional>
#include <sstream>
#include <fstream>
#include <stdexcept>
#include <algorithm>
#include <regex>

namespace tmpl {

// Exception type
class TemplateError : public std::runtime_error {
public:
    explicit TemplateError(const std::string& msg) : std::runtime_error(msg) {}
};

// Forward declaration
class Context;

// Filter function type
using FilterFunction = std::function<std::string(const std::string&)>;

// Context for template variables
class Context {
public:
    void set(const std::string& key, const std::string& value) {
        data_[key] = value;
    }

    void set(const std::string& key, int value) {
        data_[key] = std::to_string(value);
    }

    void set(const std::string& key, double value) {
        data_[key] = std::to_string(value);
    }

    void set(const std::string& key, bool value) {
        data_[key] = value ? "true" : "false";
    }

    void set_array(const std::string& key, const std::vector<Context>& items) {
        arrays_[key] = items;
    }

    void set_context(const std::string& key, const Context& ctx) {
        for (const auto& [k, v] : ctx.data_) {
            data_[key + "." + k] = v;
        }
    }

    std::string get(const std::string& key, const std::string& default_val = "") const {
        auto it = data_.find(key);
        return (it != data_.end()) ? it->second : default_val;
    }

    bool has(const std::string& key) const {
        return data_.find(key) != data_.end();
    }

    bool has_array(const std::string& key) const {
        return arrays_.find(key) != arrays_.end();
    }

    const std::vector<Context>& get_array(const std::string& key) const {
        static std::vector<Context> empty;
        auto it = arrays_.find(key);
        return (it != arrays_.end()) ? it->second : empty;
    }

    bool is_truthy(const std::string& key) const {
        if (!has(key)) return false;
        std::string value = get(key);
        return !value.empty() && value != "false" && value != "0";
    }

private:
    std::map<std::string, std::string> data_;
    std::map<std::string, std::vector<Context>> arrays_;
};

// Template Engine
class TemplateEngine {
public:
    TemplateEngine() {
        register_builtin_filters();
    }

    std::string render(const std::string& template_str, const Context& ctx) {
        return render_impl(template_str, ctx);
    }

    std::string render_file(const std::string& filename, const Context& ctx) {
        std::ifstream file(template_dir_ + filename);
        if (!file.is_open()) {
            throw TemplateError("Cannot open template file: " + filename);
        }

        std::string content((std::istreambuf_iterator<char>(file)),
                           std::istreambuf_iterator<char>());

        return render(content, ctx);
    }

    void register_filter(const std::string& name, FilterFunction func) {
        filters_[name] = func;
    }

    void set_template_dir(const std::string& dir) {
        template_dir_ = dir;
        if (!template_dir_.empty() && template_dir_.back() != '/') {
            template_dir_ += '/';
        }
    }

private:
    std::map<std::string, FilterFunction> filters_;
    std::string template_dir_;

    void register_builtin_filters() {
        // Upper case
        register_filter("upper", [](const std::string& value) {
            std::string result = value;
            std::transform(result.begin(), result.end(), result.begin(), ::toupper);
            return result;
        });

        // Lower case
        register_filter("lower", [](const std::string& value) {
            std::string result = value;
            std::transform(result.begin(), result.end(), result.begin(), ::tolower);
            return result;
        });

        // Capitalize
        register_filter("capitalize", [](const std::string& value) {
            if (value.empty()) return value;
            std::string result = value;
            result[0] = std::toupper(result[0]);
            return result;
        });

        // Title case
        register_filter("title", [](const std::string& value) {
            std::string result;
            bool new_word = true;
            for (char c : value) {
                if (std::isspace(c)) {
                    new_word = true;
                    result += c;
                } else if (new_word) {
                    result += std::toupper(c);
                    new_word = false;
                } else {
                    result += std::tolower(c);
                }
            }
            return result;
        });

        // Trim
        register_filter("trim", [](const std::string& value) {
            auto start = value.find_first_not_of(" \t\r\n");
            if (start == std::string::npos) return std::string("");
            auto end = value.find_last_not_of(" \t\r\n");
            return value.substr(start, end - start + 1);
        });

        // Length
        register_filter("length", [](const std::string& value) {
            return std::to_string(value.length());
        });
    }

    std::string render_impl(const std::string& template_str, const Context& ctx) {
        std::string result = template_str;

        // Remove comments {# ... #}
        result = remove_comments(result);

        // Process control structures
        result = process_for_loops(result, ctx);
        result = process_conditionals(result, ctx);

        // Process variables {{ ... }}
        result = process_variables(result, ctx);

        return result;
    }

    std::string remove_comments(const std::string& str) {
        std::string result;
        size_t pos = 0;

        while (pos < str.size()) {
            size_t comment_start = str.find("{#", pos);
            if (comment_start == std::string::npos) {
                result += str.substr(pos);
                break;
            }

            result += str.substr(pos, comment_start - pos);

            size_t comment_end = str.find("#}", comment_start + 2);
            if (comment_end == std::string::npos) {
                throw TemplateError("Unclosed comment");
            }

            pos = comment_end + 2;
        }

        return result;
    }

    std::string process_variables(const std::string& str, const Context& ctx) {
        std::string result;
        size_t pos = 0;

        while (pos < str.size()) {
            size_t var_start = str.find("{{", pos);
            if (var_start == std::string::npos) {
                result += str.substr(pos);
                break;
            }

            result += str.substr(pos, var_start - pos);

            size_t var_end = str.find("}}", var_start + 2);
            if (var_end == std::string::npos) {
                throw TemplateError("Unclosed variable");
            }

            std::string var_expr = str.substr(var_start + 2, var_end - var_start - 2);
            result += evaluate_variable(trim(var_expr), ctx);

            pos = var_end + 2;
        }

        return result;
    }

    std::string evaluate_variable(const std::string& expr, const Context& ctx) {
        // Check for filters: {{ var | filter }}
        size_t pipe_pos = expr.find('|');
        std::string var_name = pipe_pos != std::string::npos ?
                              trim(expr.substr(0, pipe_pos)) : expr;

        std::string value = html_escape(ctx.get(var_name, ""));

        // Apply filters
        if (pipe_pos != std::string::npos) {
            std::string filter_chain = expr.substr(pipe_pos + 1);
            value = apply_filters(value, trim(filter_chain));
        }

        return value;
    }

    std::string apply_filters(std::string value, const std::string& filter_chain) {
        std::istringstream stream(filter_chain);
        std::string filter_name;

        while (std::getline(stream, filter_name, '|')) {
            filter_name = trim(filter_name);
            if (filters_.count(filter_name)) {
                value = filters_[filter_name](value);
            }
        }

        return value;
    }

    std::string process_conditionals(const std::string& str, const Context& ctx) {
        std::string result = str;

        while (true) {
            size_t if_start = result.find("{% if ");
            if (if_start == std::string::npos) break;

            size_t condition_end = result.find("%}", if_start);
            if (condition_end == std::string::npos) {
                throw TemplateError("Malformed if statement");
            }

            std::string condition = result.substr(if_start + 6, condition_end - if_start - 6);
            condition = trim(condition);

            size_t endif_pos = find_matching_endif(result, if_start);
            if (endif_pos == std::string::npos) {
                throw TemplateError("Missing endif");
            }

            size_t else_pos = find_else(result, if_start, endif_pos);

            std::string if_content;
            std::string else_content;

            if (else_pos != std::string::npos) {
                if_content = result.substr(condition_end + 2, else_pos - condition_end - 2);
                size_t else_start = result.find("%}", else_pos) + 2;
                else_content = result.substr(else_start, endif_pos - else_start);
            } else {
                if_content = result.substr(condition_end + 2, endif_pos - condition_end - 2);
            }

            std::string replacement;
            if (ctx.is_truthy(condition)) {
                replacement = process_conditionals(if_content, ctx);
            } else {
                replacement = process_conditionals(else_content, ctx);
            }

            size_t endif_end = result.find("%}", endif_pos) + 2;
            result.replace(if_start, endif_end - if_start, replacement);
        }

        return result;
    }

    std::string process_for_loops(const std::string& str, const Context& ctx) {
        std::string result = str;

        while (true) {
            size_t for_start = result.find("{% for ");
            if (for_start == std::string::npos) break;

            size_t for_header_end = result.find("%}", for_start);
            if (for_header_end == std::string::npos) {
                throw TemplateError("Malformed for loop");
            }

            std::string for_expr = result.substr(for_start + 7, for_header_end - for_start - 7);
            for_expr = trim(for_expr);

            // Parse: item in items
            size_t in_pos = for_expr.find(" in ");
            if (in_pos == std::string::npos) {
                throw TemplateError("Invalid for loop syntax");
            }

            std::string item_var = trim(for_expr.substr(0, in_pos));
            std::string array_name = trim(for_expr.substr(in_pos + 4));

            size_t endfor_pos = find_matching_endfor(result, for_start);
            if (endfor_pos == std::string::npos) {
                throw TemplateError("Missing endfor");
            }

            std::string loop_content = result.substr(for_header_end + 2, endfor_pos - for_header_end - 2);

            std::string replacement;
            if (ctx.has_array(array_name)) {
                for (const auto& item_ctx : ctx.get_array(array_name)) {
                    Context loop_ctx = ctx;
                    for (const auto& [key, value] : item_ctx.all()) {
                        loop_ctx.set(item_var + "." + key, value);
                    }
                    replacement += render_impl(loop_content, loop_ctx);
                }
            }

            size_t endfor_end = result.find("%}", endfor_pos) + 2;
            result.replace(for_start, endfor_end - for_start, replacement);
        }

        return result;
    }

    size_t find_matching_endif(const std::string& str, size_t if_pos) {
        int depth = 1;
        size_t pos = if_pos + 1;

        while (pos < str.size() && depth > 0) {
            if (str.substr(pos, 6) == "{% if ") {
                depth++;
                pos += 6;
            } else if (str.substr(pos, 10) == "{% endif %}") {
                depth--;
                if (depth == 0) return pos;
                pos += 10;
            } else {
                pos++;
            }
        }

        return std::string::npos;
    }

    size_t find_else(const std::string& str, size_t if_pos, size_t endif_pos) {
        size_t pos = if_pos;
        int depth = 1;

        while (pos < endif_pos) {
            if (str.substr(pos, 6) == "{% if ") {
                depth++;
            } else if (str.substr(pos, 10) == "{% endif %}") {
                depth--;
            } else if (depth == 1 && str.substr(pos, 9) == "{% else %}") {
                return pos;
            }
            pos++;
        }

        return std::string::npos;
    }

    size_t find_matching_endfor(const std::string& str, size_t for_pos) {
        int depth = 1;
        size_t pos = for_pos + 1;

        while (pos < str.size() && depth > 0) {
            if (str.substr(pos, 7) == "{% for ") {
                depth++;
                pos += 7;
            } else if (str.substr(pos, 12) == "{% endfor %}") {
                depth--;
                if (depth == 0) return pos;
                pos += 12;
            } else {
                pos++;
            }
        }

        return std::string::npos;
    }

    std::string trim(const std::string& str) {
        auto start = str.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) return "";
        auto end = str.find_last_not_of(" \t\r\n");
        return str.substr(start, end - start + 1);
    }

    std::string html_escape(const std::string& str) {
        std::string result;
        for (char c : str) {
            switch (c) {
                case '&':  result += "&amp;"; break;
                case '<':  result += "&lt;"; break;
                case '>':  result += "&gt;"; break;
                case '"':  result += "&quot;"; break;
                case '\'': result += "&#39;"; break;
                default:   result += c; break;
            }
        }
        return result;
    }
};

} // namespace tmpl
