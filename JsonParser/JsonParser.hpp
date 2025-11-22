#pragma once

#include <string>
#include <string_view>
#include <vector>
#include <unordered_map>
#include <variant>
#include <memory>
#include <stdexcept>
#include <sstream>
#include <charconv>
#include <cctype>
#include <cstring>

// SIMD support detection
#if defined(__SSE4_2__) || defined(__AVX2__)
    #define JSON_SIMD_ENABLED 1
    #include <immintrin.h>
    #ifdef __AVX2__
        #define JSON_AVX2_ENABLED 1
    #endif
#else
    #define JSON_SIMD_ENABLED 0
#endif

namespace json {

// SIMD-accelerated helper functions
namespace simd {

#if JSON_SIMD_ENABLED

// Fast whitespace skipping using SIMD
inline size_t skip_whitespace_simd(const char* data, size_t pos, size_t size) {
    const char* ptr = data + pos;
    const char* end = data + size;

#ifdef JSON_AVX2_ENABLED
    // AVX2: Process 32 bytes at a time
    __m256i ws = _mm256_set1_epi8(' ');
    __m256i tab = _mm256_set1_epi8('\t');
    __m256i nl = _mm256_set1_epi8('\n');
    __m256i cr = _mm256_set1_epi8('\r');

    while (ptr + 32 <= end) {
        __m256i chunk = _mm256_loadu_si256((__m256i*)ptr);
        __m256i is_ws = _mm256_or_si256(
            _mm256_or_si256(_mm256_cmpeq_epi8(chunk, ws), _mm256_cmpeq_epi8(chunk, tab)),
            _mm256_or_si256(_mm256_cmpeq_epi8(chunk, nl), _mm256_cmpeq_epi8(chunk, cr))
        );

        int mask = _mm256_movemask_epi8(is_ws);
        if (mask != -1) {
            // Not all whitespace, count trailing ones
            int count = __builtin_ctz(~mask);
            return (ptr - data) + count;
        }
        ptr += 32;
    }
#else
    // SSE4.2: Process 16 bytes at a time
    __m128i ws = _mm_set1_epi8(' ');
    __m128i tab = _mm_set1_epi8('\t');
    __m128i nl = _mm_set1_epi8('\n');
    __m128i cr = _mm_set1_epi8('\r');

    while (ptr + 16 <= end) {
        __m128i chunk = _mm_loadu_si128((__m128i*)ptr);
        __m128i is_ws = _mm_or_si128(
            _mm_or_si128(_mm_cmpeq_epi8(chunk, ws), _mm_cmpeq_epi8(chunk, tab)),
            _mm_or_si128(_mm_cmpeq_epi8(chunk, nl), _mm_cmpeq_epi8(chunk, cr))
        );

        int mask = _mm_movemask_epi8(is_ws);
        if (mask != 0xFFFF) {
            int count = __builtin_ctz(~mask);
            return (ptr - data) + count;
        }
        ptr += 16;
    }
#endif

    // Fallback for remaining bytes
    while (ptr < end && (*ptr == ' ' || *ptr == '\t' || *ptr == '\n' || *ptr == '\r')) {
        ++ptr;
    }

    return ptr - data;
}

// Fast quote finding using SIMD
inline size_t find_quote_simd(const char* data, size_t pos, size_t size) {
    const char* ptr = data + pos;
    const char* end = data + size;

#ifdef JSON_AVX2_ENABLED
    __m256i quote = _mm256_set1_epi8('"');
    __m256i backslash = _mm256_set1_epi8('\\');

    while (ptr + 32 <= end) {
        __m256i chunk = _mm256_loadu_si256((__m256i*)ptr);
        __m256i is_quote = _mm256_cmpeq_epi8(chunk, quote);
        __m256i is_backslash = _mm256_cmpeq_epi8(chunk, backslash);

        int quote_mask = _mm256_movemask_epi8(is_quote);
        int backslash_mask = _mm256_movemask_epi8(is_backslash);

        if (quote_mask != 0) {
            int count = __builtin_ctz(quote_mask);
            return (ptr - data) + count;
        }

        if (backslash_mask != 0) {
            // Has escape, use scalar fallback
            break;
        }

        ptr += 32;
    }
#else
    __m128i quote = _mm_set1_epi8('"');

    while (ptr + 16 <= end) {
        __m128i chunk = _mm_loadu_si128((__m128i*)ptr);
        __m128i is_quote = _mm_cmpeq_epi8(chunk, quote);

        int mask = _mm_movemask_epi8(is_quote);
        if (mask != 0) {
            int count = __builtin_ctz(mask);
            return (ptr - data) + count;
        }

        ptr += 16;
    }
#endif

    // Scalar fallback
    while (ptr < end) {
        if (*ptr == '"') return ptr - data;
        if (*ptr == '\\') {
            // Skip escaped character
            if (ptr + 1 < end) ptr += 2;
            else break;
        } else {
            ++ptr;
        }
    }

    return size; // Not found
}

#endif // JSON_SIMD_ENABLED

// Fallback scalar implementations
inline size_t skip_whitespace_scalar(const char* data, size_t pos, size_t size) {
    while (pos < size && (data[pos] == ' ' || data[pos] == '\t' ||
                          data[pos] == '\n' || data[pos] == '\r')) {
        ++pos;
    }
    return pos;
}

inline size_t find_quote_scalar(const char* data, size_t pos, size_t size) {
    while (pos < size) {
        if (data[pos] == '"') return pos;
        if (data[pos] == '\\') {
            if (pos + 1 < size) pos += 2;
            else break;
        } else {
            ++pos;
        }
    }
    return size;
}

} // namespace simd

namespace json {

// Forward declarations
class Value;
class Document;

// Exception types
class ParseError : public std::runtime_error {
public:
    ParseError(const std::string& msg, size_t pos)
        : std::runtime_error(msg + " at position " + std::to_string(pos))
        , position(pos) {}

