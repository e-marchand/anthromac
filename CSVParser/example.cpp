#include "CSVParser.hpp"
#include <iostream>
#include <iomanip>
#include <fstream>

using namespace csv;

void print_section(const std::string& title) {
    std::cout << "\n=== " << title << " ===" << std::endl;
}

void create_sample_csv() {
    std::ofstream file("sample.csv");
    file << "Name,Age,City,Salary\n";
    file << "Alice,30,New York,75000.50\n";
    file << "Bob,25,San Francisco,65000.00\n";
    file << "Charlie,35,Boston,85000.75\n";
    file.close();
}

void create_quoted_csv() {
    std::ofstream file("quoted.csv");
    file << "Name,Description,Notes\n";
    file << "\"Smith, John\",\"Software Engineer, Senior\",Active\n";
    file << "\"Doe, Jane\",\"Manager, \"\"Sales\"\" Department\",\"On leave\"\n";
    file.close();
}

void example_basic_reading() {
    print_section("Example 1: Basic CSV Reading");

    create_sample_csv();

    CSVParser parser("sample.csv", CSVOptions().with_header());

    std::cout << "Headers: ";
    for (const auto& header : parser.headers()) {
        std::cout << header << " ";
    }
    std::cout << "\n\n";

    for (const auto& row : parser) {
        std::cout << "Name: " << row.get("Name")
                  << ", Age: " << row.get("Age")
                  << ", City: " << row.get("City")
                  << ", Salary: " << row.get("Salary") << "\n";
    }
}

void example_type_conversion() {
    print_section("Example 2: Type Conversion");

    create_sample_csv();

    CSVParser parser("sample.csv", CSVOptions().with_header());

    for (const auto& row : parser) {
        std::string name = row.get<std::string>("Name");
        int age = row.get<int>("Age");
        double salary = row.get<double>("Salary");

        std::cout << name << " (" << age << " years old) earns $"
                  << std::fixed << std::setprecision(2) << salary << "\n";
    }
}

void example_quoted_fields() {
    print_section("Example 3: Quoted Fields");

    create_quoted_csv();

    CSVParser parser("quoted.csv", CSVOptions().with_header());

    for (const auto& row : parser) {
        std::cout << "Name: " << row.get("Name") << "\n";
        std::cout << "  Description: " << row.get("Description") << "\n";
        std::cout << "  Notes: " << row.get("Notes") << "\n\n";
    }
}

void example_writing_csv() {
    print_section("Example 4: Writing CSV");

    CSVWriter writer("output.csv");

    // Write header
    writer.write_row({"ID", "Product", "Price", "In Stock"});

    // Write data
    writer.write_row({"1", "Widget", "9.99", "true"});
    writer.write_row({"2", "Gadget, deluxe", "19.99", "false"});
    writer.write_row({"3", "Thing", "4.99", "true"});

    writer.close();

    std::cout << "Created output.csv\n";

    // Read it back
    std::cout << "\nContents:\n";
    CSVParser parser("output.csv", CSVOptions().with_header());

    for (const auto& row : parser) {
        std::cout << "ID: " << row.get("ID")
                  << ", Product: " << row.get("Product")
                  << ", Price: $" << row.get("Price")
                  << ", In Stock: " << row.get("In Stock") << "\n";
    }
}

void example_custom_delimiter() {
    print_section("Example 5: Custom Delimiter (TSV)");

    // Create tab-separated file
    std::ofstream tsv("data.tsv");
    tsv << "Name\tAge\tCity\n";
    tsv << "Alice\t30\tNew York\n";
    tsv << "Bob\t25\tSan Francisco\n";
    tsv.close();

    CSVOptions opts;
    opts.delimiter('\t').with_header();

    CSVParser parser("data.tsv", opts);

    for (const auto& row : parser) {
        std::cout << row.get("Name") << " from " << row.get("City") << "\n";
    }
}

