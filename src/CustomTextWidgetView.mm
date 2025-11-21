#import <Cocoa/Cocoa.h>
#include "CustomTextWidget.h"
#include <string>

// Objective-C++ NSView subclass that bridges to C++ CustomTextWidget
// This implements NSServicesMenuRequestor to support Writing Tools
@interface CustomTextWidgetView : NSView <NSServicesMenuRequestor>
{
    CustomTextWidget* _widget;
    NSFont* _font;
    NSColor* _textColor;
    NSColor* _backgroundColor;
    NSColor* _selectionColor;
}

- (instancetype)initWithFrame:(NSRect)frameRect;
- (void)setWidget:(CustomTextWidget*)widget;
- (CustomTextWidget*)widget;

@end

@implementation CustomTextWidgetView

- (instancetype)initWithFrame:(NSRect)frameRect {
    self = [super initWithFrame:frameRect];
    if (self) {
        _widget = nullptr;
        _font = [NSFont systemFontOfSize:14.0];
        _textColor = [NSColor textColor];
        _backgroundColor = [NSColor textBackgroundColor];
        _selectionColor = [NSColor selectedTextBackgroundColor];
    }
    return self;
}

- (void)setWidget:(CustomTextWidget*)widget {
    _widget = widget;

    // Set up callback to refresh view when text changes
    if (_widget) {
        _widget->setTextModifiedCallback([self](const std::string& text) {
            dispatch_async(dispatch_get_main_queue(), ^{
                [self setNeedsDisplay:YES];
            });
        });
    }
}

- (CustomTextWidget*)widget {
    return _widget;
}

- (BOOL)acceptsFirstResponder {
    return YES;
}

- (BOOL)canBecomeKeyView {
    return YES;
}

// MARK: - Drawing

- (void)drawRect:(NSRect)dirtyRect {
    [super drawRect:dirtyRect];

    // Draw background
    [_backgroundColor setFill];
    NSRectFill(dirtyRect);

    if (!_widget) {
        return;
    }

    // Get text from widget
    std::string text = _widget->getText();
    NSString* nsText = [NSString stringWithUTF8String:text.c_str()];

    // Draw text
    NSDictionary* attributes = @{
        NSFontAttributeName: _font,
        NSForegroundColorAttributeName: _textColor
    };

    NSRect textRect = NSInsetRect(self.bounds, 10, 10);
    [nsText drawInRect:textRect withAttributes:attributes];

    // Draw selection highlight if there is one
    size_t selStart, selLength;
    _widget->getSelectionRange(selStart, selLength);

    if (selLength > 0) {
        // Simple selection visualization
        // In a real implementation, you'd calculate proper text metrics
        NSRect selectionRect = NSMakeRect(textRect.origin.x,
                                         textRect.origin.y,
                                         textRect.size.width,
                                         20);
        [_selectionColor setFill];
        NSRectFillUsingOperation(selectionRect, NSCompositingOperationSourceOver);
    }
}

// MARK: - Mouse Handling

- (void)mouseDown:(NSEvent *)event {
    [[self window] makeFirstResponder:self];

    if (_widget) {
        // Select all text on click (simplified)
        std::string text = _widget->getText();
        _widget->setSelection(0, text.length());
        [self setNeedsDisplay:YES];
    }
}

// MARK: - NSServicesMenuRequestor Protocol
// This is the KEY to Writing Tools integration!

- (id)validRequestorForSendType:(NSPasteboardType)sendType
                     returnType:(NSPasteboardType)returnType {

    // Support plain text and RTF
    if ([sendType isEqualToString:NSPasteboardTypeString] ||
        [sendType isEqualToString:NSPasteboardTypeRTF]) {
        // We can provide text to Writing Tools
        if (_widget && !_widget->getText().empty()) {
            return self;
        }
    }

    return [super validRequestorForSendType:sendType returnType:returnType];
}

- (BOOL)writeSelectionToPasteboard:(NSPasteboard *)pboard
                             types:(NSArray<NSPasteboardType> *)types {

    if (!_widget) {
        return NO;
    }

    // Get the selected text (or all text if nothing selected)
    std::string selectedText = _widget->getSelectedText();
    NSString* nsSelectedText = [NSString stringWithUTF8String:selectedText.c_str()];

    if (!nsSelectedText || [nsSelectedText length] == 0) {
        return NO;
    }

    [pboard clearContents];

    BOOL success = NO;

    // Provide plain text
    if ([types containsObject:NSPasteboardTypeString]) {
        success = [pboard setString:nsSelectedText forType:NSPasteboardTypeString];
    }

    // Provide RTF if requested
    if ([types containsObject:NSPasteboardTypeRTF]) {
        NSAttributedString* attrString = [[NSAttributedString alloc]
            initWithString:nsSelectedText
            attributes:@{NSFontAttributeName: _font}];
        NSData* rtfData = [attrString RTFFromRange:NSMakeRange(0, [attrString length])
                                documentAttributes:@{}];
        if (rtfData) {
            success = [pboard setData:rtfData forType:NSPasteboardTypeRTF] || success;
        }
    }

    return success;
}

- (BOOL)readSelectionFromPasteboard:(NSPasteboard *)pboard {
    if (!_widget) {
        return NO;
    }

    // Read the text modified by Writing Tools
    NSString* nsText = [pboard stringForType:NSPasteboardTypeString];

    if (!nsText) {
        // Try RTF
        NSData* rtfData = [pboard dataForType:NSPasteboardTypeRTF];
        if (rtfData) {
            NSAttributedString* attrString = [[NSAttributedString alloc]
                initWithRTF:rtfData documentAttributes:nil];
            nsText = [attrString string];
        }
    }

    if (nsText) {
        std::string cppText = [nsText UTF8String];
        _widget->replaceSelection(cppText);
        [self setNeedsDisplay:YES];

        NSLog(@"Writing Tools updated text: %@", nsText);
        return YES;
    }

    return NO;
}

// MARK: - Keyboard Shortcuts

- (void)keyDown:(NSEvent *)event {
    // Handle Command+A to select all
    if ([event modifierFlags] & NSEventModifierFlagCommand) {
        if ([[event characters] isEqualToString:@"a"]) {
            if (_widget) {
                std::string text = _widget->getText();
                _widget->setSelection(0, text.length());
                [self setNeedsDisplay:YES];
            }
            return;
        }
    }

    [super keyDown:event];
}

@end

// C interface for creating the view from C++
extern "C" {
    void* CreateCustomTextWidgetView(double x, double y, double width, double height) {
        NSRect frame = NSMakeRect(x, y, width, height);
        CustomTextWidgetView* view = [[CustomTextWidgetView alloc] initWithFrame:frame];
        return (__bridge_retained void*)view;
    }

    void SetWidgetForView(void* viewPtr, CustomTextWidget* widget) {
        CustomTextWidgetView* view = (__bridge CustomTextWidgetView*)viewPtr;
        [view setWidget:widget];
    }

    void* GetViewPointer(void* viewPtr) {
        return viewPtr;
    }
}