    size_t position;
};

// Value types
enum class ValueType {
    Null,
    Bool,
    Number,
    String,
    Array,
    Object
};

// Type aliases
using Array = std::vector<Value>;
using Object = std::unordered_map<std::string, Value>;

// JSON Value class
class Value {
public:
    Value() : data_(nullptr) {}
    Value(std::nullptr_t) : data_(nullptr) {}
    Value(bool b) : data_(b) {}
    Value(int i) : data_(static_cast<double>(i)) {}
    Value(double d) : data_(d) {}
    Value(const char* s) : data_(std::string(s)) {}
    Value(std::string s) : data_(std::move(s)) {}
    Value(std::string_view sv) : data_(std::string(sv)) {}
    Value(Array arr) : data_(std::move(arr)) {}
    Value(Object obj) : data_(std::move(obj)) {}

    // Type checking
    ValueType type() const {
        if (std::holds_alternative<std::nullptr_t>(data_)) return ValueType::Null;
        if (std::holds_alternative<bool>(data_)) return ValueType::Bool;
        if (std::holds_alternative<double>(data_)) return ValueType::Number;
        if (std::holds_alternative<std::string>(data_)) return ValueType::String;
        if (std::holds_alternative<Array>(data_)) return ValueType::Array;
        if (std::holds_alternative<Object>(data_)) return ValueType::Object;
        return ValueType::Null;
    }

    bool is_null() const { return type() == ValueType::Null; }
    bool is_bool() const { return type() == ValueType::Bool; }
    bool is_number() const { return type() == ValueType::Number; }
    bool is_string() const { return type() == ValueType::String; }
    bool is_array() const { return type() == ValueType::Array; }
    bool is_object() const { return type() == ValueType::Object; }

    // Value access
    bool as_bool() const {
        if (auto* b = std::get_if<bool>(&data_)) return *b;
        throw std::runtime_error("Value is not a boolean");
    }

    double as_double() const {
        if (auto* d = std::get_if<double>(&data_)) return *d;
        throw std::runtime_error("Value is not a number");
    }

    int as_int() const {
        return static_cast<int>(as_double());
    }

    const std::string& as_string() const {
        if (auto* s = std::get_if<std::string>(&data_)) return *s;
        throw std::runtime_error("Value is not a string");
    }

