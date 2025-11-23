#pragma once

#include <string>
#include <string_view>
#include <vector>
#include <memory>
#include <sstream>
#include <algorithm>
#include <regex>
#include <cctype>

namespace md {

// Parser options
struct ParserOptions {
    bool github_flavored = false;
    bool pretty_print = false;
    bool escape_html = true;
    bool generate_toc = false;
    bool hard_line_breaks = false;
    bool autolink = true;
    int tab_width = 4;
    std::string code_class_prefix = "language-";
};

// HTML utility functions
class HTMLUtils {
public:
    static std::string escape(const std::string& text) {
        std::string result;
        result.reserve(text.size());

        for (char c : text) {
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

    static std::string unescape(const std::string& text) {
        std::string result = text;
        size_t pos = 0;

        while ((pos = result.find("&amp;", pos)) != std::string::npos) {
            result.replace(pos, 5, "&");
            pos += 1;
        }
        pos = 0;
        while ((pos = result.find("&lt;", pos)) != std::string::npos) {
            result.replace(pos, 4, "<");
            pos += 1;
        }
        pos = 0;
        while ((pos = result.find("&gt;", pos)) != std::string::npos) {
            result.replace(pos, 4, ">");
            pos += 1;
        }
        pos = 0;
        while ((pos = result.find("&quot;", pos)) != std::string::npos) {
            result.replace(pos, 6, "\"");
            pos += 1;
        }

        return result;
    }

    static std::string make_id(const std::string& text) {
        std::string id;
        for (char c : text) {
            if (std::isalnum(c)) {
                id += std::tolower(c);
            } else if (std::isspace(c)) {
                id += '-';
            }
        }
        return id;
    }
};

// AST Node types
enum class NodeType {
    Document,
    Header,
    Paragraph,
    List,
    ListItem,
    CodeBlock,
    Blockquote,
    HorizontalRule,
    Table,
    TableRow,
    TableCell,
    Text,
    Bold,
    Italic,
    Code,
    Link,
    Image,
    Strikethrough,
    LineBreak
};

// Base AST node
class Node {
public:
    NodeType type;
    std::vector<std::shared_ptr<Node>> children;
    std::string content;
    std::map<std::string, std::string> attributes;

    explicit Node(NodeType t) : type(t) {}
    virtual ~Node() = default;

    void add_child(std::shared_ptr<Node> child) {
        children.push_back(child);
    }
};

// Inline parser
class InlineParser {
public:
    InlineParser(const ParserOptions& opts) : options_(opts) {}

    std::vector<std::shared_ptr<Node>> parse(const std::string& text) {
        std::vector<std::shared_ptr<Node>> nodes;
        pos_ = 0;
        text_ = text;

        while (pos_ < text_.size()) {
            // Try to parse special inline elements
            if (auto node = try_parse_bold()) {
                nodes.push_back(node);
            } else if (auto node = try_parse_italic()) {
                nodes.push_back(node);
            } else if (auto node = try_parse_code()) {
                nodes.push_back(node);
            } else if (auto node = try_parse_image()) {
                nodes.push_back(node);
            } else if (auto node = try_parse_link()) {
                nodes.push_back(node);
            } else if (options_.github_flavored && (auto node = try_parse_strikethrough())) {
                nodes.push_back(node);
            } else if (options_.autolink && (auto node = try_parse_autolink())) {
                nodes.push_back(node);
            } else if (options_.hard_line_breaks && text_[pos_] == '\n') {
                nodes.push_back(std::make_shared<Node>(NodeType::LineBreak));
                pos_++;
            } else {
                // Regular text
                std::string content;
                while (pos_ < text_.size() && !is_special_char(text_[pos_])) {
                    content += text_[pos_++];
                }
                if (!content.empty()) {
                    auto text_node = std::make_shared<Node>(NodeType::Text);
                    text_node->content = content;
                    nodes.push_back(text_node);
                }
            }
        }

        return nodes;
    }

private:
    const ParserOptions& options_;
    std::string text_;
    size_t pos_ = 0;

    bool is_special_char(char c) const {
        return c == '*' || c == '_' || c == '`' || c == '[' || c == '!' || c == '~' || c == '\n';
    }

    std::shared_ptr<Node> try_parse_bold() {
        if (pos_ + 1 >= text_.size()) return nullptr;

        bool double_star = (text_[pos_] == '*' && text_[pos_ + 1] == '*');
        bool double_under = (text_[pos_] == '_' && text_[pos_ + 1] == '_');

        if (!double_star && !double_under) return nullptr;

        char delim = text_[pos_];
        size_t start = pos_ + 2;
        size_t end = start;

        while (end + 1 < text_.size()) {
            if (text_[end] == delim && text_[end + 1] == delim) {
                std::string content = text_.substr(start, end - start);
                pos_ = end + 2;

                auto node = std::make_shared<Node>(NodeType::Bold);
                InlineParser inner_parser(options_);
                node->children = inner_parser.parse(content);
                return node;
            }
            end++;
        }

        return nullptr;
    }

    std::shared_ptr<Node> try_parse_italic() {
        if (pos_ >= text_.size()) return nullptr;

        char delim = text_[pos_];
        if (delim != '*' && delim != '_') return nullptr;

        // Make sure it's not bold
        if (pos_ + 1 < text_.size() && text_[pos_ + 1] == delim) {
            return nullptr;
        }

        size_t start = pos_ + 1;
        size_t end = start;

        while (end < text_.size()) {
            if (text_[end] == delim) {
                std::string content = text_.substr(start, end - start);
                if (content.empty()) return nullptr;

                pos_ = end + 1;

                auto node = std::make_shared<Node>(NodeType::Italic);
                InlineParser inner_parser(options_);
                node->children = inner_parser.parse(content);
                return node;
            }
            end++;
        }

        return nullptr;
    }

    std::shared_ptr<Node> try_parse_code() {
        if (text_[pos_] != '`') return nullptr;

        size_t start = pos_ + 1;
        size_t end = start;

        while (end < text_.size() && text_[end] != '`') {
            end++;
        }

        if (end >= text_.size()) return nullptr;

        std::string content = text_.substr(start, end - start);
        pos_ = end + 1;

        auto node = std::make_shared<Node>(NodeType::Code);
        node->content = content;
        return node;
    }

    std::shared_ptr<Node> try_parse_image() {
        if (pos_ + 1 >= text_.size() || text_[pos_] != '!' || text_[pos_ + 1] != '[') {
            return nullptr;
        }

        size_t alt_start = pos_ + 2;
        size_t alt_end = text_.find(']', alt_start);
        if (alt_end == std::string::npos) return nullptr;

        if (alt_end + 1 >= text_.size() || text_[alt_end + 1] != '(') {
            return nullptr;
        }

        size_t url_start = alt_end + 2;
        size_t url_end = text_.find(')', url_start);
        if (url_end == std::string::npos) return nullptr;

        std::string alt = text_.substr(alt_start, alt_end - alt_start);
        std::string url_and_title = text_.substr(url_start, url_end - url_start);

        // Parse URL and optional title
        std::string url, title;
        size_t title_start = url_and_title.find('"');
        if (title_start != std::string::npos) {
            url = url_and_title.substr(0, title_start);
            // Trim whitespace
            url.erase(url.find_last_not_of(" \t") + 1);

            size_t title_end = url_and_title.find('"', title_start + 1);
            if (title_end != std::string::npos) {
                title = url_and_title.substr(title_start + 1, title_end - title_start - 1);
            }
        } else {
            url = url_and_title;
        }

        pos_ = url_end + 1;

        auto node = std::make_shared<Node>(NodeType::Image);
        node->attributes["src"] = url;
        node->attributes["alt"] = alt;
        if (!title.empty()) {
            node->attributes["title"] = title;
        }
        return node;
    }

    std::shared_ptr<Node> try_parse_link() {
        if (text_[pos_] != '[') return nullptr;

        size_t text_start = pos_ + 1;
        size_t text_end = text_.find(']', text_start);
        if (text_end == std::string::npos) return nullptr;

        if (text_end + 1 >= text_.size() || text_[text_end + 1] != '(') {
            return nullptr;
        }

        size_t url_start = text_end + 2;
        size_t url_end = text_.find(')', url_start);
        if (url_end == std::string::npos) return nullptr;

        std::string link_text = text_.substr(text_start, text_end - text_start);
        std::string url_and_title = text_.substr(url_start, url_end - url_start);

        // Parse URL and optional title
        std::string url, title;
        size_t title_start = url_and_title.find('"');
        if (title_start != std::string::npos) {
            url = url_and_title.substr(0, title_start);
            url.erase(url.find_last_not_of(" \t") + 1);

            size_t title_end = url_and_title.find('"', title_start + 1);
            if (title_end != std::string::npos) {
                title = url_and_title.substr(title_start + 1, title_end - title_start - 1);
            }
        } else {
            url = url_and_title;
        }

        pos_ = url_end + 1;

        auto node = std::make_shared<Node>(NodeType::Link);
        node->attributes["href"] = url;
        if (!title.empty()) {
            node->attributes["title"] = title;
        }
        InlineParser inner_parser(options_);
        node->children = inner_parser.parse(link_text);
        return node;
    }

    std::shared_ptr<Node> try_parse_strikethrough() {
        if (pos_ + 1 >= text_.size() || text_[pos_] != '~' || text_[pos_ + 1] != '~') {
            return nullptr;
        }

        size_t start = pos_ + 2;
        size_t end = start;

        while (end + 1 < text_.size()) {
            if (text_[end] == '~' && text_[end + 1] == '~') {
                std::string content = text_.substr(start, end - start);
                pos_ = end + 2;

                auto node = std::make_shared<Node>(NodeType::Strikethrough);
                InlineParser inner_parser(options_);
                node->children = inner_parser.parse(content);
                return node;
            }
            end++;
        }

        return nullptr;
    }

    std::shared_ptr<Node> try_parse_autolink() {
        // Simple URL detection
        if (pos_ + 7 >= text_.size()) return nullptr;

        std::string http = text_.substr(pos_, 7);
        std::string https = text_.substr(pos_, 8);

        bool is_http = (http == "http://");
        bool is_https = (https == "https:/");

        if (!is_http && !is_https) return nullptr;

        size_t url_start = pos_;
        size_t url_end = pos_;

        // Find end of URL (space, newline, or punctuation not in URL)
        while (url_end < text_.size() &&
               !std::isspace(text_[url_end]) &&
               text_[url_end] != '<' &&
               text_[url_end] != '>') {
            url_end++;
        }

        std::string url = text_.substr(url_start, url_end - url_start);
        pos_ = url_end;

        auto node = std::make_shared<Node>(NodeType::Link);
        node->attributes["href"] = url;
        auto text_node = std::make_shared<Node>(NodeType::Text);
        text_node->content = url;
        node->children.push_back(text_node);
        return node;
    }
};

// Block parser
class BlockParser {
public:
    BlockParser(const ParserOptions& opts) : options_(opts), inline_parser_(opts) {}

    std::shared_ptr<Node> parse(const std::string& markdown) {
        lines_ = split_lines(markdown);
        pos_ = 0;

        auto doc = std::make_shared<Node>(NodeType::Document);

        while (pos_ < lines_.size()) {
            if (auto node = try_parse_header()) {
                doc->add_child(node);
            } else if (auto node = try_parse_code_block()) {
                doc->add_child(node);
            } else if (auto node = try_parse_horizontal_rule()) {
                doc->add_child(node);
            } else if (auto node = try_parse_blockquote()) {
                doc->add_child(node);
            } else if (options_.github_flavored && (auto node = try_parse_table())) {
                doc->add_child(node);
            } else if (auto node = try_parse_list()) {
                doc->add_child(node);
            } else if (auto node = try_parse_paragraph()) {
                doc->add_child(node);
            } else {
                // Skip empty line
                pos_++;
            }
        }

        return doc;
    }

private:
    const ParserOptions& options_;
    InlineParser inline_parser_;
    std::vector<std::string> lines_;
    size_t pos_ = 0;

    std::vector<std::string> split_lines(const std::string& text) {
        std::vector<std::string> lines;
        std::istringstream stream(text);
        std::string line;
        while (std::getline(stream, line)) {
            lines.push_back(line);
        }
        return lines;
    }

    std::string trim(const std::string& str) {
        auto start = str.find_first_not_of(" \t");
        if (start == std::string::npos) return "";
        auto end = str.find_last_not_of(" \t");
        return str.substr(start, end - start + 1);
    }

    std::shared_ptr<Node> try_parse_header() {
        if (pos_ >= lines_.size()) return nullptr;

        const auto& line = lines_[pos_];
        if (line.empty() || line[0] != '#') return nullptr;

        size_t level = 0;
        while (level < line.size() && line[level] == '#') {
            level++;
        }

        if (level > 6 || level >= line.size() || line[level] != ' ') {
            return nullptr;
        }

        std::string content = trim(line.substr(level));
        pos_++;

        auto node = std::make_shared<Node>(NodeType::Header);
        node->attributes["level"] = std::to_string(level);
        node->attributes["id"] = HTMLUtils::make_id(content);
        node->children = inline_parser_.parse(content);

        return node;
    }

    std::shared_ptr<Node> try_parse_code_block() {
        if (pos_ >= lines_.size()) return nullptr;

        const auto& line = lines_[pos_];

        // Fenced code block
        if (line.size() >= 3 && line.substr(0, 3) == "```") {
            std::string language;
            if (line.size() > 3) {
                language = trim(line.substr(3));
            }

            pos_++;
            std::vector<std::string> code_lines;

            while (pos_ < lines_.size()) {
                if (lines_[pos_].find("```") == 0) {
                    pos_++;
                    break;
                }
                code_lines.push_back(lines_[pos_++]);
            }

            std::string code;
            for (size_t i = 0; i < code_lines.size(); ++i) {
                if (i > 0) code += '\n';
                code += code_lines[i];
            }

            auto node = std::make_shared<Node>(NodeType::CodeBlock);
            node->content = code;
            if (!language.empty()) {
                node->attributes["language"] = language;
            }
            return node;
        }

        // Indented code block
        if (line.size() >= 4 && line.substr(0, 4) == "    ") {
            std::vector<std::string> code_lines;

            while (pos_ < lines_.size()) {
                const auto& l = lines_[pos_];
                if (l.size() >= 4 && l.substr(0, 4) == "    ") {
                    code_lines.push_back(l.substr(4));
                    pos_++;
                } else if (trim(l).empty()) {
                    code_lines.push_back("");
                    pos_++;
                } else {
                    break;
                }
            }

            std::string code;
            for (size_t i = 0; i < code_lines.size(); ++i) {
                if (i > 0) code += '\n';
                code += code_lines[i];
            }

            auto node = std::make_shared<Node>(NodeType::CodeBlock);
            node->content = code;
            return node;
        }

        return nullptr;
    }

    std::shared_ptr<Node> try_parse_horizontal_rule() {
        if (pos_ >= lines_.size()) return nullptr;

        const auto& line = trim(lines_[pos_]);
        if (line.size() < 3) return nullptr;

        // Check for ---, ***, or ___
        char ch = line[0];
        if (ch != '-' && ch != '*' && ch != '_') return nullptr;

        int count = 0;
        for (char c : line) {
            if (c == ch) {
                count++;
            } else if (!std::isspace(c)) {
                return nullptr;
            }
        }

        if (count >= 3) {
            pos_++;
            return std::make_shared<Node>(NodeType::HorizontalRule);
        }

        return nullptr;
    }

    std::shared_ptr<Node> try_parse_blockquote() {
        if (pos_ >= lines_.size()) return nullptr;

        const auto& line = lines_[pos_];
        if (line.empty() || line[0] != '>') return nullptr;

        std::vector<std::string> quote_lines;

        while (pos_ < lines_.size()) {
            const auto& l = lines_[pos_];
            if (!l.empty() && l[0] == '>') {
                std::string content = l.substr(1);
                if (!content.empty() && content[0] == ' ') {
                    content = content.substr(1);
                }
                quote_lines.push_back(content);
                pos_++;
            } else if (trim(l).empty()) {
                quote_lines.push_back("");
                pos_++;
            } else {
                break;
            }
        }

        // Parse quoted content
        std::string quoted_text;
        for (size_t i = 0; i < quote_lines.size(); ++i) {
            if (i > 0) quoted_text += '\n';
            quoted_text += quote_lines[i];
        }

        BlockParser inner_parser(options_);
        auto inner_doc = inner_parser.parse(quoted_text);

        auto node = std::make_shared<Node>(NodeType::Blockquote);
        node->children = inner_doc->children;
        return node;
    }

    std::shared_ptr<Node> try_parse_list() {
        if (pos_ >= lines_.size()) return nullptr;

        const auto& line = trim(lines_[pos_]);
        if (line.empty()) return nullptr;

        bool is_ordered = !line.empty() && std::isdigit(line[0]);
        bool is_unordered = (line[0] == '-' || line[0] == '*' || line[0] == '+') &&
                           (line.size() > 1 && line[1] == ' ');

        if (!is_ordered && !is_unordered) return nullptr;

        auto list_node = std::make_shared<Node>(NodeType::List);
        list_node->attributes["ordered"] = is_ordered ? "true" : "false";

        while (pos_ < lines_.size()) {
            const auto& l = trim(lines_[pos_]);
            if (l.empty()) {
                pos_++;
                continue;
            }

            bool current_is_ordered = !l.empty() && std::isdigit(l[0]);
            bool current_is_unordered = (l[0] == '-' || l[0] == '*' || l[0] == '+') &&
                                       (l.size() > 1 && l[1] == ' ');

            if ((is_ordered && !current_is_ordered) || (is_unordered && !current_is_unordered)) {
                break;
            }

            // Extract item content
            std::string content;
            if (is_unordered) {
                content = trim(l.substr(2));
            } else {
                size_t dot_pos = l.find('.');
                if (dot_pos != std::string::npos) {
                    content = trim(l.substr(dot_pos + 1));
                }
            }

            // Check for task list item (GitHub extension)
            bool is_checked = false;
            bool is_task = false;
            if (options_.github_flavored && content.size() >= 4) {
                if (content.substr(0, 4) == "[x] " || content.substr(0, 4) == "[X] ") {
                    is_task = true;
                    is_checked = true;
                    content = content.substr(4);
                } else if (content.substr(0, 4) == "[ ] ") {
                    is_task = true;
                    content = content.substr(4);
                }
            }

            auto item_node = std::make_shared<Node>(NodeType::ListItem);
            if (is_task) {
                item_node->attributes["task"] = "true";
                item_node->attributes["checked"] = is_checked ? "true" : "false";
            }
            item_node->children = inline_parser_.parse(content);
            list_node->add_child(item_node);

            pos_++;
        }

        return list_node->children.empty() ? nullptr : list_node;
    }

    std::shared_ptr<Node> try_parse_table() {
        if (pos_ + 1 >= lines_.size()) return nullptr;

        const auto& header_line = lines_[pos_];
        const auto& separator_line = lines_[pos_ + 1];

        // Check if this looks like a table
        if (header_line.find('|') == std::string::npos ||
            separator_line.find('|') == std::string::npos) {
            return nullptr;
        }

        // Parse separator line to check if it's a valid table
        auto sep_cells = split_table_row(separator_line);
        bool valid_separator = true;
        for (const auto& cell : sep_cells) {
            std::string trimmed = trim(cell);
            bool valid = true;
            for (char c : trimmed) {
                if (c != '-' && c != ':' && c != ' ') {
                    valid = false;
                    break;
                }
            }
            if (!valid || trimmed.empty()) {
                valid_separator = false;
                break;
            }
        }

        if (!valid_separator) return nullptr;

        // Parse table
        auto table_node = std::make_shared<Node>(NodeType::Table);

        // Header row
        auto header_row = std::make_shared<Node>(NodeType::TableRow);
        header_row->attributes["header"] = "true";
        auto header_cells = split_table_row(header_line);
        for (const auto& cell : header_cells) {
            auto cell_node = std::make_shared<Node>(NodeType::TableCell);
            cell_node->attributes["header"] = "true";
            cell_node->children = inline_parser_.parse(trim(cell));
            header_row->add_child(cell_node);
        }
        table_node->add_child(header_row);

        pos_ += 2;  // Skip header and separator

        // Data rows
        while (pos_ < lines_.size()) {
            const auto& line = lines_[pos_];
            if (line.find('|') == std::string::npos) break;

            auto row = std::make_shared<Node>(NodeType::TableRow);
            auto cells = split_table_row(line);
            for (const auto& cell : cells) {
                auto cell_node = std::make_shared<Node>(NodeType::TableCell);
                cell_node->children = inline_parser_.parse(trim(cell));
                row->add_child(cell_node);
            }
            table_node->add_child(row);
            pos_++;
        }

        return table_node;
    }

    std::vector<std::string> split_table_row(const std::string& line) {
        std::vector<std::string> cells;
        std::string cell;
        bool in_escape = false;

        for (size_t i = 0; i < line.size(); ++i) {
            char c = line[i];
            if (c == '\\') {
                in_escape = true;
                cell += c;
            } else if (c == '|' && !in_escape) {
                if (!cell.empty() || !cells.empty()) {
                    cells.push_back(cell);
                    cell.clear();
                }
            } else {
                cell += c;
                in_escape = false;
            }
        }

        if (!cell.empty()) {
            cells.push_back(cell);
        }

        return cells;
    }

    std::shared_ptr<Node> try_parse_paragraph() {
        if (pos_ >= lines_.size()) return nullptr;

        std::vector<std::string> para_lines;

        while (pos_ < lines_.size()) {
            const auto& line = lines_[pos_];
            if (trim(line).empty()) {
                pos_++;
                break;
            }

            // Stop at headers, lists, code blocks, etc.
            if (!line.empty() &&
                (line[0] == '#' || line[0] == '>' ||
                 (line.size() >= 3 && line.substr(0, 3) == "```") ||
                 (line.size() >= 4 && line.substr(0, 4) == "    "))) {
                break;
            }

            para_lines.push_back(line);
            pos_++;
        }

        if (para_lines.empty()) return nullptr;

        std::string content;
        for (size_t i = 0; i < para_lines.size(); ++i) {
            if (i > 0) content += ' ';
            content += trim(para_lines[i]);
        }

        auto node = std::make_shared<Node>(NodeType::Paragraph);
        node->children = inline_parser_.parse(content);
        return node;
    }
};

// HTML generator
class HTMLGenerator {
public:
    HTMLGenerator(const ParserOptions& opts) : options_(opts), indent_level_(0) {}

    std::string generate(const std::shared_ptr<Node>& node) {
        if (!node) return "";

        switch (node->type) {
            case NodeType::Document:
                return generate_children(node);

            case NodeType::Header:
                return generate_header(node);

            case NodeType::Paragraph:
                return generate_paragraph(node);

            case NodeType::List:
                return generate_list(node);

            case NodeType::ListItem:
                return generate_list_item(node);

            case NodeType::CodeBlock:
                return generate_code_block(node);

            case NodeType::Blockquote:
                return generate_blockquote(node);

            case NodeType::HorizontalRule:
                return generate_horizontal_rule();

            case NodeType::Table:
                return generate_table(node);

            case NodeType::TableRow:
                return generate_table_row(node);

            case NodeType::TableCell:
                return generate_table_cell(node);

            case NodeType::Text:
                return generate_text(node);

            case NodeType::Bold:
                return generate_bold(node);

            case NodeType::Italic:
                return generate_italic(node);

            case NodeType::Code:
                return generate_code(node);

            case NodeType::Link:
                return generate_link(node);

            case NodeType::Image:
                return generate_image(node);

            case NodeType::Strikethrough:
                return generate_strikethrough(node);

            case NodeType::LineBreak:
                return "<br>";

            default:
                return "";
        }
    }

private:
    const ParserOptions& options_;
    int indent_level_;

    std::string indent() const {
        if (!options_.pretty_print) return "";
        return std::string(indent_level_ * 2, ' ');
    }

    std::string newline() const {
        return options_.pretty_print ? "\n" : "";
    }

    std::string generate_children(const std::shared_ptr<Node>& node) {
        std::string result;
        for (const auto& child : node->children) {
            result += generate(child);
        }
        return result;
    }

    std::string generate_header(const std::shared_ptr<Node>& node) {
        std::string level = node->attributes.at("level");
        std::string id = node->attributes.count("id") ? node->attributes.at("id") : "";

        std::string result = indent() + "<h" + level;
        if (!id.empty()) {
            result += " id=\"" + id + "\"";
        }
        result += ">";
        result += generate_children(node);
        result += "</h" + level + ">" + newline();

        return result;
    }

    std::string generate_paragraph(const std::shared_ptr<Node>& node) {
        return indent() + "<p>" + generate_children(node) + "</p>" + newline();
    }

    std::string generate_list(const std::shared_ptr<Node>& node) {
        bool ordered = (node->attributes.at("ordered") == "true");
        std::string tag = ordered ? "ol" : "ul";

        std::string result = indent() + "<" + tag + ">" + newline();
        indent_level_++;
        result += generate_children(node);
        indent_level_--;
        result += indent() + "</" + tag + ">" + newline();

        return result;
    }

    std::string generate_list_item(const std::shared_ptr<Node>& node) {
        std::string result = indent() + "<li>";

        // Task list checkbox
        if (node->attributes.count("task")) {
            bool checked = (node->attributes.at("checked") == "true");
            result += "<input type=\"checkbox\"";
            if (checked) result += " checked";
            result += " disabled> ";
        }

        result += generate_children(node);
        result += "</li>" + newline();

        return result;
    }

    std::string generate_code_block(const std::shared_ptr<Node>& node) {
        std::string content = options_.escape_html ?
            HTMLUtils::escape(node->content) : node->content;

        std::string result = indent() + "<pre><code";

        if (node->attributes.count("language")) {
            std::string lang = node->attributes.at("language");
            result += " class=\"" + options_.code_class_prefix + lang + "\"";
        }

        result += ">" + content + "</code></pre>" + newline();

        return result;
    }

    std::string generate_blockquote(const std::shared_ptr<Node>& node) {
        std::string result = indent() + "<blockquote>" + newline();
        indent_level_++;
        result += generate_children(node);
        indent_level_--;
        result += indent() + "</blockquote>" + newline();

        return result;
    }

    std::string generate_horizontal_rule() {
        return indent() + "<hr>" + newline();
    }

    std::string generate_table(const std::shared_ptr<Node>& node) {
        std::string result = indent() + "<table>" + newline();
        indent_level_++;

        bool in_header = true;
        for (const auto& row : node->children) {
            if (in_header && row->attributes.count("header")) {
                result += indent() + "<thead>" + newline();
                indent_level_++;
                result += generate(row);
                indent_level_--;
                result += indent() + "</thead>" + newline();
                result += indent() + "<tbody>" + newline();
                indent_level_++;
                in_header = false;
            } else {
                result += generate(row);
            }
        }

        if (!in_header) {
            indent_level_--;
            result += indent() + "</tbody>" + newline();
        }

        indent_level_--;
        result += indent() + "</table>" + newline();

        return result;
    }

    std::string generate_table_row(const std::shared_ptr<Node>& node) {
        std::string result = indent() + "<tr>" + newline();
        indent_level_++;
        result += generate_children(node);
        indent_level_--;
        result += indent() + "</tr>" + newline();

        return result;
    }

    std::string generate_table_cell(const std::shared_ptr<Node>& node) {
        std::string tag = node->attributes.count("header") ? "th" : "td";
        return indent() + "<" + tag + ">" + generate_children(node) + "</" + tag + ">" + newline();
    }

    std::string generate_text(const std::shared_ptr<Node>& node) {
        return options_.escape_html ?
            HTMLUtils::escape(node->content) : node->content;
    }

    std::string generate_bold(const std::shared_ptr<Node>& node) {
        return "<strong>" + generate_children(node) + "</strong>";
    }

    std::string generate_italic(const std::shared_ptr<Node>& node) {
        return "<em>" + generate_children(node) + "</em>";
    }

    std::string generate_code(const std::shared_ptr<Node>& node) {
        std::string content = options_.escape_html ?
            HTMLUtils::escape(node->content) : node->content;
        return "<code>" + content + "</code>";
    }

    std::string generate_link(const std::shared_ptr<Node>& node) {
        std::string href = node->attributes.at("href");
        std::string result = "<a href=\"" + href + "\"";

        if (node->attributes.count("title")) {
            result += " title=\"" + node->attributes.at("title") + "\"";
        }

        result += ">" + generate_children(node) + "</a>";
        return result;
    }

    std::string generate_image(const std::shared_ptr<Node>& node) {
        std::string src = node->attributes.at("src");
        std::string alt = node->attributes.at("alt");
        std::string result = "<img src=\"" + src + "\" alt=\"" + alt + "\"";

        if (node->attributes.count("title")) {
            result += " title=\"" + node->attributes.at("title") + "\"";
        }

        result += ">";
        return result;
    }

    std::string generate_strikethrough(const std::shared_ptr<Node>& node) {
        return "<del>" + generate_children(node) + "</del>";
    }
};

// Main parser class
class MarkdownParser {
public:
    MarkdownParser(const ParserOptions& options = ParserOptions())
        : options_(options),
          block_parser_(options),
          inline_parser_(options),
          html_generator_(options) {}

    std::string parse(const std::string& markdown) {
        auto ast = block_parser_.parse(markdown);
        return html_generator_.generate(ast);
    }

    std::string parse_inline(const std::string& markdown) {
        auto nodes = inline_parser_.parse(markdown);
        std::string result;
        for (const auto& node : nodes) {
            result += html_generator_.generate(node);
        }
        return result;
    }

    void reset() {
        // Reset any internal state if needed
    }

    void set_options(const ParserOptions& options) {
        options_ = options;
        block_parser_ = BlockParser(options);
        inline_parser_ = InlineParser(options);
        html_generator_ = HTMLGenerator(options);
    }

    ParserOptions get_options() const {
        return options_;
    }

    std::string get_table_of_contents() const {
        // TODO: Implement TOC generation
        return "";
    }

private:
    ParserOptions options_;
    BlockParser block_parser_;
    InlineParser inline_parser_;
    HTMLGenerator html_generator_;
};

} // namespace md
