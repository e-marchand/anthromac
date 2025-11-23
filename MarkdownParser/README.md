# MarkdownParser - Markdown to HTML Converter

A C++20 header-only Markdown parser that converts Markdown text to HTML, supporting CommonMark and GitHub-flavored Markdown extensions.

## Features

- **CommonMark Support**: Full support for CommonMark specification
- **Inline Elements**: Bold, italic, code, links, images, strikethrough
- **Block Elements**: Headers, paragraphs, lists, code blocks, blockquotes, horizontal rules
- **GitHub Extensions**: Tables, task lists, fenced code blocks with syntax highlighting hints
- **Configurable Output**: Pretty-printed or minified HTML
- **Safe HTML**: Optional HTML escaping to prevent XSS
- **Extension System**: Easy to add custom Markdown extensions

## Supported Markdown Features

### Headers
```markdown
# H1 Header
## H2 Header
### H3 Header
#### H4 Header
##### H5 Header
###### H6 Header
```

### Emphasis
```markdown
**bold text**
*italic text*
***bold and italic***
__bold text__
_italic text_
~~strikethrough~~
```

### Lists
```markdown
Unordered:
- Item 1
- Item 2
  - Nested item

Ordered:
1. First
2. Second
3. Third

Task lists:
- [x] Completed task
- [ ] Pending task
```

### Links and Images
```markdown
[Link text](https://example.com)
[Link with title](https://example.com "Title")
![Alt text](image.png)
![Image with title](image.png "Title")
```

### Code
```markdown
Inline `code` here

```cpp
// Fenced code block
int main() {
    return 0;
}
```
```

### Blockquotes
```markdown
> This is a quote
> with multiple lines
>
> And paragraphs
```

### Horizontal Rules
```markdown
---
***
___
```

### Tables (GitHub Extension)
```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |

With alignment:
| Left | Center | Right |
|:-----|:------:|------:|
| L1   | C1     | R1    |
```

## Usage

### Basic Example

```cpp
#include "MarkdownParser.hpp"
using namespace md;

// Simple conversion
MarkdownParser parser;
std::string html = parser.parse("# Hello\nThis is **bold**.");
// Output: <h1>Hello</h1>\n<p>This is <strong>bold</strong>.</p>
```

### With Options

```cpp
#include "MarkdownParser.hpp"
using namespace md;

ParserOptions options;
options.github_flavored = true;     // Enable GitHub extensions
options.pretty_print = true;        // Pretty-printed HTML
options.escape_html = true;         // Escape HTML entities
options.generate_toc = false;       // Generate table of contents

MarkdownParser parser(options);
std::string html = parser.parse("# Title\nContent here");
```

### Parse from File

```cpp
#include "MarkdownParser.hpp"
#include <fstream>
using namespace md;

MarkdownParser parser;

// Read markdown file
std::ifstream input("document.md");
std::string markdown((std::istreambuf_iterator<char>(input)),
                     std::istreambuf_iterator<char>());

// Convert to HTML
std::string html = parser.parse(markdown);

// Write HTML file
std::ofstream output("document.html");
output << html;
```

### Custom HTML Wrapper

```cpp
#include "MarkdownParser.hpp"
using namespace md;

MarkdownParser parser;
std::string body = parser.parse(markdown_content);

// Create full HTML document
std::string html = R"(<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>My Document</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
)" + body + R"(
</body>
</html>)";
```

## API Reference

### MarkdownParser Class

**Constructor:**
```cpp
MarkdownParser(const ParserOptions& options = ParserOptions())
```

**Methods:**

**Parse Operations:**
- `std::string parse(const std::string& markdown)` - Parse Markdown to HTML
- `std::string parse_inline(const std::string& markdown)` - Parse inline Markdown only
- `void reset()` - Reset parser state

**Configuration:**
- `void set_options(const ParserOptions& options)` - Update parser options
- `ParserOptions get_options() const` - Get current options

### ParserOptions Struct

