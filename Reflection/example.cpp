#include "Reflection.hpp"
#include <iostream>
#include <iomanip>
#include <vector>

using namespace reflection;

// Example 1: Simple struct with reflection
struct Point {
    double x;
    double y;
    double z;
};

BEGIN_METADATA(Point)
    METADATA_FIELD(x, double),
    METADATA_FIELD(y, double),
    METADATA_FIELD(z, double)
END_METADATA()

// Example 2: Person struct
struct Person {
    std::string name;
    int age;
    bool active;
};

BEGIN_METADATA(Person)
    METADATA_FIELD(name, std::string),
    METADATA_FIELD(age, int),
    METADATA_FIELD(active, bool)
END_METADATA()

// Example 3: Nested struct
struct Address {
    std::string street;
    std::string city;
    int zip;
};

BEGIN_METADATA(Address)
    METADATA_FIELD(street, std::string),
    METADATA_FIELD(city, std::string),
    METADATA_FIELD(zip, int)
END_METADATA()

struct Employee {
    std::string name;
    int id;
    Address address;
};

BEGIN_METADATA(Employee)
    METADATA_FIELD(name, std::string),
    METADATA_FIELD(id, int),
    METADATA_FIELD(address, Address)
END_METADATA()

// Example 4: Struct with vector
struct Team {
    std::string name;
    std::vector<int> scores;
};

BEGIN_METADATA(Team)
    METADATA_FIELD(name, std::string),
    METADATA_FIELD(scores, std::vector<int>)
END_METADATA()

// Example demonstrations

void example_basic_reflection() {
    std::cout << "\n=== Example 1: Basic Reflection ===" << std::endl;

    Point p{1.5, 2.5, 3.5};

    std::cout << "Point fields:" << std::endl;
    for_each_field(p, [](const char* name, const auto& value) {
        std::cout << "  " << name << ": " << value << std::endl;
    });

    std::cout << "\nField count: " << field_count<Point>() << std::endl;
    std::cout << "Field names: ";
    std::cout << field_name<Point, 0>() << ", ";
    std::cout << field_name<Point, 1>() << ", ";
    std::cout << field_name<Point, 2>() << std::endl;
}

void example_person() {
    std::cout << "\n=== Example 2: Person Struct ===" << std::endl;

    Person person{"Alice", 30, true};

    std::cout << "Person fields:" << std::endl;
    for_each_field(person, [](const char* name, const auto& value) {
        std::cout << "  " << name << ": ";
        using T = std::decay_t<decltype(value)>;
        if constexpr (std::is_same_v<T, bool>) {
            std::cout << (value ? "true" : "false");
        } else {
            std::cout << value;
        }
        std::cout << std::endl;
    });
}

void example_json_serialization() {
    std::cout << "\n=== Example 3: JSON Serialization ===" << std::endl;

    Person p{"Bob", 25, false};

    std::string json = serialize_json(p);
    std::cout << "JSON output:" << std::endl;
    std::cout << json << std::endl;

    Point point{10.5, 20.5, 30.5};
    std::cout << "\nPoint JSON:" << std::endl;
    std::cout << serialize_json(point) << std::endl;
}

void example_nested_structures() {
    std::cout << "\n=== Example 4: Nested Structures ===" << std::endl;

    Employee emp{
        "John Doe",
        12345,
        {"123 Main St", "New York", 10001}
    };

    std::cout << "Employee JSON:" << std::endl;
    std::string json = serialize_json(emp);
    std::cout << json << std::endl;

    std::cout << "\nFormatted:" << std::endl;
    std::cout << "Name: " << emp.name << std::endl;
    std::cout << "ID: " << emp.id << std::endl;
    std::cout << "Address: " << emp.address.street << ", "
              << emp.address.city << " " << emp.address.zip << std::endl;
}

void example_custom_visitor() {
    std::cout << "\n=== Example 5: Custom Visitor ===" << std::endl;

    struct FieldPrinter {
        int indent = 0;

        void operator()(const char* name, const auto& value) {
            std::cout << std::string(indent * 2, ' ') << name << " = ";

            using T = std::decay_t<decltype(value)>;
            if constexpr (std::is_same_v<T, std::string>) {
                std::cout << "\"" << value << "\"";
            } else if constexpr (std::is_same_v<T, bool>) {
                std::cout << (value ? "true" : "false");
            } else if constexpr (has_reflection_v<T>) {
                std::cout << "{" << std::endl;
                ++indent;
                visit_fields(value, *this);
                --indent;
                std::cout << std::string(indent * 2, ' ') << "}";
            } else {
                std::cout << value;
            }
            std::cout << std::endl;
        }
    };

    Employee emp{
        "Jane Smith",
        54321,
        {"456 Oak Ave", "Boston", 02101}
    };

    FieldPrinter printer;
    visit_fields(emp, printer);
}