void example_skip_empty_rows() {
    print_section("Example 6: Skip Empty Rows");

    // Create CSV with empty rows
    std::ofstream file("with_empty.csv");
    file << "Name,Value\n";
    file << "Alice,100\n";
    file << "\n";  // Empty row
    file << "Bob,200\n";
    file << "\n";  // Empty row
    file << "Charlie,300\n";
    file.close();

    CSVOptions opts;
    opts.with_header().skip_empty_rows(true);

    CSVParser parser("with_empty.csv", opts);

    int count = 0;
    for (const auto& row : parser) {
        count++;
        std::cout << "Row " << count << ": " << row.get("Name")
                  << " = " << row.get("Value") << "\n";
    }
}

void example_trim_whitespace() {
    print_section("Example 7: Trim Whitespace");

    // Create CSV with whitespace
    std::ofstream file("whitespace.csv");
    file << "Name,Value\n";
    file << "  Alice  ,  100  \n";
    file << "Bob,200\n";
    file.close();

    std::cout << "Without trimming:\n";
    CSVParser parser1("whitespace.csv", CSVOptions().with_header());
    for (const auto& row : parser1) {
        std::cout << "[" << row.get("Name") << "] = [" << row.get("Value") << "]\n";
    }

    std::cout << "\nWith trimming:\n";
    CSVParser parser2("whitespace.csv", CSVOptions().with_header().trim_whitespace(true));
    for (const auto& row : parser2) {
        std::cout << "[" << row.get("Name") << "] = [" << row.get("Value") << "]\n";
    }
}

void example_stream_parsing() {
    print_section("Example 8: Stream Parsing");

    std::istringstream ss("Name,Age\nAlice,30\nBob,25\nCharlie,35");

    CSVParser parser(ss, CSVOptions().with_header());

    for (const auto& row : parser) {
        std::cout << row.get("Name") << " is " << row.get("Age") << " years old\n";
    }
}

void example_stream_writing() {
    print_section("Example 9: Stream Writing");

    std::ostringstream ss;
    CSVWriter writer(ss);

    writer.write_row({"A", "B", "C"});
    writer.write_row({"1", "2", "3"});
    writer.write_row({"x", "y", "z"});

    std::string csv = ss.str();
    std::cout << "Generated CSV:\n" << csv << std::endl;
}

void example_iterator_usage() {
    print_section("Example 10: Iterator Usage");

    create_sample_csv();

    CSVParser parser("sample.csv", CSVOptions().with_header());

    auto it = parser.begin();
    auto end = parser.end();

    int row_num = 1;
    while (it != end) {
        std::cout << "Row " << row_num++ << ": ";
        for (const auto& field : *it) {
            std::cout << field << " ";
        }
        std::cout << "\n";
        ++it;
    }
}

void example_error_handling() {
    print_section("Example 11: Error Handling");

    create_sample_csv();

    try {
        CSVParser parser("sample.csv", CSVOptions().with_header());

        for (const auto& row : parser) {
            // Valid conversion
            int age = row.get<int>("Age");
            std::cout << "Age: " << age << "\n";

            // This will throw - trying to convert name to int
            try {
                int name = row.get<int>("Name");
                std::cout << "Name as int: " << name << "\n";
            } catch (const std::invalid_argument& e) {
                std::cout << "Expected error: Cannot convert Name to int\n";
            }

            break;  // Just show first row
        }
    } catch (const CSVError& e) {
        std::cerr << "CSV Error: " << e.what() << "\n";
    }

    // Non-existent file
    try {
        CSVParser parser("nonexistent.csv");
    } catch (const CSVError& e) {
        std::cout << "Expected error: " << e.what() << "\n";
    }
}

void example_calculation() {
    print_section("Example 12: Data Calculation");

    create_sample_csv();

    CSVParser parser("sample.csv", CSVOptions().with_header());

    double total_salary = 0.0;
    int count = 0;

    for (const auto& row : parser) {
        total_salary += row.get<double>("Salary");
        count++;
    }

    double average = total_salary / count;

    std::cout << "Total employees: " << count << "\n";
    std::cout << "Total salary: $" << std::fixed << std::setprecision(2) << total_salary << "\n";
    std::cout << "Average salary: $" << average << "\n";
}

