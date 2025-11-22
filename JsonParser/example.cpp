#include "JsonParser.hpp"
#include <iostream>
#include <chrono>
#include <fstream>

using namespace json;

// Example 1: Basic DOM parsing
void example_basic_parsing() {
    std::cout << "\n=== Example 1: Basic DOM Parsing ===" << std::endl;

    std::string json_str = R"({
        "name": "Alice",
        "age": 30,
        "active": true,
        "salary": 75000.50
    })";

    try {
        Document doc = parse(json_str);

        std::cout << "Name: " << doc["name"].as_string() << std::endl;
        std::cout << "Age: " << doc["age"].as_int() << std::endl;
        std::cout << "Active: " << (doc["active"].as_bool() ? "yes" : "no") << std::endl;
        std::cout << "Salary: $" << doc["salary"].as_double() << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }
}

// Example 2: Array parsing and iteration
void example_array_parsing() {
    std::cout << "\n=== Example 2: Array Parsing ===" << std::endl;

    std::string json_str = R"({
        "numbers": [1, 2, 3, 4, 5],
        "fruits": ["apple", "banana", "cherry"]
    })";

    Document doc = parse(json_str);

    std::cout << "Numbers: ";
    for (const auto& num : doc["numbers"].as_array()) {
        std::cout << num.as_int() << " ";
    }
    std::cout << std::endl;

    std::cout << "Fruits: ";
    for (const auto& fruit : doc["fruits"].as_array()) {
        std::cout << fruit.as_string() << " ";
    }
    std::cout << std::endl;
}

// Example 3: Object iteration
void example_object_iteration() {
    std::cout << "\n=== Example 3: Object Iteration ===" << std::endl;

    std::string json_str = R"({
        "scores": {
            "math": 95,
            "science": 87,
            "english": 92
        }
    })";

    Document doc = parse(json_str);

    std::cout << "Scores:" << std::endl;
    for (const auto& [subject, score] : doc["scores"].as_object()) {
        std::cout << "  " << subject << ": " << score.as_int() << std::endl;
    }
}

// Example 4: Nested structures
void example_nested_structures() {
    std::cout << "\n=== Example 4: Nested Structures ===" << std::endl;

    std::string json_str = R"({
        "company": {
            "name": "Tech Corp",
            "employees": [
                {"name": "Alice", "role": "Engineer"},
                {"name": "Bob", "role": "Designer"},
                {"name": "Charlie", "role": "Manager"}
            ],
            "location": {
                "city": "San Francisco",
                "country": "USA"
            }
        }
    })";

    Document doc = parse(json_str);

    std::cout << "Company: " << doc["company"]["name"].as_string() << std::endl;
    std::cout << "Location: " << doc["company"]["location"]["city"].as_string()
              << ", " << doc["company"]["location"]["country"].as_string() << std::endl;

    std::cout << "\nEmployees:" << std::endl;
    for (const auto& emp : doc["company"]["employees"].as_array()) {
        std::cout << "  " << emp["name"].as_string()
                  << " - " << emp["role"].as_string() << std::endl;
    }
}

// Example 5: SAX-style parsing
class PrintHandler : public SAXHandler {
public:
    void on_null() override {
        std::cout << indent() << "null" << std::endl;
    }

    void on_bool(bool value) override {
        std::cout << indent() << (value ? "true" : "false") << std::endl;
    }

    void on_number(double value) override {
        std::cout << indent() << value << std::endl;
    }

    void on_string(std::string_view value) override {
        std::cout << indent() << "\"" << value << "\"" << std::endl;
    }

    void on_start_object() override {
        std::cout << indent() << "{" << std::endl;
        depth_++;
    }

    void on_key(std::string_view key) override {
        std::cout << indent() << "key: \"" << key << "\"" << std::endl;
    }

    void on_end_object() override {
        depth_--;
        std::cout << indent() << "}" << std::endl;
    }

    void on_start_array() override {
        std::cout << indent() << "[" << std::endl;
        depth_++;
    }

    void on_end_array() override {
        depth_--;
        std::cout << indent() << "]" << std::endl;
    }

private:
    int depth_ = 0;

    std::string indent() const {
        return std::string(depth_ * 2, ' ');
    }
};

void example_sax_parsing() {
    std::cout << "\n=== Example 5: SAX-Style Parsing ===" << std::endl;

    std::string json_str = R"({"name":"Alice","age":30,"scores":[95,87,92]})";

    PrintHandler handler;
    SAXParser parser(handler);

    try {
        parser.parse(json_str);
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }
}

// Example 6: Building JSON
void example_building_json() {
    std::cout << "\n=== Example 6: Building JSON ===" << std::endl;

    Document doc;
    doc.set_object();

    doc["name"] = "Alice";
    doc["age"] = 30;
    doc["active"] = true;
    doc["salary"] = 75000.50;

    doc["scores"] = Value::array();
    doc["scores"].push_back(95);
    doc["scores"].push_back(87);
    doc["scores"].push_back(92);

    doc["address"] = Value::object();
    doc["address"]["city"] = "New York";
    doc["address"]["zip"] = "10001";

    std::cout << "Compact JSON:" << std::endl;
    std::cout << doc.stringify() << std::endl;

    std::cout << "\nPretty JSON:" << std::endl;
    std::cout << doc.stringify(2) << std::endl;
}

// Example 7: JSON Pointer
void example_json_pointer() {
    std::cout << "\n=== Example 7: JSON Pointer ===" << std::endl;

    std::string json_str = R"({
        "user": {
            "name": "Alice",
            "contact": {
                "email": "alice@example.com",
                "phone": "555-1234"
            },
            "scores": [95, 87, 92]
        }
    })";

    Document doc = parse(json_str);

    try {
        auto name = doc.at_pointer("/user/name");
        std::cout << "Name: " << name.as_string() << std::endl;

        auto email = doc.at_pointer("/user/contact/email");
        std::cout << "Email: " << email.as_string() << std::endl;

        auto first_score = doc.at_pointer("/user/scores/0");
        std::cout << "First score: " << first_score.as_int() << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }
}