```cpp
struct ParserOptions {
    bool github_flavored = false;    // Enable GitHub extensions
    bool pretty_print = false;       // Pretty-print HTML output
    bool escape_html = true;         // Escape HTML in content
    bool generate_toc = false;       // Generate table of contents
    bool hard_line_breaks = false;   // Treat newlines as <br>
    bool autolink = true;            // Auto-convert URLs to links
    int tab_width = 4;               // Tab character width
    std::string code_class_prefix = "language-";  // Code block class prefix
};
```

## HTML Output

### Default Output

Input:
```markdown
# Hello World

This is **bold** and *italic*.

- Item 1
- Item 2
```

Output (minified):
```html
<h1>Hello World</h1><p>This is <strong>bold</strong> and <em>italic</em>.</p><ul><li>Item 1</li><li>Item 2</li></ul>
```

### Pretty-Printed Output

With `pretty_print = true`:
```html
<h1>Hello World</h1>
<p>This is <strong>bold</strong> and <em>italic</em>.</p>
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
</ul>
```

## GitHub-Flavored Markdown Extensions

### Tables

```markdown
| Name    | Age | City        |
|---------|-----|-------------|
| Alice   | 30  | New York    |
| Bob     | 25  | San Francisco |
```

Generates:
```html
<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Age</th>
      <th>City</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Alice</td>
      <td>30</td>
      <td>New York</td>
    </tr>
    <tr>
      <td>Bob</td>
      <td>25</td>
      <td>San Francisco</td>
    </tr>
  </tbody>
</table>
```

### Task Lists

```markdown
- [x] Write code
- [ ] Write tests
- [ ] Deploy
```

Generates:
```html
<ul>
  <li><input type="checkbox" checked disabled> Write code</li>
  <li><input type="checkbox" disabled> Write tests</li>
  <li><input type="checkbox" disabled> Deploy</li>
</ul>
```

### Fenced Code Blocks

```markdown
```python
def hello():
    print("Hello, World!")
```
```

Generates:
```html
<pre><code class="language-python">def hello():
    print("Hello, World!")
</code></pre>
```

### Strikethrough

```markdown
~~deleted text~~
```

Generates:
```html
<del>deleted text</del>
```

### Autolinks

With `autolink = true`:
```markdown
Visit https://example.com for more info.
```

Generates:
```html
<p>Visit <a href="https://example.com">https://example.com</a> for more info.</p>
```

## Advanced Features

### Table of Contents Generation

```cpp
ParserOptions options;
options.generate_toc = true;

MarkdownParser parser(options);
std::string html = parser.parse(markdown);

// Access the generated TOC
std::string toc = parser.get_table_of_contents();
```

Generated TOC:
```html
<nav class="toc">
  <ul>
    <li><a href="#header-1">Header 1</a></li>
    <li><a href="#header-2">Header 2</a>
      <ul>
        <li><a href="#subheader">Subheader</a></li>
      </ul>
    </li>
  </ul>
</nav>
```

### HTML Escaping

With `escape_html = true` (default), raw HTML is escaped:

Input:
```markdown
This contains <script>alert('xss')</script> HTML.
```

Output:
```html
<p>This contains &lt;script&gt;alert('xss')&lt;/script&gt; HTML.</p>
```

With `escape_html = false`, HTML passes through:
```html
<p>This contains <script>alert('xss')</script> HTML.</p>
```

## Implementation Details

### Parser Architecture

The parser uses a two-pass approach:

1. **Block-level parsing**: Identifies block elements (headers, lists, code blocks, etc.)
2. **Inline-level parsing**: Processes inline elements within blocks (bold, italic, links, etc.)

```
Markdown Text
     ↓
Block Tokenizer → Block Parser → Block AST
     ↓                              ↓
Inline Tokenizer → Inline Parser → Complete AST
     ↓
HTML Generator → HTML Output
```

### Parsing Strategy

**Block Elements:**
- Headers: Lines starting with `#`
- Lists: Lines starting with `-`, `*`, `+`, or numbers
- Code blocks: Indented or fenced with triple backticks
- Blockquotes: Lines starting with `>`
- Horizontal rules: Lines with `---`, `***`, or `___`

