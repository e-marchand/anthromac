# TemplateEngine - Mustache/Jinja-Style Templating

A C++20 header-only template engine supporting Mustache and Jinja-style syntax for text generation.

## Features

- **Variable Substitution**: `{{ variable }}`
- **Conditionals**: `{% if condition %} ... {% endif %}`
- **Loops**: `{% for item in list %} ... {% endfor %}`
- **Filters**: `{{ variable | filter }}`
- **Comments**: `{# comment #}`
- **Partials/Includes**: `{% include "partial.html" %}`
- **Safe HTML Escaping**: Automatic HTML entity escaping
- **Custom Filters**: Register custom filter functions
- **Nested Templates**: Support for template inheritance

## Syntax

### Variables

```html
Hello, {{ name }}!
Your age is {{ age }}.
```

### Conditionals

```html
{% if logged_in %}
  Welcome back, {{ username }}!
{% else %}
  Please log in.
{% endif %}
```

### Loops

```html
<ul>
{% for item in items %}
  <li>{{ item.name }} - ${{ item.price }}</li>
{% endfor %}
</ul>
```

### Filters

```html
{{ name | upper }}
{{ price | format_currency }}
{{ text | truncate(50) }}
```

### Comments

```html
{# This is a comment and won't appear in output #}
```

## Usage

### Basic Example

```cpp
#include "TemplateEngine.hpp"
using namespace tmpl;

TemplateEngine engine;

std::string tmpl = "Hello, {{ name }}!";
Context ctx;
ctx.set("name", "Alice");

std::string result = engine.render(tmpl, ctx);
// Output: "Hello, Alice!"
```

### With Conditionals

```cpp
TemplateEngine engine;

std::string tmpl = R"(
{% if user.admin %}
  Admin Panel
{% else %}
  User Dashboard
{% endif %}
)";

Context ctx;
ctx.set("user.admin", true);

std::string result = engine.render(tmpl, ctx);
```

### With Loops

```cpp
TemplateEngine engine;

std::string tmpl = R"(
<ul>
{% for product in products %}
  <li>{{ product.name }}: ${{ product.price }}</li>
{% endfor %}
</ul>
)";

Context ctx;
ctx.set_array("products", {
    {{"name", "Widget"}, {"price", "9.99"}},
    {{"name", "Gadget"}, {"price", "19.99"}}
});

std::string result = engine.render(tmpl, ctx);
```

### With Filters

```cpp
TemplateEngine engine;

// Register custom filter
engine.register_filter("upper", [](const std::string& value) {
    std::string result = value;
    std::transform(result.begin(), result.end(), result.begin(), ::toupper);
    return result;
});

std::string tmpl = "Hello, {{ name | upper }}!";
Context ctx;
ctx.set("name", "alice");

std::string result = engine.render(tmpl, ctx);
// Output: "Hello, ALICE!"
```

### Loading from File

```cpp
TemplateEngine engine;

Context ctx;
ctx.set("title", "My Page");
ctx.set("content", "Hello, World!");

std::string result = engine.render_file("template.html", ctx);
```

## API Reference

### TemplateEngine Class

**Methods:**
```cpp
std::string render(const std::string& template_str, const Context& ctx)
std::string render_file(const std::string& filename, const Context& ctx)

void register_filter(const std::string& name, FilterFunction func)
void set_template_dir(const std::string& dir)
```

### Context Class

**Value Setting:**
```cpp
void set(const std::string& key, const std::string& value)
void set(const std::string& key, int value)
void set(const std::string& key, double value)
void set(const std::string& key, bool value)

void set_array(const std::string& key, const std::vector<Context>& items)
```

**Value Access:**
```cpp
std::string get(const std::string& key, const std::string& default_val = "")
bool has(const std::string& key)
```

### Built-in Filters

- `upper` - Convert to uppercase
- `lower` - Convert to lowercase
- `capitalize` - Capitalize first letter
- `title` - Title case
- `trim` - Remove whitespace
- `length` - Get string length
- `default(value)` - Use default if empty

## Examples

### Example 1: Simple Page

Template:
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <p>{{ content }}</p>
</body>
</html>
```

Code:
```cpp
TemplateEngine engine;
Context ctx;
ctx.set("title", "My Page");
ctx.set("heading", "Welcome");
ctx.set("content", "Hello, World!");

std::string html = engine.render_file("page.html", ctx);
```

### Example 2: Product List

Template:
```html
<h1>Products</h1>
<ul>
{% for product in products %}
  <li>
    <strong>{{ product.name | upper }}</strong>
    - ${{ product.price }}
    {% if product.sale %}
      <span class="sale">ON SALE!</span>
    {% endif %}
  </li>
{% endfor %}
</ul>
```

Code:
```cpp
TemplateEngine engine;
Context ctx;

std::vector<Context> products;

Context p1;
p1.set("name", "Widget");
p1.set("price", "9.99");
p1.set("sale", false);
products.push_back(p1);

Context p2;
p2.set("name", "Gadget");
p2.set("price", "19.99");
p2.set("sale", true);
products.push_back(p2);

