# Reflection - C++ Compile-Time Reflection

A compile-time reflection system for C++ using template metaprogramming and macros, enabling runtime introspection of types without any runtime overhead for static queries.

## Features
- Enumerate class members at compile-time
- Automatic serialization/deserialization to JSON/XML/Binary
- Type-safe property access by name
- Zero runtime overhead for compile-time queries
- Integration with custom formats
- Visitor pattern implementation
- No external dependencies

## Example
```cpp
REFLECT_CLASS(Person)
    REFLECT_FIELD(name, std::string)
    REFLECT_FIELD(age, int)
    REFLECT_FIELD(email, std::string)
END_REFLECT()

Person p{"Alice", 30, "alice@example.com"};
std::string json = serialize_json(p);
// {"name":"Alice","age":30,"email":"alice@example.com"}
```

## Usage

### Define a Reflectable Class
```cpp
#include "Reflection.hpp"
using namespace reflection;

// Simple class with reflection
REFLECT_CLASS(Person)
    REFLECT_FIELD(name, std::string)
    REFLECT_FIELD(age, int)
    REFLECT_FIELD(active, bool)
END_REFLECT()

// The above macro expands to proper struct definition
// You can now create instances normally:
Person p{"Alice", 30, true};
```

### Access Fields by Name
```cpp
Person p{"Bob", 25, true};

// Get field value by name (compile-time type-safe)
auto name = get_field<"name">(p);  // Returns std::string&
auto age = get_field<"age">(p);    // Returns int&

// Set field value by name
set_field<"name">(p, "Robert");
set_field<"age">(p, 26);
```

### Enumerate Fields
```cpp
Person p{"Charlie", 35, false};

// Iterate over all fields at runtime
for_each_field(p, [](auto&& field_name, auto&& value) {
    std::cout << field_name << ": " << value << std::endl;
});

// Output:
// name: Charlie
// age: 35
// active: 0
```

### JSON Serialization
```cpp
Person p{"Diana", 28, true};

// Serialize to JSON
std::string json = serialize_json(p);
// {"name":"Diana","age":28,"active":true}

// Deserialize from JSON
Person loaded = deserialize_json<Person>(json);
```

### Custom Serialization
```cpp
struct Point {
    double x, y, z;
};

REFLECT_CLASS(Point)
    REFLECT_FIELD(x, double)
    REFLECT_FIELD(y, double)
    REFLECT_FIELD(z, double)
END_REFLECT()

Point pt{1.5, 2.5, 3.5};

// Custom visitor
struct BinarySerializer {
    std::vector<uint8_t> buffer;

    template<typename T>
    void operator()(const char* name, const T& value) {
        // Serialize value to binary
        const uint8_t* bytes = reinterpret_cast<const uint8_t*>(&value);
        buffer.insert(buffer.end(), bytes, bytes + sizeof(T));
    }
};

BinarySerializer serializer;
visit_fields(pt, serializer);
// serializer.buffer now contains binary data
```

### Nested Structures
```cpp
REFLECT_CLASS(Address)
    REFLECT_FIELD(street, std::string)
    REFLECT_FIELD(city, std::string)
    REFLECT_FIELD(zip, int)
END_REFLECT()

REFLECT_CLASS(Employee)
    REFLECT_FIELD(name, std::string)
    REFLECT_FIELD(id, int)
    REFLECT_FIELD(address, Address)
END_REFLECT()

Employee emp{
    "John Doe",
    12345,
    {"123 Main St", "New York", 10001}
};

std::string json = serialize_json(emp);
// {
//   "name":"John Doe",
//   "id":12345,
//   "address":{"street":"123 Main St","city":"New York","zip":10001}
// }
```

### Array and Vector Support
```cpp
REFLECT_CLASS(Team)
    REFLECT_FIELD(name, std::string)
    REFLECT_FIELD(scores, std::vector<int>)
END_REFLECT()

Team team{"Champions", {95, 87, 92, 88}};
std::string json = serialize_json(team);
// {"name":"Champions","scores":[95,87,92,88]}
```

