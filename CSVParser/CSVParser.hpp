#pragma once

#include <string>
#include <string_view>
#include <vector>
#include <map>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <algorithm>
#include <iterator>
#include <memory>

namespace csv {

// Exception type
class CSVError : public std::runtime_error {
public:
    explicit CSVError(const std::string& msg) : std::runtime_error(msg) {}
};

// CSV parsing options
class CSVOptions {
public:
    CSVOptions& delimiter(char c) { delimiter_ = c; return *this; }
    CSVOptions& quote(char c) { quote_ = c; return *this; }
    CSVOptions& escape(char c) { escape_ = c; return *this; }
    CSVOptions& with_header(bool h = true) { has_header_ = h; return *this; }
    CSVOptions& skip_empty_rows(bool s = true) { skip_empty_ = s; return *this; }
    CSVOptions& trim_whitespace(bool t = true) { trim_ = t; return *this; }

    char get_delimiter() const { return delimiter_; }
    char get_quote() const { return quote_; }
    char get_escape() const { return escape_; }
    bool has_header() const { return has_header_; }
    bool skip_empty() const { return skip_empty_; }
    bool trim() const { return trim_; }

private:
    char delimiter_ = ',';
    char quote_ = '"';
    char escape_ = '"';
    bool has_header_ = false;
    bool skip_empty_ = false;
    bool trim_ = false;
};

// CSV row
class CSVRow {
public:
    CSVRow() = default;

    CSVRow(std::vector<std::string> fields, const std::vector<std::string>& headers = {})
        : fields_(std::move(fields)), headers_(&headers) {}

    // Get field by index
    std::string get(size_t index) const {
        if (index >= fields_.size()) {
            throw std::out_of_range("Field index out of range");
        }
        return fields_[index];
    }

    // Get field by header name
    std::string get(const std::string& header) const {
        if (!headers_ || headers_->empty()) {
            throw CSVError("No headers available");
        }

        auto it = std::find(headers_->begin(), headers_->end(), header);
        if (it == headers_->end()) {
            throw CSVError("Header not found: " + header);
        }

        size_t index = std::distance(headers_->begin(), it);
        return get(index);
    }

    // Get field with type conversion
    template<typename T>
    T get(size_t index) const {
        return convert<T>(get(index));
    }

    template<typename T>
    T get(const std::string& header) const {
        return convert<T>(get(header));
    }

    size_t size() const { return fields_.size(); }
    bool empty() const { return fields_.empty(); }

    // Iterator support
    auto begin() const { return fields_.begin(); }
    auto end() const { return fields_.end(); }

    const std::vector<std::string>& fields() const { return fields_; }

private:
    std::vector<std::string> fields_;
    const std::vector<std::string>* headers_ = nullptr;

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
            return lower == "true" || lower == "1" || lower == "yes";
        } else {
            static_assert(sizeof(T) == 0, "Unsupported type for CSV conversion");
        }
    }
};

// CSV parser
class CSVParser {
public:
    class Iterator {
    public:
        using iterator_category = std::input_iterator_tag;
        using value_type = CSVRow;
        using difference_type = std::ptrdiff_t;
        using pointer = const CSVRow*;
        using reference = const CSVRow&;

        Iterator(CSVParser* parser, bool end = false)
            : parser_(parser), is_end_(end) {
            if (!is_end_) {
                ++(*this);
            }
        }

        reference operator*() const { return current_row_; }
        pointer operator->() const { return &current_row_; }

        Iterator& operator++() {
            if (parser_ && parser_->parse_row(current_row_)) {
                return *this;
            }
            is_end_ = true;
            return *this;
        }

        Iterator operator++(int) {
            Iterator tmp = *this;
            ++(*this);
            return tmp;
        }

        bool operator==(const Iterator& other) const {
            return is_end_ == other.is_end_;
        }

        bool operator!=(const Iterator& other) const {
            return !(*this == other);
        }

    private:
        CSVParser* parser_;
        CSVRow current_row_;
        bool is_end_;
    };

    explicit CSVParser(const std::string& filename, const CSVOptions& opts = CSVOptions())
        : options_(opts), owns_stream_(true) {
        auto* file = new std::ifstream(filename);
        if (!file->is_open()) {
            delete file;
            throw CSVError("Cannot open file: " + filename);
        }
        stream_ = file;
        initialize();
    }

    explicit CSVParser(std::istream& stream, const CSVOptions& opts = CSVOptions())
        : stream_(&stream), options_(opts), owns_stream_(false) {
        initialize();
    }

    ~CSVParser() {
        if (owns_stream_) {
            delete stream_;
        }
    }