// Example 8: Error handling
void example_error_handling() {
    std::cout << "\n=== Example 8: Error Handling ===" << std::endl;

    std::vector<std::string> invalid_jsons = {
        R"({"name": "Alice")",           // Missing closing brace
        R"({"name": Alice})",             // Unquoted string value
        R"({"age": 30,})",                // Trailing comma
        R"([1, 2, 3,])",                  // Trailing comma in array
        R"({"number": 123.})",            // Invalid number
    };

    for (size_t i = 0; i < invalid_jsons.size(); ++i) {
        std::cout << "\nTesting invalid JSON #" << (i + 1) << ":" << std::endl;
        try {
            Document doc = parse(invalid_jsons[i]);
            std::cout << "  Unexpectedly succeeded!" << std::endl;
        } catch (const ParseError& e) {
            std::cout << "  Caught ParseError: " << e.what() << std::endl;
        } catch (const std::exception& e) {
            std::cout << "  Caught exception: " << e.what() << std::endl;
        }
    }
}

// Example 9: Type checking
void example_type_checking() {
    std::cout << "\n=== Example 9: Type Checking ===" << std::endl;

    std::string json_str = R"({
        "null_value": null,
        "bool_value": true,
        "number_value": 42,
        "string_value": "hello",
        "array_value": [1, 2, 3],
        "object_value": {"key": "value"}
    })";

    Document doc = parse(json_str);

    std::cout << "null_value is null: " << (doc["null_value"].is_null() ? "yes" : "no") << std::endl;
    std::cout << "bool_value is bool: " << (doc["bool_value"].is_bool() ? "yes" : "no") << std::endl;
    std::cout << "number_value is number: " << (doc["number_value"].is_number() ? "yes" : "no") << std::endl;
    std::cout << "string_value is string: " << (doc["string_value"].is_string() ? "yes" : "no") << std::endl;
    std::cout << "array_value is array: " << (doc["array_value"].is_array() ? "yes" : "no") << std::endl;
    std::cout << "object_value is object: " << (doc["object_value"].is_object() ? "yes" : "no") << std::endl;
}

// Example 10: Performance benchmark
void benchmark_parsing() {
    std::cout << "\n=== Benchmark: JSON Parsing Performance ===" << std::endl;

    // Generate a large JSON
    std::ostringstream oss;
    oss << "[";
    for (int i = 0; i < 10000; ++i) {
        oss << R"({"id":)" << i << R"(,"name":"User)" << i << R"(","score":)" << (i % 100) << "}";
        if (i < 9999) oss << ",";
    }
    oss << "]";

    std::string large_json = oss.str();
    std::cout << "JSON size: " << large_json.size() << " bytes" << std::endl;

    // Benchmark parsing
    const int iterations = 100;

    auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < iterations; ++i) {
        Document doc = parse(large_json);
        // Access some data to ensure it's not optimized away
        volatile int size = doc.root().as_array().size();
        (void)size;
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Parsed " << iterations << " times in " << duration.count() << "ms" << std::endl;
    std::cout << "Average: " << (duration.count() / static_cast<double>(iterations)) << "ms per parse" << std::endl;
    std::cout << "Throughput: " << ((large_json.size() * iterations) / (1024.0 * 1024.0)) / (duration.count() / 1000.0)
              << " MB/s" << std::endl;
}

// Example 11: Real-world use case - Configuration file
void example_config_file() {
    std::cout << "\n=== Example 11: Configuration File ===" << std::endl;

    std::string config_json = R"({
        "server": {
            "host": "0.0.0.0",
            "port": 8080,
            "ssl": {
                "enabled": true,
                "cert": "/path/to/cert.pem",
                "key": "/path/to/key.pem"
            }
        },
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "myapp",
            "pool_size": 10
        },
        "logging": {
            "level": "info",
            "file": "/var/log/myapp.log"
        }
    })";

    Document config = parse(config_json);

    std::cout << "Server Configuration:" << std::endl;
    std::cout << "  Host: " << config["server"]["host"].as_string() << std::endl;
    std::cout << "  Port: " << config["server"]["port"].as_int() << std::endl;
    std::cout << "  SSL Enabled: " << (config["server"]["ssl"]["enabled"].as_bool() ? "yes" : "no") << std::endl;

    std::cout << "\nDatabase Configuration:" << std::endl;
    std::cout << "  Host: " << config["database"]["host"].as_string() << std::endl;
    std::cout << "  Port: " << config["database"]["port"].as_int() << std::endl;
    std::cout << "  Database: " << config["database"]["name"].as_string() << std::endl;
    std::cout << "  Pool Size: " << config["database"]["pool_size"].as_int() << std::endl;

    std::cout << "\nLogging Configuration:" << std::endl;
    std::cout << "  Level: " << config["logging"]["level"].as_string() << std::endl;
    std::cout << "  File: " << config["logging"]["file"].as_string() << std::endl;
}

int main() {
    std::cout << "=== JsonParser Example Demo ===" << std::endl;

    example_basic_parsing();
    example_array_parsing();
    example_object_iteration();
    example_nested_structures();
    example_sax_parsing();
    example_building_json();
    example_json_pointer();
    example_error_handling();
    example_type_checking();
    benchmark_parsing();
    example_config_file();

    std::cout << "\n=== All examples completed ===" << std::endl;
    return 0;
}
