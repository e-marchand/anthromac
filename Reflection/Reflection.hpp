#pragma once

#include <string>
#include <string_view>
#include <tuple>
#include <type_traits>
#include <utility>
#include <sstream>
#include <vector>
#include <stdexcept>

namespace reflection {

// Helper for compile-time string
template<size_t N>
struct FixedString {
    char data[N];
    static constexpr size_t size = N - 1;

    constexpr FixedString(const char (&str)[N]) {
        for (size_t i = 0; i < N; ++i) {
            data[i] = str[i];
        }
    }

    constexpr operator const char*() const { return data; }
    constexpr const char* c_str() const { return data; }
};

// Field descriptor
template<typename Class, typename FieldType, FixedString Name>
struct Field {
    using class_type = Class;
    using field_type = FieldType;
    static constexpr const char* name = Name.data;

    FieldType Class::*pointer;

    constexpr Field(FieldType Class::*ptr) : pointer(ptr) {}

    FieldType& get(Class& obj) const {
        return obj.*pointer;
    }

    const FieldType& get(const Class& obj) const {
        return obj.*pointer;
    }

    void set(Class& obj, const FieldType& value) const {
        obj.*pointer = value;
    }
};

// Class metadata holder
template<typename T, typename... Fields>
struct ClassMetadata {
    using class_type = T;
    using fields_tuple = std::tuple<Fields...>;

    static constexpr size_t field_count = sizeof...(Fields);

    std::tuple<Fields...> fields;

    constexpr ClassMetadata(Fields... fs) : fields(fs...) {}

    template<size_t Index>
    auto& get_field() {
        return std::get<Index>(fields);
    }

    template<size_t Index>
    const auto& get_field() const {
        return std::get<Index>(fields);
    }
};

// Forward declaration for get_metadata
template<typename T>
constexpr auto get_metadata();

// Helper to check if type has reflection
template<typename T, typename = void>
struct has_reflection : std::false_type {};

template<typename T>
struct has_reflection<T, std::void_t<decltype(get_metadata<T>())>> : std::true_type {};

template<typename T>
inline constexpr bool has_reflection_v = has_reflection<T>::value;

// For-each field visitor
template<typename T, typename Func>
void for_each_field(T& obj, Func&& func) {
    if constexpr (has_reflection_v<T>) {
        constexpr auto metadata = get_metadata<T>();
        std::apply([&](auto&&... fields) {
            (..., func(fields.name, fields.get(obj)));
        }, metadata.fields);
    }
}

template<typename T, typename Func>
void for_each_field(const T& obj, Func&& func) {
    if constexpr (has_reflection_v<T>) {
        constexpr auto metadata = get_metadata<T>();
        std::apply([&](auto&&... fields) {
            (..., func(fields.name, fields.get(obj)));
        }, metadata.fields);
    }
}

// Visit fields with visitor pattern
template<typename T, typename Visitor>
void visit_fields(const T& obj, Visitor& visitor) {
    for_each_field(obj, [&visitor](const char* name, const auto& value) {
        visitor(name, value);
    });
}

// Serialization helpers
namespace detail {

template<typename T>
std::string value_to_json(const T& value) {
    if constexpr (std::is_same_v<T, std::string>) {
        return "\"" + value + "\"";
    } else if constexpr (std::is_same_v<T, bool>) {
        return value ? "true" : "false";
    } else if constexpr (std::is_arithmetic_v<T>) {
        return std::to_string(value);
    } else if constexpr (has_reflection_v<T>) {
        // Nested object
        return serialize_json(value);
    } else {
        return "\"<unsupported>\"";
    }
}

// Forward declaration
template<typename T>
std::string serialize_json(const T& obj);

template<typename T>
std::string value_to_json_impl(const std::vector<T>& vec) {
    std::ostringstream oss;
    oss << "[";
    for (size_t i = 0; i < vec.size(); ++i) {
        oss << value_to_json(vec[i]);
        if (i < vec.size() - 1) oss << ",";
    }
    oss << "]";
    return oss.str();
}

template<typename T>
std::string value_to_json(const std::vector<T>& vec) {
    return value_to_json_impl(vec);
}

} // namespace detail

// JSON serialization
template<typename T>
std::string serialize_json(const T& obj) {
    std::ostringstream oss;
    oss << "{";

    bool first = true;
    for_each_field(obj, [&](const char* name, const auto& value) {
        if (!first) oss << ",";
        first = false;

        oss << "\"" << name << "\":";
        using ValueType = std::decay_t<decltype(value)>;
        oss << detail::value_to_json(value);
    });

    oss << "}";
    return oss.str();
}

// Field count
template<typename T>
constexpr size_t field_count() {
    if constexpr (has_reflection_v<T>) {
        return get_metadata<T>().field_count;
    } else {
        return 0;
    }
}

// Get field name by index
template<typename T, size_t Index>
constexpr const char* field_name() {
    if constexpr (has_reflection_v<T> && Index < field_count<T>()) {
        constexpr auto metadata = get_metadata<T>();
        return std::get<Index>(metadata.fields).name;
    } else {
        return nullptr;
    }
}

} // namespace reflection

// Macro system for easy reflection definition

#define REFLECT_CLASS(ClassName) \
    struct ClassName { \
        using _reflection_class_type = ClassName;

#define REFLECT_FIELD(field_name, field_type) \
        field_type field_name{};

#define END_REFLECT() \
    }; \
    namespace reflection { \
    template<> \
    constexpr auto get_metadata<_reflection_class_type>() { \
        return _make_metadata_##_reflection_class_type(); \
    } \
    } \
    static constexpr auto _make_metadata_##_reflection_class_type()

// Helper macro to build field descriptors
#define REFLECT_FIELD_DESCRIPTOR(ClassName, field_name, field_type) \
    reflection::Field<ClassName, field_type, #field_name>(&ClassName::field_name)

// Manual metadata definition helper
#define BEGIN_METADATA(ClassName) \
    namespace reflection { \
    template<> \
    constexpr auto get_metadata<ClassName>() { \
        using Class = ClassName; \
        return ClassMetadata{

#define METADATA_FIELD(field_name, field_type) \
            Field<Class, field_type, #field_name>(&Class::field_name)

#define END_METADATA() \
        }; \
    } \
    }

// Simpler reflection system using REFLECT macro
#define REFLECT(...) \
    static constexpr auto _make_metadata() { \
        using Class = std::remove_reference_t<decltype(*this)>; \
        return ::reflection::ClassMetadata{ \
            __VA_ARGS__ \
        }; \
    }

#define FIELD(name, type) \
    type name{}; \
    static inline constexpr auto _field_##name = \
        ::reflection::Field<_reflection_class_type, type, #name>(&_reflection_class_type::name)

// Alternative macro system with cleaner syntax
#define REFLECTABLE_STRUCT(Name, ...) \
    struct Name { \
        using _reflection_class_type = Name; \
        __VA_ARGS__ \
    }; \
    namespace reflection { \
    template<> \
    constexpr auto get_metadata<Name>() { \
        using Class = Name; \
        return Name::_make_metadata(); \
    } \
    }

#endif // REFLECTION_HPP