## API Reference

### Macros

**REFLECT_CLASS(ClassName)**
- Begins reflection definition for a class
- Must be followed by REFLECT_FIELD declarations
- Must end with END_REFLECT()

**REFLECT_FIELD(field_name, type)**
- Declares a reflectable field
- `field_name`: Name of the field
- `type`: C++ type of the field

**END_REFLECT()**
- Ends reflection definition
- Generates necessary reflection metadata

### Functions

**get_field<"name">(object)**
- Get field value by name (compile-time checked)
- Returns reference to field
- Type-safe

**set_field<"name">(object, value)**
- Set field value by name
- Compile-time type checking
- Perfect forwarding

**for_each_field(object, callback)**
- Iterate over all fields
- Callback: `void(const char* name, auto&& value)`
- Runtime enumeration

**visit_fields(object, visitor)**
- Visit all fields with custom visitor
- Visitor must have `operator()(const char*, const T&)`
- Supports custom serialization

**field_count<Type>()**
- Get number of fields (compile-time)
- Returns constexpr size_t

**field_name<Type, Index>()**
- Get field name by index (compile-time)
- Returns const char*

**has_field<Type, "name">()**
- Check if type has field (compile-time)
- Returns constexpr bool

### Serialization

**serialize_json(object)**
- Serialize object to JSON string
- Handles nested objects
- Supports arrays/vectors

**deserialize_json<Type>(json_string)**
- Deserialize JSON to object
- Type-safe parsing
- Throws on invalid JSON

**serialize_xml(object)**
- Serialize object to XML string
- Nested structure support

**serialize_binary(object)**
- Serialize to binary format
- Fixed-size types only
- Fast and compact

## Building

### As Header-Only Library
Simply include the reflection header:

```cpp
#include "Reflection.hpp"
```

### With CMake
```bash
cd Reflection
mkdir build && cd build
cmake ..
cmake --build .
./reflection_example
```

## How It Works

The reflection system uses several C++ techniques:

1. **Macros** - Generate boilerplate code
2. **Templates** - Type-safe field access
3. **Variadic Templates** - Iterate over fields
4. **Compile-Time Strings** - Field names
5. **Type Traits** - Type introspection

### Generated Code Example

```cpp
REFLECT_CLASS(Point)
    REFLECT_FIELD(x, double)
    REFLECT_FIELD(y, double)
END_REFLECT()

// Expands to approximately:
struct Point {
    double x;
    double y;

    // Reflection metadata (simplified)
    static constexpr size_t field_count = 2;
    static constexpr const char* field_names[] = {"x", "y"};
    // ... additional metadata
};
```

## Use Cases

The Reflection system is ideal for:
- **Serialization** - JSON, XML, Binary formats
- **Database ORMs** - Map objects to database rows
- **GUI Bindings** - Automatic form generation
- **Configuration** - Load/save app settings
- **Network Protocols** - Message serialization
- **Testing** - Automatic test data generation
- **Debugging** - Runtime object inspection

## Limitations

- Requires macro definitions for each class
- Only public fields are reflected
- Limited support for complex templates
- No reflection of methods (fields only)
- C++20 required for some features

## Performance

- **Compile-time overhead**: Increased compile time due to metaprogramming
- **Runtime overhead**: Zero for compile-time queries
- **Runtime enumeration**: Minimal (function pointer indirection)
- **Serialization**: Comparable to hand-written code

## Requirements
- C++20 compatible compiler (for template string literals)
- Standard library with `<type_traits>`, `<tuple>` support
- No external dependencies

## Thread Safety
- Reflection metadata is immutable (thread-safe)
- Object access follows normal C++ rules
- Serialization functions are thread-safe if objects don't change

## Compatibility
- **GCC 10+**: Full support
- **Clang 10+**: Full support
- **MSVC 2019+**: Full support
- **C++17 Mode**: Limited support (no string literals as template parameters)