    Array& as_array() {
        if (auto* a = std::get_if<Array>(&data_)) return *a;
        throw std::runtime_error("Value is not an array");
    }

    const Array& as_array() const {
        if (auto* a = std::get_if<Array>(&data_)) return *a;
        throw std::runtime_error("Value is not an array");
    }

    Object& as_object() {
        if (auto* o = std::get_if<Object>(&data_)) return *o;
        throw std::runtime_error("Value is not an object");
    }

    const Object& as_object() const {
        if (auto* o = std::get_if<Object>(&data_)) return *o;
        throw std::runtime_error("Value is not an object");
    }

    // Array operations
    void push_back(Value value) {
        as_array().push_back(std::move(value));
    }

    size_t size() const {
        if (is_array()) return as_array().size();
        if (is_object()) return as_object().size();
        return 0;
    }

    // Object operations
    Value& operator[](std::string_view key) {
        return as_object()[std::string(key)];
    }

    Value& operator[](size_t index) {
        return as_array()[index];
    }

    const Value& operator[](std::string_view key) const {
        return as_object().at(std::string(key));
    }

    const Value& operator[](size_t index) const {
        return as_array()[index];
    }

    // Helper to create arrays and objects
    static Value array() { return Value(Array{}); }
    static Value object() { return Value(Object{}); }

    // Stringify
    std::string stringify(int indent = -1, int current_indent = 0) const;

private:
    std::variant<std::nullptr_t, bool, double, std::string, Array, Object> data_;
};

// SAX Handler interface
class SAXHandler {
public:
    virtual ~SAXHandler() = default;
    virtual void on_null() {}
    virtual void on_bool(bool value) { (void)value; }
    virtual void on_number(double value) { (void)value; }
    virtual void on_string(std::string_view value) { (void)value; }
    virtual void on_start_object() {}
    virtual void on_key(std::string_view key) { (void)key; }
    virtual void on_end_object() {}
    virtual void on_start_array() {}
    virtual void on_end_array() {}
};

// JSON Parser
class Parser {
public:
    explicit Parser(std::string_view json)
        : json_(json), pos_(0) {}

    Value parse() {
        skip_whitespace();
        Value result = parse_value();
        skip_whitespace();
        if (pos_ < json_.size()) {
            throw ParseError("Unexpected characters after JSON", pos_);
        }
        return result;
    }

private:
    std::string_view json_;
    size_t pos_;

    void skip_whitespace() {
#if JSON_SIMD_ENABLED
        pos_ = simd::skip_whitespace_simd(json_.data(), pos_, json_.size());
#else
        pos_ = simd::skip_whitespace_scalar(json_.data(), pos_, json_.size());
#endif
    }

    char peek() const {
        return pos_ < json_.size() ? json_[pos_] : '\0';
    }

    char advance() {
        return pos_ < json_.size() ? json_[pos_++] : '\0';
    }

    void expect(char ch) {
        if (advance() != ch) {
            throw ParseError(std::string("Expected '") + ch + "'", pos_ - 1);
        }
    }

    Value parse_value() {
        skip_whitespace();
        char ch = peek();

        switch (ch) {
            case 'n': return parse_null();
            case 't': case 'f': return parse_bool();
            case '"': return parse_string();
            case '[': return parse_array();
            case '{': return parse_object();
            case '-': case '0': case '1': case '2': case '3': case '4':
            case '5': case '6': case '7': case '8': case '9':
                return parse_number();
            default:
                throw ParseError("Unexpected character", pos_);
        }
    }

    Value parse_null() {
        if (json_.substr(pos_, 4) == "null") {
            pos_ += 4;
            return Value(nullptr);
        }
        throw ParseError("Invalid null literal", pos_);
    }

    Value parse_bool() {
        if (json_.substr(pos_, 4) == "true") {
            pos_ += 4;
            return Value(true);
        }
        if (json_.substr(pos_, 5) == "false") {
            pos_ += 5;
            return Value(false);
        }
        throw ParseError("Invalid boolean literal", pos_);
    }