ctx.set_array("products", products);

std::string html = engine.render_file("products.html", ctx);
```

### Example 3: User Profile

Template:
```html
<div class="profile">
  <h2>{{ user.name | title }}</h2>

  {% if user.verified %}
    <span class="badge">✓ Verified</span>
  {% endif %}

  <p>Email: {{ user.email | lower }}</p>
  <p>Member since: {{ user.joined }}</p>

  {% if user.posts %}
    <h3>Recent Posts</h3>
    <ul>
    {% for post in user.posts %}
      <li>{{ post.title }} ({{ post.date }})</li>
    {% endfor %}
    </ul>
  {% else %}
    <p>No posts yet.</p>
  {% endif %}
</div>
```

Code:
```cpp
TemplateEngine engine;
Context ctx;

ctx.set("user.name", "alice smith");
ctx.set("user.email", "ALICE@EXAMPLE.COM");
ctx.set("user.verified", true);
ctx.set("user.joined", "2024-01-01");

std::vector<Context> posts;
Context post1;
post1.set("title", "First Post");
post1.set("date", "2024-01-15");
posts.push_back(post1);

ctx.set_array("user.posts", posts);

std::string html = engine.render_file("profile.html", ctx);
```

### Example 4: Custom Filters

```cpp
TemplateEngine engine;

// Truncate filter
engine.register_filter("truncate", [](const std::string& value, int max_len = 50) {
    if (value.length() <= max_len) return value;
    return value.substr(0, max_len) + "...";
});

// Currency filter
engine.register_filter("currency", [](const std::string& value) {
    return "$" + value;
});

std::string tmpl = R"(
{{ description | truncate(20) }}
Price: {{ price | currency }}
)";

Context ctx;
ctx.set("description", "This is a very long description that needs truncating");
ctx.set("price", "19.99");

std::string result = engine.render(tmpl, ctx);
```

### Example 5: Email Template

```cpp
TemplateEngine engine;

std::string email_tmpl = R"(
Dear {{ customer.name | title }},

Thank you for your order #{{ order.id }}.

Order Summary:
{% for item in order.items %}
  - {{ item.name }}: {{ item.quantity }} x ${{ item.price }}
{% endfor %}

Total: ${{ order.total }}

{% if order.discount %}
You saved ${{ order.discount }} with your discount code!
{% endif %}

Best regards,
{{ company.name }}
)";

Context ctx;
ctx.set("customer.name", "john doe");
ctx.set("order.id", "12345");
ctx.set("order.total", "99.99");
ctx.set("company.name", "ACME Corp");

// ... add order items ...

std::string email = engine.render(email_tmpl, ctx);
```

## Advanced Features

### Nested Contexts

```cpp
Context user;
user.set("name", "Alice");
user.set("role", "admin");

Context ctx;
ctx.set_context("user", user);

// Access: {{ user.name }}
```

### HTML Escaping

```cpp
Context ctx;
ctx.set("unsafe", "<script>alert('xss')</script>");

// {{ unsafe }} outputs: &lt;script&gt;alert('xss')&lt;/script&gt;
// {{ unsafe | raw }} outputs: <script>alert('xss')</script>
```

### Template Inheritance

```cpp
// base.html
std::string base = R"(
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Default Title{% endblock %}</title>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
)";

// child.html
std::string child = R"(
{% extends "base.html" %}
{% block title %}My Page{% endblock %}
{% block content %}<h1>Hello!</h1>{% endblock %}
)";
```

## Error Handling

```cpp
try {
    TemplateEngine engine;
    Context ctx;
    std::string result = engine.render("{{ undefined }}", ctx);
} catch (const TemplateError& e) {
    std::cerr << "Template error: " << e.what() << "\n";
}
```

## Performance

- **Rendering**: ~10 MB/s for typical templates
- **Caching**: Templates can be pre-compiled
- **Memory**: Minimal overhead per context

## Best Practices

**Separate Logic from Templates:**
```cpp
// Good: Prepare data in C++
Context ctx;
ctx.set("total_price", calculate_total(cart));

// Bad: Complex logic in template
// {% for item in cart %}{{ item.price * item.quantity }}{% endfor %}
```

**Use Filters for Formatting:**
```cpp
engine.register_filter("date", format_date);
engine.register_filter("money", format_currency);

// {{ created_at | date }}
// {{ price | money }}
```

## Building

### As Header-Only Library

```cpp
#include "TemplateEngine.hpp"
```

### With CMake

```bash
cd TemplateEngine
mkdir build && cd build
cmake ..
cmake --build .
./template_example
```

## Use Cases

- **Web Pages**: Generate HTML from templates
- **Email Templates**: Send formatted emails
- **Reports**: Generate PDF/HTML reports
- **Code Generation**: Generate source code
- **Documentation**: Generate docs from data
- **Configuration**: Generate config files

## Thread Safety

- Engine instances are thread-safe for rendering
- Context objects are **not** thread-safe
- Create separate contexts per thread

## Requirements

- C++20 compatible compiler
- Standard library
- No external dependencies

## License

MIT License
