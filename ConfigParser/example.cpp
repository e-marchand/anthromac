#include "ConfigParser.hpp"
#include <iostream>
#include <fstream>

using namespace config;

void print_section(const std::string& title) {
    std::cout << "\n=== " << title << " ===" << std::endl;
}

void create_sample_ini() {
    std::ofstream file("sample.ini");
    file << "# Database configuration\n";
    file << "[database]\n";
    file << "host = localhost\n";
    file << "port = 5432\n";
    file << "username = admin\n";
    file << "pool_size = 10\n\n";
    file << "[logging]\n";
    file << "level = info\n";
    file << "file = /var/log/app.log\n";
    file.close();
}

void create_sample_toml() {
    std::ofstream file("sample.toml");
    file << "# Application configuration\n";
    file << "[app]\n";
    file << "name = \"MyApp\"\n";
    file << "version = \"1.0.0\"\n\n";
    file << "[app.server]\n";
    file << "host = \"0.0.0.0\"\n";
    file << "port = 8080\n";
    file << "workers = 4\n\n";
    file << "[app.features]\n";
    file << "authentication = true\n";
    file << "rate_limiting = false\n";
    file.close();
}

void create_sample_yaml() {
    std::ofstream file("sample.yaml");
    file << "# Server configuration\n";
    file << "server:\n";
    file << "  host: 0.0.0.0\n";
    file << "  port: 8080\n";
    file << "  workers: 4\n";
    file << "database:\n";
    file << "  host: localhost\n";
    file << "  port: 5432\n";
    file << "  name: mydb\n";
    file.close();
}

void example_ini_parsing() {
    print_section("Example 1: INI Parsing");

    create_sample_ini();

    Config cfg = ConfigParser::parse_ini("sample.ini");

    std::string host = cfg.get<std::string>("database.host");
    int port = cfg.get<int>("database.port");
    std::string log_level = cfg.get<std::string>("logging.level");

    std::cout << "Database: " << host << ":" << port << "\n";
    std::cout << "Log level: " << log_level << "\n";
}

void example_toml_parsing() {
    print_section("Example 2: TOML Parsing");

    create_sample_toml();

    Config cfg = ConfigParser::parse_toml("sample.toml");

    std::string name = cfg.get<std::string>("app.name");
    std::string version = cfg.get<std::string>("app.version");
    int port = cfg.get<int>("app.server.port");
    bool auth = cfg.get<bool>("app.features.authentication");

    std::cout << name << " v" << version << "\n";
    std::cout << "Port: " << port << "\n";
    std::cout << "Authentication: " << (auth ? "enabled" : "disabled") << "\n";
}

void example_yaml_parsing() {
    print_section("Example 3: YAML Parsing");

    create_sample_yaml();

    Config cfg = ConfigParser::parse_yaml("sample.yaml");

    std::string host = cfg.get<std::string>("server.host");
    int port = cfg.get<int>("server.port");
    int workers = cfg.get<int>("server.workers");

    std::cout << "Server: " << host << ":" << port << "\n";
    std::cout << "Workers: " << workers << "\n";
}

void example_writing_config() {
    print_section("Example 4: Writing Configuration");

    Config cfg;
    cfg.set("app.name", "MyApp");
    cfg.set("app.version", "1.0.0");
    cfg.set("server.port", 8080);
    cfg.set("server.enabled", true);

    ConfigParser::write_file(cfg, "output.ini", Format::INI);
    ConfigParser::write_file(cfg, "output.toml", Format::TOML);
    ConfigParser::write_file(cfg, "output.yaml", Format::YAML);

    std::cout << "Created output.ini, output.toml, output.yaml\n";
}

void example_default_values() {
    print_section("Example 5: Default Values");

    create_sample_ini();

    Config cfg = ConfigParser::parse_ini("sample.ini");

    int port = cfg.get<int>("server.port", 8080);
    std::string host = cfg.get<std::string>("server.host", "localhost");
    bool debug = cfg.get<bool>("debug", false);

    std::cout << "Server: " << host << ":" << port << "\n";
    std::cout << "Debug: " << (debug ? "on" : "off") << " (default)\n";
}

void example_sections() {
    print_section("Example 6: Section Access");

    create_sample_ini();

    Config cfg = ConfigParser::parse_ini("sample.ini");

    std::cout << "Sections:\n";
    for (const auto& section : cfg.sections()) {
        std::cout << "  [" << section << "]\n";

        auto sec = cfg.section(section);
        for (const auto& [key, value] : sec.all()) {
            std::cout << "    " << key << " = " << value << "\n";
        }
    }
}

void example_type_conversion() {
    print_section("Example 7: Type Conversion");

    Config cfg;
    cfg.set("port", 8080);
    cfg.set("enabled", true);
    cfg.set("timeout", 30.5);

    int port = cfg.get<int>("port");
    bool enabled = cfg.get<bool>("enabled");
    double timeout = cfg.get<double>("timeout");

    std::cout << "Port (int): " << port << "\n";
    std::cout << "Enabled (bool): " << std::boolalpha << enabled << "\n";
    std::cout << "Timeout (double): " << timeout << "\n";
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "     ConfigParser - Examples            " << std::endl;
    std::cout << "========================================" << std::endl;

    try {
        example_ini_parsing();
        example_toml_parsing();
        example_yaml_parsing();
        example_writing_config();
        example_default_values();
        example_sections();
        example_type_conversion();

        std::cout << "\n========================================" << std::endl;
        std::cout << "   All examples completed successfully  " << std::endl;
        std::cout << "========================================" << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