    Value parse_number() {
        size_t start = pos_;

        // Handle negative sign
        if (peek() == '-') advance();

        // Parse digits
        if (!std::isdigit(peek())) {
            throw ParseError("Invalid number", pos_);
        }

        // Integer part
        if (peek() == '0') {
            advance();
        } else {
            while (std::isdigit(peek())) advance();
        }

        // Fractional part
        if (peek() == '.') {
            advance();
            if (!std::isdigit(peek())) {
                throw ParseError("Invalid number: expected digit after decimal point", pos_);
            }
            while (std::isdigit(peek())) advance();
        }

        // Exponent part
        if (peek() == 'e' || peek() == 'E') {
            advance();
            if (peek() == '+' || peek() == '-') advance();
            if (!std::isdigit(peek())) {
                throw ParseError("Invalid number: expected digit in exponent", pos_);
            }
            while (std::isdigit(peek())) advance();
        }

        std::string_view num_str = json_.substr(start, pos_ - start);
        double value;
        auto result = std::from_chars(num_str.data(), num_str.data() + num_str.size(), value);

        if (result.ec != std::errc()) {
            throw ParseError("Invalid number format", start);
        }

        return Value(value);
    }

    Value parse_string() {
        expect('"');
        size_t start = pos_;
        std::string result;
        bool has_escapes = false;

        while (pos_ < json_.size() && json_[pos_] != '"') {
            if (json_[pos_] == '\\') {
                has_escapes = true;
                ++pos_;
                if (pos_ >= json_.size()) {
                    throw ParseError("Unterminated string", start);
                }
                ++pos_;
            } else {
                ++pos_;
            }
        }

        if (pos_ >= json_.size()) {
            throw ParseError("Unterminated string", start);
        }

        std::string_view str_content = json_.substr(start, pos_ - start);
        ++pos_; // Skip closing quote

        if (!has_escapes) {
            return Value(str_content);
        }

        // Handle escape sequences
        result.reserve(str_content.size());
        for (size_t i = 0; i < str_content.size(); ++i) {
            if (str_content[i] == '\\' && i + 1 < str_content.size()) {
                switch (str_content[++i]) {
                    case '"': result += '"'; break;
                    case '\\': result += '\\'; break;
                    case '/': result += '/'; break;
                    case 'b': result += '\b'; break;
                    case 'f': result += '\f'; break;
                    case 'n': result += '\n'; break;
                    case 'r': result += '\r'; break;
                    case 't': result += '\t'; break;
                    default: result += str_content[i]; break;
                }
            } else {
                result += str_content[i];
            }
        }

        return Value(std::move(result));
    }

    Value parse_array() {
        expect('[');
        skip_whitespace();

        Array arr;

        if (peek() == ']') {
            advance();
            return Value(std::move(arr));
        }

        while (true) {
            arr.push_back(parse_value());
            skip_whitespace();

            if (peek() == ']') {
                advance();
                break;
            }

            expect(',');
            skip_whitespace();
        }

        return Value(std::move(arr));
    }

    Value parse_object() {
        expect('{');
        skip_whitespace();

        Object obj;

        if (peek() == '}') {
            advance();
            return Value(std::move(obj));
        }

        while (true) {
            skip_whitespace();
            if (peek() != '"') {
                throw ParseError("Expected string key in object", pos_);
            }

            Value key_value = parse_string();
            std::string key = key_value.as_string();

            skip_whitespace();
            expect(':');
            skip_whitespace();

            obj[key] = parse_value();

            skip_whitespace();

            if (peek() == '}') {
                advance();
                break;
            }

            expect(',');
        }

        return Value(std::move(obj));
    }
};

// SAX Parser
class SAXParser {
public:
    SAXParser(SAXHandler& handler) : handler_(handler) {}

    void parse(std::string_view json) {
        json_ = json;
        pos_ = 0;
        skip_whitespace();
        parse_value();
    }

private:
    SAXHandler& handler_;
    std::string_view json_;
    size_t pos_;

