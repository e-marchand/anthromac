#include "TemplateEngine.hpp"
#include <iostream>
#include <fstream>

using namespace tmpl;

void print_section(const std::string& title) {
    std::cout << "\n=== " << title << " ===" << std::endl;
}

void example_simple_variables() {
    print_section("Example 1: Simple Variables");

    TemplateEngine engine;

    std::string tmpl = "Hello, {{ name }}! You are {{ age }} years old.";

    Context ctx;
    ctx.set("name", "Alice");
    ctx.set("age", 30);

    std::string result = engine.render(tmpl, ctx);
    std::cout << result << std::endl;
}

void example_conditionals() {
    print_section("Example 2: Conditionals");

    TemplateEngine engine;

    std::string tmpl = R"(
{% if logged_in %}
Welcome back, {{ username }}!
{% else %}
Please log in.
{% endif %}
)";

    Context ctx1;
    ctx1.set("logged_in", true);
    ctx1.set("username", "Alice");

    std::cout << "Logged in:\n" << engine.render(tmpl, ctx1) << "\n";

    Context ctx2;
    ctx2.set("logged_in", false);

    std::cout << "Not logged in:\n" << engine.render(tmpl, ctx2) << std::endl;
}

void example_loops() {
    print_section("Example 3: Loops");

    TemplateEngine engine;

    std::string tmpl = R"(<ul>
{% for product in products %}
  <li>{{ product.name }}: ${{ product.price }}</li>
{% endfor %}
</ul>)";

    Context ctx;

    std::vector<Context> products;

    Context p1;
    p1.set("name", "Widget");
    p1.set("price", "9.99");
    products.push_back(p1);

    Context p2;
    p2.set("name", "Gadget");
    p2.set("price", "19.99");
    products.push_back(p2);

    Context p3;
    p3.set("name", "Thing");
    p3.set("price", "4.99");
    products.push_back(p3);

    ctx.set_array("products", products);

    std::string result = engine.render(tmpl, ctx);
    std::cout << result << std::endl;
}

void example_filters() {
    print_section("Example 4: Filters");

    TemplateEngine engine;

    std::string tmpl = R"(
Original: {{ name }}
Upper: {{ name | upper }}
Lower: {{ name | lower }}
Title: {{ name | title }}
Capitalized: {{ name | capitalize }}
)";

    Context ctx;
    ctx.set("name", "alice smith");

    std::string result = engine.render(tmpl, ctx);
    std::cout << result << std::endl;
}

void example_custom_filter() {
    print_section("Example 5: Custom Filter");

    TemplateEngine engine;

    // Register custom filter
    engine.register_filter("reverse", [](const std::string& value) {
        std::string reversed = value;
        std::reverse(reversed.begin(), reversed.end());
        return reversed;
    });

    std::string tmpl = "{{ text }} reversed is {{ text | reverse }}";

    Context ctx;
    ctx.set("text", "Hello");

    std::string result = engine.render(tmpl, ctx);
    std::cout << result << std::endl;
}

void example_html_page() {
    print_section("Example 6: HTML Page");

    TemplateEngine engine;

    std::string tmpl = R"(<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <p>{{ content }}</p>

    {% if show_footer %}
    <footer>© 2024 {{ company }}</footer>
    {% endif %}
</body>
</html>)";

    Context ctx;
    ctx.set("title", "My Page");
    ctx.set("heading", "Welcome");
    ctx.set("content", "This is a sample page generated from a template.");
    ctx.set("show_footer", true);
    ctx.set("company", "ACME Corp");

    std::string html = engine.render(tmpl, ctx);
    std::cout << html << std::endl;
}

void example_comments() {
    print_section("Example 7: Comments");

    TemplateEngine engine;

    std::string tmpl = R"(
Hello, {{ name }}!
{# This is a comment and won't appear #}
Your status: {{ status }}
)";

    Context ctx;
    ctx.set("name", "Bob");
    ctx.set("status", "Active");

    std::string result = engine.render(tmpl, ctx);
    std::cout << result << std::endl;
}

void example_nested_context() {
    print_section("Example 8: Nested Context");

    TemplateEngine engine;

    std::string tmpl = R"(
User: {{ user.name }}
Email: {{ user.email }}
Admin: {{ user.admin }}
)";

    Context user;
    user.set("name", "Alice");
    user.set("email", "alice@example.com");
    user.set("admin", true);

    Context ctx;
    ctx.set_context("user", user);

    std::string result = engine.render(tmpl, ctx);
    std::cout << result << std::endl;
}

void example_html_escaping() {
    print_section("Example 9: HTML Escaping");

    TemplateEngine engine;

    std::string tmpl = "User input: {{ user_input }}";

    Context ctx;
    ctx.set("user_input", "<script>alert('xss')</script>");

    std::string result = engine.render(tmpl, ctx);
    std::cout << result << std::endl;
    std::cout << "(HTML entities are escaped for safety)" << std::endl;
}

void example_product_list() {
    print_section("Example 10: Product List with Conditionals");

    TemplateEngine engine;

    std::string tmpl = R"(<h1>Products</h1>
<ul>
{% for product in products %}
  <li>
    <strong>{{ product.name | upper }}</strong> - ${{ product.price }}
    {% if product.sale %}
    <span class="sale">ON SALE!</span>
    {% endif %}
  </li>
{% endfor %}
</ul>)";

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

    Context p3;
    p3.set("name", "Thing");
    p3.set("price", "4.99");
    p3.set("sale", false);
    products.push_back(p3);

    ctx.set_array("products", products);

    std::string html = engine.render(tmpl, ctx);
    std::cout << html << std::endl;
}

void example_email_template() {
    print_section("Example 11: Email Template");

    TemplateEngine engine;

    std::string email_tmpl = R"(Dear {{ customer.name | title }},

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
{{ company.name }})";

    Context ctx;
    ctx.set("customer.name", "john doe");
    ctx.set("order.id", "12345");
    ctx.set("order.total", "99.99");
    ctx.set("order.discount", "10.00");
    ctx.set("company.name", "ACME Corp");

    std::vector<Context> items;

    Context item1;
    item1.set("name", "Widget");
    item1.set("quantity", "2");
    item1.set("price", "9.99");
    items.push_back(item1);

    Context item2;
    item2.set("name", "Gadget");
    item2.set("quantity", "1");
    item2.set("price", "19.99");
    items.push_back(item2);

    ctx.set_array("order.items", items);

    std::string email = engine.render(email_tmpl, ctx);
    std::cout << email << std::endl;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "    TemplateEngine - Examples           " << std::endl;
    std::cout << "========================================" << std::endl;

    try {
        example_simple_variables();
        example_conditionals();
        example_loops();
        example_filters();
        example_custom_filter();
        example_html_page();
        example_comments();
        example_nested_context();
        example_html_escaping();
        example_product_list();
        example_email_template();

        std::cout << "\n========================================" << std::endl;
        std::cout << "   All examples completed successfully  " << std::endl;
        std::cout << "========================================" << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
