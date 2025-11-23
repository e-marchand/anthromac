# ConfigParser - INI/TOML/YAML Configuration Parser

A C++20 header-only configuration file parser supporting INI, TOML, and YAML formats with a unified API.

## Features

- **Multiple Formats**: Support for INI, TOML (subset), and YAML (subset)
- **Unified API**: Same interface for all formats
- **Type Safety**: Type-safe value retrieval with conversion
- **Sections/Tables**: Support for nested configuration
- **Comments**: Preserve and handle comments in all formats
- **Auto-Detection**: Automatic format detection from file extension
- **Writing**: Generate config files in any supported format
- **Environment Variables**: Support for environment variable expansion

## Supported Formats

### INI Format
```ini
# Comment
[section]
key = value
number = 42
flag = true
```

### TOML Format (Subset)
```toml
# Comment
[section]
key = "value"
number = 42
flag = true

[section.subsection]
nested = "data"
```

### YAML Format (Subset)
```yaml
# Comment
section:
  key: value
  number: 42
  flag: true
  subsection:
    nested: data
```

## Usage

### Reading Configuration

```cpp
#include "ConfigParser.hpp"
using namespace config;

// Auto-detect format from extension
Config cfg = ConfigParser::parse_file("config.ini");

// Get values with type conversion
std::string name = cfg.get<std::string>("database.host");
int port = cfg.get<int>("database.port");
bool enabled = cfg.get<bool>("features.logging");

// Get with default value
int timeout = cfg.get<int>("timeout", 30);
```

### Explicit Format

```cpp
// Parse specific format
Config ini = ConfigParser::parse_ini("config.ini");
Config toml = ConfigParser::parse_toml("config.toml");
Config yaml = ConfigParser::parse_yaml("config.yaml");
```

### Writing Configuration

```cpp
Config cfg;

cfg.set("database.host", "localhost");
cfg.set("database.port", 5432);
cfg.set("features.logging", true);

// Write to file
ConfigParser::write_file(cfg, "output.ini", Format::INI);
ConfigParser::write_file(cfg, "output.toml", Format::TOML);
ConfigParser::write_file(cfg, "output.yaml", Format::YAML);
```

### Nested Values

```cpp
Config cfg = ConfigParser::parse_file("config.toml");

// Access nested values with dot notation
std::string value = cfg.get<std::string>("server.database.host");

// Or use sections
auto db_section = cfg.section("server.database");
std::string host = db_section.get<std::string>("host");
int port = db_section.get<int>("port");
```

### Iterating Sections

```cpp
Config cfg = ConfigParser::parse_file("config.ini");

// Iterate all sections
for (const auto& section_name : cfg.sections()) {
    std::cout << "Section: " << section_name << "\n";

    auto section = cfg.section(section_name);
    for (const auto& [key, value] : section.all()) {
        std::cout << "  " << key << " = " << value << "\n";
    }
}
```

## API Reference

### ConfigParser Class

**Static Methods:**
```cpp
static Config parse_file(const std::string& filename)
static Config parse_ini(const std::string& filename)
static Config parse_toml(const std::string& filename)
static Config parse_yaml(const std::string& filename)

static Config parse_string(const std::string& content, Format format)

static void write_file(const Config& cfg, const std::string& filename, Format format)
static std::string to_string(const Config& cfg, Format format)
```

### Config Class

**Value Access:**
```cpp
template<typename T>
T get(const std::string& key) const

template<typename T>
T get(const std::string& key, const T& default_value) const

bool has(const std::string& key) const
```

**Value Modification:**
```cpp
template<typename T>
void set(const std::string& key, const T& value)

void remove(const std::string& key)
```

**Section Access:**
```cpp
Config section(const std::string& name) const
std::vector<std::string> sections() const
std::map<std::string, std::string> all() const
```

### Supported Types

Type conversions supported:
- `std::string`
- `int`, `long`, `long long`
- `float`, `double`
- `bool` (true/false, yes/no, 1/0)
- `std::vector<T>` (arrays)

## Examples

### Example 1: Database Configuration

Config file `database.ini`:
```ini
[database]
host = localhost
port = 5432
username = admin
password = secret
pool_size = 10
```

Code:
```cpp
Config cfg = ConfigParser::parse_file("database.ini");

std::string host = cfg.get<std::string>("database.host");
int port = cfg.get<int>("database.port");
std::string user = cfg.get<std::string>("database.username");
int pool = cfg.get<int>("database.pool_size");

std::cout << "Connecting to " << host << ":" << port << "\n";
```

### Example 2: Application Settings (TOML)

Config file `app.toml`:
```toml
[app]
name = "MyApp"
version = "1.0.0"

[app.logging]
level = "info"
file = "/var/log/app.log"

[app.features]
authentication = true
rate_limiting = false
```