    void skip_whitespace() {
#if JSON_SIMD_ENABLED
        pos_ = simd::skip_whitespace_simd(json_.data(), pos_, json_.size());
#else
        pos_ = simd::skip_whitespace_scalar(json_.data(), pos_, json_.size());
#endif
    }

    char peek() const {
        return pos_ < json_.size() ? json_[pos_] : '\0';
    }

    char advance() {
        return pos_ < json_.size() ? json_[pos_++] : '\0';
    }

    void expect(char ch) {
        if (advance() != ch) {
            throw ParseError(std::string("Expected '") + ch + "'", pos_ - 1);
        }
    }

    void parse_value() {
        skip_whitespace();
        char ch = peek();

        switch (ch) {
            case 'n': parse_null(); break;
            case 't': case 'f': parse_bool(); break;
            case '"': parse_string(); break;
            case '[': parse_array(); break;
            case '{': parse_object(); break;
            case '-': case '0': case '1': case '2': case '3': case '4':
            case '5': case '6': case '7': case '8': case '9':
                parse_number(); break;
            default:
                throw ParseError("Unexpected character", pos_);
        }
    }

    void parse_null() {
        if (json_.substr(pos_, 4) == "null") {
            pos_ += 4;
            handler_.on_null();
            return;
        }
        throw ParseError("Invalid null literal", pos_);
    }

    void parse_bool() {
        if (json_.substr(pos_, 4) == "true") {
            pos_ += 4;
            handler_.on_bool(true);
            return;
        }
        if (json_.substr(pos_, 5) == "false") {
            pos_ += 5;
            handler_.on_bool(false);
            return;
        }
        throw ParseError("Invalid boolean literal", pos_);
    }

    void parse_number() {
        size_t start = pos_;

        if (peek() == '-') advance();

        if (!std::isdigit(peek())) {
            throw ParseError("Invalid number", pos_);
        }

        if (peek() == '0') {
            advance();
        } else {
            while (std::isdigit(peek())) advance();
        }

        if (peek() == '.') {
            advance();
            if (!std::isdigit(peek())) {
                throw ParseError("Invalid number", pos_);
            }
            while (std::isdigit(peek())) advance();
        }

        if (peek() == 'e' || peek() == 'E') {
            advance();
            if (peek() == '+' || peek() == '-') advance();
            if (!std::isdigit(peek())) {
                throw ParseError("Invalid number", pos_);
            }
            while (std::isdigit(peek())) advance();
        }

        std::string_view num_str = json_.substr(start, pos_ - start);
        double value;
        auto result = std::from_chars(num_str.data(), num_str.data() + num_str.size(), value);

        if (result.ec == std::errc()) {
            handler_.on_number(value);
        }
    }

    void parse_string() {
        expect('"');
        size_t start = pos_;

        while (pos_ < json_.size() && json_[pos_] != '"') {
            if (json_[pos_] == '\\') {
                ++pos_;
                if (pos_ >= json_.size()) break;
            }
            ++pos_;
        }

        std::string_view str = json_.substr(start, pos_ - start);
        ++pos_;

        handler_.on_string(str);
    }

    void parse_array() {
        expect('[');
        handler_.on_start_array();
        skip_whitespace();

        if (peek() == ']') {
            advance();
            handler_.on_end_array();
            return;
        }

        while (true) {
            parse_value();
            skip_whitespace();

            if (peek() == ']') {
                advance();
                break;
            }

            expect(',');
            skip_whitespace();
        }

        handler_.on_end_array();
    }

    void parse_object() {
        expect('{');
        handler_.on_start_object();
        skip_whitespace();

        if (peek() == '}') {
            advance();
            handler_.on_end_object();
            return;
        }

        while (true) {
            skip_whitespace();
            expect('"');
            size_t start = pos_;

            while (pos_ < json_.size() && json_[pos_] != '"') {
                if (json_[pos_] == '\\') ++pos_;
                ++pos_;
            }

            std::string_view key = json_.substr(start, pos_ - start);
            ++pos_;

            handler_.on_key(key);

            skip_whitespace();
            expect(':');
            skip_whitespace();

            parse_value();
            skip_whitespace();

            if (peek() == '}') {
                advance();
                break;
            }

            expect(',');
        }

        handler_.on_end_object();
    }
};

// Document class
class Document {
public:
    Document() = default;
    Document(Value root) : root_(std::move(root)) {}