void example_vector_support() {
    std::cout << "\n=== Example 6: Vector Support ===" << std::endl;

    Team team{"Champions", {95, 87, 92, 88, 91}};

    std::cout << "Team JSON:" << std::endl;
    std::cout << serialize_json(team) << std::endl;

    std::cout << "\nTeam details:" << std::endl;
    for_each_field(team, [](const char* name, const auto& value) {
        using T = std::decay_t<decltype(value)>;
        std::cout << name << ": ";

        if constexpr (std::is_same_v<T, std::vector<int>>) {
            std::cout << "[ ";
            for (int score : value) {
                std::cout << score << " ";
            }
            std::cout << "]";
        } else {
            std::cout << value;
        }
        std::cout << std::endl;
    });
}

void example_field_count_and_names() {
    std::cout << "\n=== Example 7: Field Introspection ===" << std::endl;

    std::cout << "Point has " << field_count<Point>() << " fields:" << std::endl;
    std::cout << "  0: " << field_name<Point, 0>() << std::endl;
    std::cout << "  1: " << field_name<Point, 1>() << std::endl;
    std::cout << "  2: " << field_name<Point, 2>() << std::endl;

    std::cout << "\nPerson has " << field_count<Person>() << " fields:" << std::endl;
    std::cout << "  0: " << field_name<Person, 0>() << std::endl;
    std::cout << "  1: " << field_name<Person, 1>() << std::endl;
    std::cout << "  2: " << field_name<Person, 2>() << std::endl;

    std::cout << "\nHas reflection:" << std::endl;
    std::cout << "  Point: " << (has_reflection_v<Point> ? "yes" : "no") << std::endl;
    std::cout << "  Person: " << (has_reflection_v<Person> ? "yes" : "no") << std::endl;
    std::cout << "  int: " << (has_reflection_v<int> ? "yes" : "no") << std::endl;
}

void example_multiple_objects() {
    std::cout << "\n=== Example 8: Multiple Objects ===" << std::endl;

    std::vector<Person> people = {
        {"Alice", 30, true},
        {"Bob", 25, false},
        {"Charlie", 35, true},
        {"Diana", 28, true}
    };

    std::cout << "People database (JSON):" << std::endl;
    std::cout << "[" << std::endl;
    for (size_t i = 0; i < people.size(); ++i) {
        std::cout << "  " << serialize_json(people[i]);
        if (i < people.size() - 1) std::cout << ",";
        std::cout << std::endl;
    }
    std::cout << "]" << std::endl;
}

void example_binary_serializer() {
    std::cout << "\n=== Example 9: Binary Serializer ===" << std::endl;

    struct BinarySerializer {
        std::vector<uint8_t> buffer;

        void operator()(const char* name, const auto& value) {
            using T = std::decay_t<decltype(value)>;

            if constexpr (std::is_arithmetic_v<T>) {
                const uint8_t* bytes = reinterpret_cast<const uint8_t*>(&value);
                buffer.insert(buffer.end(), bytes, bytes + sizeof(T));
            } else if constexpr (std::is_same_v<T, std::string>) {
                // Store string length then bytes
                size_t len = value.size();
                const uint8_t* len_bytes = reinterpret_cast<const uint8_t*>(&len);
                buffer.insert(buffer.end(), len_bytes, len_bytes + sizeof(len));
                buffer.insert(buffer.end(), value.begin(), value.end());
            }
        }
    };

    Point p{1.5, 2.5, 3.5};

    BinarySerializer serializer;
    visit_fields(p, serializer);

    std::cout << "Binary size: " << serializer.buffer.size() << " bytes" << std::endl;
    std::cout << "Binary data (hex): ";
    for (uint8_t byte : serializer.buffer) {
        std::cout << std::hex << std::setw(2) << std::setfill('0')
                  << static_cast<int>(byte) << " ";
    }
    std::cout << std::dec << std::endl;
}

void example_conditional_processing() {
    std::cout << "\n=== Example 10: Conditional Processing ===" << std::endl;

    Person p1{"Active User", 30, true};
    Person p2{"Inactive User", 25, false};

    auto process_if_active = [](const Person& p) {
        bool is_active = false;

        for_each_field(p, [&](const char* name, const auto& value) {
            if (std::string(name) == "active") {
                using T = std::decay_t<decltype(value)>;
                if constexpr (std::is_same_v<T, bool>) {
                    is_active = value;
                }
            }
        });

        if (is_active) {
            std::cout << "Processing active user: " << p.name << std::endl;
        } else {
            std::cout << "Skipping inactive user: " << p.name << std::endl;
        }
    };

    process_if_active(p1);
    process_if_active(p2);
}

int main() {
    std::cout << "=== Reflection Library Examples ===" << std::endl;
    std::cout << "Compile-time reflection with zero overhead" << std::endl;

    example_basic_reflection();
    example_person();
    example_json_serialization();
    example_nested_structures();
    example_custom_visitor();
    example_vector_support();
    example_field_count_and_names();
    example_multiple_objects();
    example_binary_serializer();
    example_conditional_processing();

    std::cout << "\n=== All examples completed ===" << std::endl;
    return 0;
}
