#ifndef CUSTOM_TEXT_WIDGET_H
#define CUSTOM_TEXT_WIDGET_H

#include <string>
#include <functional>

// C++ interface for a custom text widget
// This represents your custom GUI text widget implementation
class CustomTextWidget {
public:
    CustomTextWidget();
    ~CustomTextWidget();

    // Text content management
    void setText(const std::string& text);
    std::string getText() const;

    // Selection management
    void setSelection(size_t start, size_t length);
    std::string getSelectedText() const;
    void replaceSelection(const std::string& newText);

    // Callback when text is modified by Writing Tools
    void setTextModifiedCallback(std::function<void(const std::string&)> callback);

    // Get selection range
    void getSelectionRange(size_t& start, size_t& length) const;

private:
    std::string m_text;
    size_t m_selectionStart;
    size_t m_selectionLength;
    std::function<void(const std::string&)> m_textModifiedCallback;
};

#endif // CUSTOM_TEXT_WIDGET_H