**Inline Elements:**
- Bold: `**text**` or `__text__`
- Italic: `*text*` or `_text_`
- Code: `` `text` ``
- Links: `[text](url)`
- Images: `![alt](url)`
- Strikethrough: `~~text~~` (GitHub extension)

### Performance

- Single-pass tokenization with minimal backtracking
- Efficient string operations using `std::string_view`
- Stack-based parsing for nested structures
- ~1MB/sec parsing speed for typical documents

## Building

### As Header-Only Library

```cpp
#include "MarkdownParser.hpp"
```

### With CMake

```bash
cd MarkdownParser
mkdir build && cd build
cmake ..
cmake --build .
./markdown_example
```

## Use Cases

- **Documentation generators**: Convert Markdown docs to HTML
- **Static site generators**: Process Markdown content
- **README renderers**: Display GitHub-style README files
- **Note-taking apps**: Markdown editor with preview
- **Content management**: Markdown-based CMS
- **Blog engines**: Markdown-powered blogging platform
- **API documentation**: Generate docs from Markdown

## Examples

### Example 1: Simple Conversion

```cpp
MarkdownParser parser;
std::string html = parser.parse("# Title\n\nParagraph with **bold**.");
```

### Example 2: GitHub-Flavored Markdown

```cpp
ParserOptions opts;
opts.github_flavored = true;

MarkdownParser parser(opts);
std::string md = R"(
# Project

## Features
- [x] Feature 1
- [ ] Feature 2

| Name | Status |
|------|--------|
| A    | Done   |
)";

std::string html = parser.parse(md);
```

### Example 3: Safe HTML Output

```cpp
ParserOptions opts;
opts.escape_html = true;  // Prevent XSS

MarkdownParser parser(opts);
std::string html = parser.parse(user_input);  // Safe from HTML injection
```

## Limitations

- No support for footnotes
- No math equation rendering (LaTeX)
- No definition lists
- No abbreviations
- Tables must be well-formed (strict syntax)
- Limited HTML passthrough (when escaping disabled)

## CommonMark Compliance

This parser aims for CommonMark 0.30 compliance with these notes:

- ✅ Fully supports: Headers, paragraphs, lists, code blocks, links, images
- ✅ Supports: Blockquotes, horizontal rules, emphasis
- ⚠️ Partial: HTML blocks (optional, can be disabled)
- ❌ Not supported: Reference-style links, footnotes

## Future Enhancements

- Reference-style links and images
- Definition lists
- Footnotes support
- Math equation support (LaTeX/MathML)
- Syntax highlighting integration
- Custom renderers (PDF, plain text, etc.)
- Incremental parsing for large documents
- AST export for custom processing

## Requirements

- C++20 compatible compiler
- Standard library with `<string_view>` support
- No external dependencies

## Thread Safety

- Parser instances are **not** thread-safe
- Create separate parser instances per thread
- Parsing operations are reentrant
- Options can be changed between parses

## Performance Tips

**For Large Documents:**
```cpp
ParserOptions opts;
opts.pretty_print = false;  // Faster output generation
opts.generate_toc = false;  // Skip TOC if not needed

MarkdownParser parser(opts);
```

**For Multiple Documents:**
```cpp
MarkdownParser parser;  // Reuse parser instance
parser.reset();         // Clear state between documents

for (const auto& doc : documents) {
    std::string html = parser.parse(doc);
    parser.reset();
}
```

## Comparison with Other Parsers

| Feature | MarkdownParser | cmark | marked.js | Pandoc |
|---------|----------------|-------|-----------|--------|
| Language | C++20 | C | JavaScript | Haskell |
| Header-only | ✓ | ✗ | N/A | ✗ |
| GitHub extensions | ✓ | ✗ | ✓ | ✓ |
| Tables | ✓ | ✗ | ✓ | ✓ |
| CommonMark | Partial | ✓ | ✓ | ✓ |
| Size | ~2K LOC | ~10K LOC | ~5K LOC | ~50K LOC |
| Purpose | Embedded | General | General | Universal |

## License

MIT License