Code:
```cpp
Config cfg = ConfigParser::parse_toml("app.toml");

std::string app_name = cfg.get<std::string>("app.name");
std::string log_level = cfg.get<std::string>("app.logging.level");
bool auth = cfg.get<bool>("app.features.authentication");

std::cout << app_name << " - Log Level: " << log_level << "\n";
```

### Example 3: Server Configuration (YAML)

Config file `server.yaml`:
```yaml
server:
  host: 0.0.0.0
  port: 8080
  workers: 4

database:
  host: localhost
  port: 5432
  name: mydb
```

Code:
```cpp
Config cfg = ConfigParser::parse_yaml("server.yaml");

std::string host = cfg.get<std::string>("server.host");
int port = cfg.get<int>("server.port");
int workers = cfg.get<int>("server.workers");

std::cout << "Server: " << host << ":" << port
          << " (workers: " << workers << ")\n";
```

### Example 4: Creating Configuration

```cpp
Config cfg;

// Set values
cfg.set("app.name", "MyApp");
cfg.set("app.version", "1.0.0");
cfg.set("server.port", 8080);
cfg.set("server.enabled", true);

// Write to different formats
ConfigParser::write_file(cfg, "config.ini", Format::INI);
ConfigParser::write_file(cfg, "config.toml", Format::TOML);
ConfigParser::write_file(cfg, "config.yaml", Format::YAML);
```

### Example 5: Default Values

```cpp
Config cfg = ConfigParser::parse_file("config.ini");

// Get with defaults
int port = cfg.get<int>("server.port", 8080);
std::string host = cfg.get<std::string>("server.host", "localhost");
bool debug = cfg.get<bool>("debug", false);

std::cout << "Port: " << port << " (default: 8080)\n";
```

### Example 6: Environment Variables

```cpp
Config cfg = ConfigParser::parse_file("config.ini");

// Expand environment variables
cfg.expand_env_vars();

// ${HOME} and $USER will be replaced
std::string path = cfg.get<std::string>("paths.home");
```

## Format Specifics

### INI Format

**Supported:**
- Sections `[section]`
- Key-value pairs `key = value`
- Comments `# comment` or `; comment`
- Quoted strings `key = "value with spaces"`

**Limitations:**
- No nested sections (use dot notation instead)
- No arrays
- Simple values only

### TOML Format (Subset)

**Supported:**
- Tables `[table]`
- Nested tables `[table.subtable]`
- Key-value pairs
- Strings, integers, floats, booleans
- Comments `# comment`

**Not Supported:**
- Arrays of tables
- Inline tables
- Dates/times
- Multi-line strings

### YAML Format (Subset)

**Supported:**
- Nested mappings
- Key-value pairs
- Strings, integers, floats, booleans
- Comments `# comment`
- Indentation-based structure

**Not Supported:**
- Lists/sequences
- Anchors and aliases
- Multi-line strings
- Complex types

## Best Practices

**For INI:**
```ini
[database]
host = localhost
port = 5432

[logging]
level = info
file = /var/log/app.log
```

**For TOML:**
```toml
[database]
host = "localhost"
port = 5432

[database.pool]
min_size = 5
max_size = 20
```

**For YAML:**
```yaml
database:
  host: localhost
  port: 5432
  pool:
    min_size: 5
    max_size: 20
```

## Error Handling

```cpp
try {
    Config cfg = ConfigParser::parse_file("config.ini");

    int port = cfg.get<int>("server.port");

} catch (const ConfigError& e) {
    std::cerr << "Config error: " << e.what() << "\n";
} catch (const std::invalid_argument& e) {
    std::cerr << "Type conversion error: " << e.what() << "\n";
}
```

## Thread Safety

- Parser instances are thread-safe (stateless)
- Config objects are **not** thread-safe for modifications
- Multiple readers: OK
- Concurrent modification: requires external synchronization

## Performance

- Parsing: ~10 MB/s for typical config files
- Memory: Proportional to config size
- Small files (<100KB): Parse in <10ms

## Building

### As Header-Only Library

```cpp
#include "ConfigParser.hpp"
```

### With CMake

```bash
cd ConfigParser
mkdir build && cd build
cmake ..
cmake --build .
./config_example
```

## Use Cases

- **Application Configuration**: Settings and preferences
- **Server Configuration**: Web server, database settings
- **Build Configuration**: Project settings, compiler flags
- **Feature Flags**: Enable/disable features
- **Localization**: Language and regional settings
- **Database Connection**: Connection strings and pools

## Requirements

- C++20 compatible compiler
- Standard library
- No external dependencies

## License

MIT License
