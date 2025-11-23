#include "MarkdownParser.hpp"
#include <iostream>
#include <fstream>
#include <iomanip>

using namespace md;

void print_section(const std::string& title) {
    std::cout << "\n=== " << title << " ===" << std::endl;
}

void example_basic_headers() {
    print_section("Example 1: Headers");

    MarkdownParser parser;

    std::string markdown = R"(# H1 Header
## H2 Header
### H3 Header
#### H4 Header
##### H5 Header
###### H6 Header)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_emphasis() {
    print_section("Example 2: Text Emphasis");

    MarkdownParser parser;

    std::string markdown = R"(This is **bold text** and this is *italic text*.

You can also use __bold__ and _italic_ with underscores.

Combine them: ***bold and italic*** together.)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_lists() {
    print_section("Example 3: Lists");

    MarkdownParser parser;

    std::string markdown = R"(Unordered list:
- Item 1
- Item 2
- Item 3

Ordered list:
1. First item
2. Second item
3. Third item)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_links_and_images() {
    print_section("Example 4: Links and Images");

    MarkdownParser parser;

    std::string markdown = R"(Here is a [link to Google](https://www.google.com).

Here is a [link with title](https://example.com "Example Website").

Here is an image: ![Alt text](image.png "Image title"))";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_code() {
    print_section("Example 5: Code");

    MarkdownParser parser;

    std::string markdown = R"(Inline code: Use the `print()` function.

Code block:
```cpp
int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
```)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_blockquotes() {
    print_section("Example 6: Blockquotes");

    MarkdownParser parser;

    std::string markdown = R"(> This is a blockquote.
> It can span multiple lines.
>
> And have multiple paragraphs.)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_horizontal_rules() {
    print_section("Example 7: Horizontal Rules");

    MarkdownParser parser;

    std::string markdown = R"(Text above

---

Text below)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_github_tables() {
    print_section("Example 8: Tables (GitHub Extension)");

    ParserOptions opts;
    opts.github_flavored = true;

    MarkdownParser parser(opts);

    std::string markdown = R"(| Name    | Age | City          |
|---------|-----|---------------|
| Alice   | 30  | New York      |
| Bob     | 25  | San Francisco |
| Charlie | 35  | Boston        |)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_task_lists() {
    print_section("Example 9: Task Lists (GitHub Extension)");

    ParserOptions opts;
    opts.github_flavored = true;

    MarkdownParser parser(opts);

    std::string markdown = R"(TODO list:
- [x] Write the code
- [x] Write the tests
- [ ] Write documentation
- [ ] Deploy to production)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_strikethrough() {
    print_section("Example 10: Strikethrough (GitHub Extension)");

    ParserOptions opts;
    opts.github_flavored = true;

    MarkdownParser parser(opts);

    std::string markdown = R"(This is ~~deleted text~~ and this is normal text.)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_pretty_print() {
    print_section("Example 11: Pretty-Printed Output");

    ParserOptions opts;
    opts.pretty_print = true;

    MarkdownParser parser(opts);

    std::string markdown = R"(# Title

This is a paragraph with **bold** text.

- Item 1
- Item 2)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_html_escaping() {
    print_section("Example 12: HTML Escaping");

    std::cout << "With escaping (default):\n";
    ParserOptions opts1;
    opts1.escape_html = true;

    MarkdownParser parser1(opts1);
    std::string markdown = "This contains <script>alert('xss')</script> HTML.";
    std::string html1 = parser1.parse(markdown);
    std::cout << "Input: " << markdown << "\n";
    std::cout << "Output: " << html1 << "\n\n";

    std::cout << "Without escaping:\n";
    ParserOptions opts2;
    opts2.escape_html = false;

    MarkdownParser parser2(opts2);
    std::string html2 = parser2.parse(markdown);
    std::cout << "Input: " << markdown << "\n";
    std::cout << "Output: " << html2 << std::endl;
}

void example_autolink() {
    print_section("Example 13: Autolinks");

    ParserOptions opts;
    opts.autolink = true;

    MarkdownParser parser(opts);

    std::string markdown = "Visit https://www.example.com for more information.";

    std::string html = parser.parse(markdown);
    std::cout << "Input: " << markdown << "\n";
    std::cout << "Output: " << html << std::endl;
}

void example_inline_parsing() {
    print_section("Example 14: Inline Parsing Only");

    MarkdownParser parser;

    std::string markdown = "This is **bold** and *italic* text with `code`.";

    std::string html = parser.parse_inline(markdown);
    std::cout << "Input: " << markdown << "\n";
    std::cout << "Output: " << html << std::endl;
}

