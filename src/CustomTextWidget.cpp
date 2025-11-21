#include "CustomTextWidget.h"
#include <algorithm>

CustomTextWidget::CustomTextWidget()
    : m_text(""), m_selectionStart(0), m_selectionLength(0) {
}

CustomTextWidget::~CustomTextWidget() {
}

void CustomTextWidget::setText(const std::string& text) {
    m_text = text;
    m_selectionStart = 0;
    m_selectionLength = 0;

    if (m_textModifiedCallback) {
        m_textModifiedCallback(m_text);
    }
}

std::string CustomTextWidget::getText() const {
    return m_text;
}

void CustomTextWidget::setSelection(size_t start, size_t length) {
    m_selectionStart = std::min(start, m_text.length());
    m_selectionLength = std::min(length, m_text.length() - m_selectionStart);
}

std::string CustomTextWidget::getSelectedText() const {
    if (m_selectionLength == 0) {
        return m_text; // Return all text if no selection
    }
    return m_text.substr(m_selectionStart, m_selectionLength);
}

void CustomTextWidget::replaceSelection(const std::string& newText) {
    if (m_selectionLength == 0) {
        // If no selection, replace entire text
        m_text = newText;
        m_selectionStart = 0;
        m_selectionLength = 0;
    } else {
        // Replace selected portion
        m_text.replace(m_selectionStart, m_selectionLength, newText);
        m_selectionStart = m_selectionStart + newText.length();
        m_selectionLength = 0;
    }

    if (m_textModifiedCallback) {
        m_textModifiedCallback(m_text);
    }
}

void CustomTextWidget::setTextModifiedCallback(std::function<void(const std::string&)> callback) {
    m_textModifiedCallback = callback;
}

void CustomTextWidget::getSelectionRange(size_t& start, size_t& length) const {
    start = m_selectionStart;
    length = m_selectionLength;
}