void example_filtering() {
    print_section("Example 13: Filtering Data");

    create_sample_csv();

    CSVParser parser("sample.csv", CSVOptions().with_header());

    std::cout << "Employees older than 28:\n";

    for (const auto& row : parser) {
        int age = row.get<int>("Age");
        if (age > 28) {
            std::cout << "  " << row.get("Name") << " (" << age << ")\n";
        }
    }
}

void example_transformation() {
    print_section("Example 14: Data Transformation");

    create_sample_csv();

    // Read from one CSV
    CSVParser parser("sample.csv", CSVOptions().with_header());

    // Write transformed data to another
    CSVWriter writer("transformed.csv");
    writer.write_row({"Name", "Age Group", "Annual Salary"});

    for (const auto& row : parser) {
        std::string name = row.get<std::string>("Name");
        int age = row.get<int>("Age");
        double salary = row.get<double>("Salary");

        std::string age_group = (age < 30) ? "Young" : "Senior";
        std::string annual = std::to_string(static_cast<int>(salary));

        writer.write_row({name, age_group, annual});
    }

    writer.close();

    std::cout << "Created transformed.csv\n";

    // Show result
    CSVParser result("transformed.csv", CSVOptions().with_header());
    for (const auto& row : result) {
        std::cout << row.get("Name") << " - " << row.get("Age Group")
                  << " - $" << row.get("Annual Salary") << "\n";
    }
}

void example_multiline_fields() {
    print_section("Example 15: Multiline Fields");

    // Create CSV with newlines in fields
    std::ofstream file("multiline.csv");
    file << "Name,Address\n";
    file << "Alice,\"123 Main St\nNew York, NY 10001\"\n";
    file << "Bob,\"456 Oak Ave\nSan Francisco, CA 94102\"\n";
    file.close();

    CSVParser parser("multiline.csv", CSVOptions().with_header());

    for (const auto& row : parser) {
        std::cout << "Name: " << row.get("Name") << "\n";
        std::cout << "Address:\n" << row.get("Address") << "\n\n";
    }
}

void example_semicolon_delimiter() {
    print_section("Example 16: Semicolon Delimiter (European CSV)");

    // Create CSV with semicolon delimiter
    std::ofstream file("european.csv");
    file << "Name;Price;Quantity\n";
    file << "Product A;12.50;100\n";
    file << "Product B;8.99;50\n";
    file.close();

    CSVOptions opts;
    opts.delimiter(';').with_header();

    CSVParser parser("european.csv", opts);

    for (const auto& row : parser) {
        std::cout << row.get("Name") << ": "
                  << row.get("Quantity") << " units @ $"
                  << row.get("Price") << " each\n";
    }
}

void example_bool_conversion() {
    print_section("Example 17: Boolean Conversion");

    std::ofstream file("bool.csv");
    file << "Feature,Enabled\n";
    file << "Feature A,true\n";
    file << "Feature B,false\n";
    file << "Feature C,1\n";
    file << "Feature D,0\n";
    file << "Feature E,yes\n";
    file.close();

    CSVParser parser("bool.csv", CSVOptions().with_header());

    for (const auto& row : parser) {
        std::string feature = row.get<std::string>("Feature");
        bool enabled = row.get<bool>("Enabled");

        std::cout << feature << ": "
                  << (enabled ? "Enabled" : "Disabled") << "\n";
    }
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "      CSVParser - Examples              " << std::endl;
    std::cout << "========================================" << std::endl;

    try {
        example_basic_reading();
        example_type_conversion();
        example_quoted_fields();
        example_writing_csv();
        example_custom_delimiter();
        example_skip_empty_rows();
        example_trim_whitespace();
        example_stream_parsing();
        example_stream_writing();
        example_iterator_usage();
        example_error_handling();
        example_calculation();
        example_filtering();
        example_transformation();
        example_multiline_fields();
        example_semicolon_delimiter();
        example_bool_conversion();

        std::cout << "\n========================================" << std::endl;
        std::cout << "   All examples completed successfully  " << std::endl;
        std::cout << "========================================" << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