void example_complex_document() {
    print_section("Example 15: Complex Document");

    ParserOptions opts;
    opts.github_flavored = true;
    opts.pretty_print = true;

    MarkdownParser parser(opts);

    std::string markdown = R"(# Project Documentation

## Overview

This project is a **modern** C++ library for *parsing* Markdown documents.

## Features

- Fast and efficient
- Easy to use
- Extensible

### Code Example

Here's how to use it:

```cpp
#include "MarkdownParser.hpp"

int main() {
    md::MarkdownParser parser;
    std::string html = parser.parse("# Hello");
    return 0;
}
```

## Installation

1. Clone the repository
2. Build with CMake
3. Include in your project

> **Note:** Requires C++20 or later

## Benchmarks

| Operation | Time (ms) | Throughput |
|-----------|-----------|------------|
| Parse     | 10        | 1 MB/s     |
| Generate  | 5         | 2 MB/s     |

## Status

- [x] Core features
- [x] GitHub extensions
- [ ] Table of contents
- [ ] Custom renderers

Visit https://github.com/example/project for more info.

---

© 2024 Example Project
)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

void example_file_conversion() {
    print_section("Example 16: File Conversion");

    ParserOptions opts;
    opts.github_flavored = true;
    opts.pretty_print = true;

    MarkdownParser parser(opts);

    // Create sample markdown file
    std::string markdown_content = R"(# Sample Document

This is a sample document for file conversion.

## Features

- Easy file I/O
- Full Markdown support
- Clean HTML output
)";

    // Write markdown file
    std::ofstream md_file("sample.md");
    md_file << markdown_content;
    md_file.close();

    std::cout << "Created sample.md\n";

    // Read markdown file
    std::ifstream input("sample.md");
    std::string markdown((std::istreambuf_iterator<char>(input)),
                         std::istreambuf_iterator<char>());
    input.close();

    // Convert to HTML
    std::string html = parser.parse(markdown);

    // Wrap in full HTML document
    std::string full_html = R"(<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sample Document</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
        blockquote { border-left: 4px solid #ddd; margin-left: 0; padding-left: 16px; }
    </style>
</head>
<body>
)";
    full_html += html;
    full_html += R"(
</body>
</html>)";

    // Write HTML file
    std::ofstream output("sample.html");
    output << full_html;
    output.close();

    std::cout << "Created sample.html\n";
    std::cout << "HTML output:\n" << full_html << std::endl;
}

void example_readme_rendering() {
    print_section("Example 17: README Rendering");

    ParserOptions opts;
    opts.github_flavored = true;
    opts.pretty_print = false;  // GitHub-style compact output

    MarkdownParser parser(opts);

    std::string readme = R"(# MyProject

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]

A **powerful** library for doing amazing things.

## Quick Start

```bash
git clone https://github.com/user/myproject
cd myproject
make
```

## Features

- [x] Fast
- [x] Reliable
- [ ] Complete

## Documentation

See the [docs](https://docs.example.com) for details.
)";

    std::string html = parser.parse(readme);
    std::cout << "README.md:\n" << readme << "\n\n";
    std::cout << "Rendered HTML:\n" << html << std::endl;
}

void example_mixed_content() {
    print_section("Example 18: Mixed Content");

    ParserOptions opts;
    opts.github_flavored = true;

    MarkdownParser parser(opts);

    std::string markdown = R"(# Mixed Content Example

Regular paragraph with **bold**, *italic*, and `code`.

> Quote with **bold text** and a [link](https://example.com).

List with formatting:
- **Bold item**
- *Italic item*
- Item with `code`
- ~~Deleted item~~

```python
def hello():
    return "Hello, **World**"  # Markdown in code stays literal
```

| Column 1 | Column 2 |
|----------|----------|
| **Bold** | *Italic* |
| `Code`   | ~~Del~~  |
)";

    std::string html = parser.parse(markdown);
    std::cout << "Input:\n" << markdown << "\n\n";
    std::cout << "Output:\n" << html << std::endl;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "   MarkdownParser - Examples            " << std::endl;
    std::cout << "========================================" << std::endl;

    try {
        example_basic_headers();
        example_emphasis();
        example_lists();
        example_links_and_images();
        example_code();
        example_blockquotes();
        example_horizontal_rules();
        example_github_tables();
        example_task_lists();
        example_strikethrough();
        example_pretty_print();
        example_html_escaping();
        example_autolink();
        example_inline_parsing();
        example_complex_document();
        example_file_conversion();
        example_readme_rendering();
        example_mixed_content();

        std::cout << "\n========================================" << std::endl;
        std::cout << "   All examples completed successfully  " << std::endl;
        std::cout << "========================================" << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