    static Document parse(std::string_view json) {
        Parser parser(json);
        return Document(parser.parse());
    }

    Value& root() { return root_; }
    const Value& root() const { return root_; }

    Value& operator[](std::string_view key) {
        return root_[key];
    }

    const Value& operator[](std::string_view key) const {
        return root_[key];
    }

    Value& operator[](size_t index) {
        return root_[index];
    }

    const Value& operator[](size_t index) const {
        return root_[index];
    }

    // JSON Pointer support (RFC 6901)
    Value at_pointer(std::string_view pointer) const {
        if (pointer.empty() || pointer[0] != '/') {
            throw std::runtime_error("JSON Pointer must start with '/'");
        }

        if (pointer == "/") {
            return root_;
        }

        Value current = root_;
        size_t pos = 1;

        while (pos < pointer.size()) {
            size_t next_slash = pointer.find('/', pos);
            if (next_slash == std::string_view::npos) {
                next_slash = pointer.size();
            }

            std::string_view token = pointer.substr(pos, next_slash - pos);

            if (current.is_object()) {
                current = current[token];
            } else if (current.is_array()) {
                size_t index = std::stoul(std::string(token));
                current = current[index];
            } else {
                throw std::runtime_error("Cannot traverse non-container type");
            }

            pos = next_slash + 1;
        }

        return current;
    }

    void set_object() {
        root_ = Value::object();
    }

    void set_array() {
        root_ = Value::array();
    }

    std::string stringify(int indent = -1) const {
        return root_.stringify(indent);
    }

private:
    Value root_;
};

// Value stringify implementation
inline std::string Value::stringify(int indent, int current_indent) const {
    std::ostringstream oss;

    auto make_indent = [](int level, int spaces) {
        return std::string(level * spaces, ' ');
    };

    switch (type()) {
        case ValueType::Null:
            oss << "null";
            break;

        case ValueType::Bool:
            oss << (as_bool() ? "true" : "false");
            break;

        case ValueType::Number: {
            double d = as_double();
            if (d == static_cast<int>(d)) {
                oss << static_cast<int>(d);
            } else {
                oss << d;
            }
            break;
        }

        case ValueType::String:
            oss << '"' << as_string() << '"';
            break;

        case ValueType::Array: {
            const auto& arr = as_array();
            oss << '[';
            if (indent >= 0 && !arr.empty()) {
                oss << '\n';
                for (size_t i = 0; i < arr.size(); ++i) {
                    oss << make_indent(current_indent + 1, indent);
                    oss << arr[i].stringify(indent, current_indent + 1);
                    if (i < arr.size() - 1) oss << ',';
                    oss << '\n';
                }
                oss << make_indent(current_indent, indent);
            } else {
                for (size_t i = 0; i < arr.size(); ++i) {
                    oss << arr[i].stringify(indent, current_indent + 1);
                    if (i < arr.size() - 1) oss << ',';
                }
            }
            oss << ']';
            break;
        }

        case ValueType::Object: {
            const auto& obj = as_object();
            oss << '{';
            if (indent >= 0 && !obj.empty()) {
                oss << '\n';
                size_t count = 0;
                for (const auto& [key, value] : obj) {
                    oss << make_indent(current_indent + 1, indent);
                    oss << '"' << key << '"' << ": ";
                    oss << value.stringify(indent, current_indent + 1);
                    if (++count < obj.size()) oss << ',';
                    oss << '\n';
                }
                oss << make_indent(current_indent, indent);
            } else {
                size_t count = 0;
                for (const auto& [key, value] : obj) {
                    oss << '"' << key << '"' << ':';
                    oss << value.stringify(indent, current_indent + 1);
                    if (++count < obj.size()) oss << ',';
                }
            }
            oss << '}';
            break;
        }
    }

    return oss.str();
}

// Convenience function
inline Document parse(std::string_view json) {
    return Document::parse(json);
}

} // namespace json