    Iterator begin() { return Iterator(this); }
    Iterator end() { return Iterator(this, true); }

    const std::vector<std::string>& headers() const { return headers_; }

    void set_buffer_size(size_t size) { buffer_size_ = size; }

private:
    std::istream* stream_;
    CSVOptions options_;
    std::vector<std::string> headers_;
    size_t buffer_size_ = 4096;
    bool owns_stream_;
    std::string line_buffer_;
    bool at_eof_ = false;

    void initialize() {
        if (options_.has_header()) {
            CSVRow header_row;
            if (parse_row(header_row)) {
                headers_ = header_row.fields();
            }
        }
    }

    bool parse_row(CSVRow& row) {
        while (true) {
            if (!read_line()) {
                return false;
            }

            auto fields = parse_line(line_buffer_);

            // Skip empty rows if option is set
            if (options_.skip_empty() && fields.empty()) {
                continue;
            }

            row = CSVRow(fields, headers_);
            return true;
        }
    }

    bool read_line() {
        if (at_eof_) return false;

        line_buffer_.clear();

        if (!std::getline(*stream_, line_buffer_)) {
            at_eof_ = true;
            return false;
        }

        // Remove trailing CR if present (for CRLF line endings)
        if (!line_buffer_.empty() && line_buffer_.back() == '\r') {
            line_buffer_.pop_back();
        }

        return true;
    }

    std::vector<std::string> parse_line(const std::string& line) {
        std::vector<std::string> fields;
        std::string field;
        bool in_quotes = false;
        size_t i = 0;

        while (i < line.size()) {
            char c = line[i];

            if (in_quotes) {
                if (c == options_.get_quote()) {
                    // Check for escaped quote
                    if (i + 1 < line.size() && line[i + 1] == options_.get_escape()) {
                        field += options_.get_quote();
                        i += 2;
                    } else {
                        // End of quoted field
                        in_quotes = false;
                        i++;
                    }
                } else {
                    field += c;
                    i++;
                }
            } else {
                if (c == options_.get_quote()) {
                    // Start of quoted field
                    in_quotes = true;
                    i++;
                } else if (c == options_.get_delimiter()) {
                    // End of field
                    fields.push_back(trim_field(field));
                    field.clear();
                    i++;
                } else {
                    field += c;
                    i++;
                }
            }
        }

        // Add last field
        fields.push_back(trim_field(field));

        return fields;
    }

    std::string trim_field(const std::string& field) const {
        if (!options_.trim()) {
            return field;
        }

        auto start = field.find_first_not_of(" \t");
        if (start == std::string::npos) {
            return "";
        }

        auto end = field.find_last_not_of(" \t");
        return field.substr(start, end - start + 1);
    }
};

// CSV writer
class CSVWriter {
public:
    explicit CSVWriter(const std::string& filename, const CSVOptions& opts = CSVOptions())
        : options_(opts), owns_stream_(true) {
        auto* file = new std::ofstream(filename);
        if (!file->is_open()) {
            delete file;
            throw CSVError("Cannot create file: " + filename);
        }
        stream_ = file;
    }

    explicit CSVWriter(std::ostream& stream, const CSVOptions& opts = CSVOptions())
        : stream_(&stream), options_(opts), owns_stream_(false) {}

    ~CSVWriter() {
        if (owns_stream_) {
            delete stream_;
        }
    }

    void write_row(const std::vector<std::string>& row) {
        for (size_t i = 0; i < row.size(); ++i) {
            if (i > 0) {
                *stream_ << options_.get_delimiter();
            }
            *stream_ << escape_field(row[i]);
        }
        *stream_ << '\n';
    }

    void write_row(const CSVRow& row) {
        write_row(row.fields());
    }

    void close() {
        if (owns_stream_) {
            static_cast<std::ofstream*>(stream_)->close();
        }
    }

private:
    std::ostream* stream_;
    CSVOptions options_;
    bool owns_stream_;

    std::string escape_field(const std::string& field) const {
        bool needs_quoting = false;

        // Check if field needs quoting
        for (char c : field) {
            if (c == options_.get_delimiter() ||
                c == options_.get_quote() ||
                c == '\n' ||
                c == '\r') {
                needs_quoting = true;
                break;
            }
        }

        if (!needs_quoting) {
            return field;
        }

        // Quote and escape
        std::string result;
        result += options_.get_quote();

        for (char c : field) {
            if (c == options_.get_quote()) {
                result += options_.get_escape();
                result += options_.get_quote();
            } else {
                result += c;
            }
        }

        result += options_.get_quote();
        return result;
    }
};

} // namespace csv
