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

    // For text selection with mouse
    BOOL _isDragging;
    NSPoint _mouseDownPoint;
    NSUInteger _mouseDownCharIndex;
}

- (instancetype)initWithFrame:(NSRect)frameRect;
- (void)setWidget:(CustomTextWidget*)widget;
- (CustomTextWidget*)widget;

// Helper methods for text selection
- (NSUInteger)characterIndexForPoint:(NSPoint)point;
- (NSRect)textRect;

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

        // Initialize mouse tracking state
        _isDragging = NO;
        _mouseDownPoint = NSZeroPoint;
        _mouseDownCharIndex = 0;
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

- (BOOL)isFlipped {
    // Use top-left coordinate system (like UIKit/text layout)
    return YES;
}

// MARK: - Drawing

- (void)drawRect:(NSRect)dirtyRect {
    [super drawRect:dirtyRect];

    if (!_widget) {
        // No widget - just draw background
        [_backgroundColor setFill];
        NSRectFill(dirtyRect);
        return;
    }

    // Get text and selection info
    std::string text = _widget->getText();
    NSString* nsText = [NSString stringWithUTF8String:text.c_str()];
    size_t selStart, selLength;
    _widget->getSelectionRange(selStart, selLength);

    // Debug: Log text length on first draw
    static BOOL firstDraw = YES;
    BOOL isFirstDraw = firstDraw;
    if (firstDraw) {
        NSLog(@"[Services] drawRect called - text length: %lu", (unsigned long)[nsText length]);
        NSLog(@"[Services] text: %@", nsText);
        NSLog(@"[Services] view bounds: %@", NSStringFromRect(self.bounds));
        NSLog(@"[Services] text color: %@, bg color: %@", _textColor, _backgroundColor);
        firstDraw = NO;
    }

    NSRect textRect = [self textRect];

    // STEP 1: Draw background
    [_backgroundColor setFill];
    NSRectFill(dirtyRect);

    // Create attributed string for text rendering and measurement
    NSDictionary* attributes = @{
        NSFontAttributeName: _font,
        NSForegroundColorAttributeName: _textColor
    };
    NSAttributedString* attrString = [[NSAttributedString alloc] initWithString:nsText attributes:attributes];

    // Calculate proper layout using NSLayoutManager for accurate glyph positions
    NSTextStorage* textStorage = [[NSTextStorage alloc] initWithAttributedString:attrString];
    NSLayoutManager* layoutManager = [[NSLayoutManager alloc] init];
    NSTextContainer* textContainer = [[NSTextContainer alloc] initWithContainerSize:textRect.size];

    [textContainer setLineFragmentPadding:0];
    [layoutManager addTextContainer:textContainer];
    [textStorage addLayoutManager:layoutManager];

    // STEP 2: Draw selection highlight (if any)
    if (selLength > 0 && selStart < [nsText length]) {
        // Get the glyph range for the selection
        NSRange glyphRange = [layoutManager glyphRangeForCharacterRange:NSMakeRange(selStart, selLength)
                                                    actualCharacterRange:NULL];

        // Enumerate line fragments that contain the selection
        [layoutManager enumerateLineFragmentsForGlyphRange:glyphRange
                                                 usingBlock:^(NSRect rect, NSRect usedRect, NSTextContainer *textContainer, NSRange lineGlyphRange, BOOL *stop) {
            // Calculate the intersection of selection with this line
            NSRange intersectionRange;
            intersectionRange.location = MAX(glyphRange.location, lineGlyphRange.location);
            intersectionRange.length = MIN(NSMaxRange(glyphRange), NSMaxRange(lineGlyphRange)) - intersectionRange.location;

            if (intersectionRange.length > 0) {
                // Get the bounding rect for this portion of the selection
                NSRect selectionRect = [layoutManager boundingRectForGlyphRange:intersectionRange
                                                                inTextContainer:textContainer];

                // Offset by textRect origin (since layout manager uses local coordinates)
                selectionRect.origin.x += textRect.origin.x;
                selectionRect.origin.y += textRect.origin.y;

                // Draw selection background
                [[_selectionColor colorWithAlphaComponent:0.4] setFill];
                NSRectFill(selectionRect);
            }
        }];
    }

    // STEP 3: Draw text on top of selection
    NSRange glyphRange = [layoutManager glyphRangeForTextContainer:textContainer];

    if (isFirstDraw) {
        NSLog(@"[Services] textRect: %@", NSStringFromRect(textRect));
        NSLog(@"[Services] glyphRange: %@, number of glyphs: %lu", NSStringFromRange(glyphRange), (unsigned long)glyphRange.length);
    }

    [layoutManager drawGlyphsForGlyphRange:glyphRange atPoint:textRect.origin];

    // STEP 4: Draw border around text area when focused
    if ([[self window] firstResponder] == self) {
        [[NSColor systemBlueColor] setStroke];
        NSBezierPath* border = [NSBezierPath bezierPathWithRect:NSInsetRect(self.bounds, 2, 2)];
        [border setLineWidth:2.0];
        [border stroke];
    }
}

// MARK: - Helper Methods

- (NSRect)textRect {
    return NSInsetRect(self.bounds, 10, 10);
}

- (NSUInteger)characterIndexForPoint:(NSPoint)point {
    if (!_widget) {
        return 0;
    }

    std::string text = _widget->getText();
    NSString* nsText = [NSString stringWithUTF8String:text.c_str()];

    if ([nsText length] == 0) {
        return 0;
    }

    NSRect textRect = [self textRect];

    // Convert point to text container coordinate system
    NSPoint localPoint = NSMakePoint(point.x - textRect.origin.x,
                                     point.y - textRect.origin.y);

    // Create text layout system for accurate hit testing
    NSDictionary* attributes = @{
        NSFontAttributeName: _font
    };
    NSAttributedString* attrString = [[NSAttributedString alloc] initWithString:nsText attributes:attributes];

    NSTextStorage* textStorage = [[NSTextStorage alloc] initWithAttributedString:attrString];
    NSLayoutManager* layoutManager = [[NSLayoutManager alloc] init];
    NSTextContainer* textContainer = [[NSTextContainer alloc] initWithContainerSize:textRect.size];

    [textContainer setLineFragmentPadding:0];
    [layoutManager addTextContainer:textContainer];
    [textStorage addLayoutManager:layoutManager];

    // Use layout manager for accurate character index from point
    NSUInteger glyphIndex = [layoutManager glyphIndexForPoint:localPoint
                                              inTextContainer:textContainer
                       fractionOfDistanceThroughGlyph:NULL];

    NSUInteger charIndex = [layoutManager characterIndexForGlyphAtIndex:glyphIndex];

    // Clamp to valid range
    if (charIndex > [nsText length]) {
        charIndex = [nsText length];
    }

    NSLog(@"Click at (%.1f, %.1f) local:(%.1f, %.1f) -> character index %lu",
          point.x, point.y, localPoint.x, localPoint.y, (unsigned long)charIndex);

    return charIndex;
}

// MARK: - Mouse Handling

- (void)mouseDown:(NSEvent *)event {
    [[self window] makeFirstResponder:self];

    if (!_widget) {
        return;
    }

    // Convert point to view coordinates
    NSPoint point = [self convertPoint:[event locationInWindow] fromView:nil];

    // Get character index at click point
    _mouseDownCharIndex = [self characterIndexForPoint:point];
    _mouseDownPoint = point;
    _isDragging = YES;

    // Start with zero-length selection at click point
    _widget->setSelection(_mouseDownCharIndex, 0);
    [self setNeedsDisplay:YES];

    NSLog(@"Mouse down at character %lu", (unsigned long)_mouseDownCharIndex);
}

- (void)mouseDragged:(NSEvent *)event {
    if (!_widget || !_isDragging) {
        return;
    }

    // Convert point to view coordinates
    NSPoint point = [self convertPoint:[event locationInWindow] fromView:nil];

    // Get character index at current drag point
    NSUInteger currentCharIndex = [self characterIndexForPoint:point];

    // Calculate selection range
    NSUInteger selStart, selLength;

    if (currentCharIndex >= _mouseDownCharIndex) {
        // Dragging forward
        selStart = _mouseDownCharIndex;
        selLength = currentCharIndex - _mouseDownCharIndex;
    } else {
        // Dragging backward
        selStart = currentCharIndex;
        selLength = _mouseDownCharIndex - currentCharIndex;
    }

    // Update selection
    _widget->setSelection(selStart, selLength);
    [self setNeedsDisplay:YES];

    // Reduce log spam - only log every 10 pixels of movement
    static NSPoint lastLogPoint = {0, 0};
    if (fabs(point.x - lastLogPoint.x) > 10 || fabs(point.y - lastLogPoint.y) > 10) {
        NSLog(@"Dragging: selection [%lu, %lu]", (unsigned long)selStart, (unsigned long)selLength);
        lastLogPoint = point;
    }
}

- (void)mouseUp:(NSEvent *)event {
    if (!_widget) {
        return;
    }

    _isDragging = NO;

    size_t selStart, selLength;
    _widget->getSelectionRange(selStart, selLength);

    NSLog(@"Mouse up: final selection [%zu, %zu]", selStart, selLength);

    // Handle double-click to select all
    if ([event clickCount] == 2) {
        std::string text = _widget->getText();
        _widget->setSelection(0, text.length());
        [self setNeedsDisplay:YES];
        NSLog(@"Double-click: selected all %zu characters", text.length());
    }
}

- (void)rightMouseDown:(NSEvent *)event {
    [[self window] makeFirstResponder:self];

    if (_widget) {
        // Check if there's already a selection
        size_t selStart, selLength;
        _widget->getSelectionRange(selStart, selLength);

        // If no selection, check if right-click is over text
        if (selLength == 0) {
            NSPoint point = [self convertPoint:[event locationInWindow] fromView:nil];
            NSUInteger charIndex = [self characterIndexForPoint:point];

            // Select word at click point, or all text if we can't determine word boundaries
            // For simplicity, just select all for now
            std::string text = _widget->getText();
            if (text.length() > 0) {
                _widget->setSelection(0, text.length());
                [self setNeedsDisplay:YES];
                NSLog(@"Right-click with no selection: selecting all text");
            }
        } else {
            NSLog(@"Right-click with existing selection [%zu, %zu]", selStart, selLength);
        }
    }

    // Create and show context menu
    NSMenu* menu = [[NSMenu alloc] initWithTitle:@""];

    // Add standard editing items
    NSMenuItem* copyItem = [[NSMenuItem alloc] initWithTitle:@"Copy"
                                                      action:@selector(copy:)
                                               keyEquivalent:@""];
    [menu addItem:copyItem];

    NSMenuItem* pasteItem = [[NSMenuItem alloc] initWithTitle:@"Paste"
                                                       action:@selector(paste:)
                                                keyEquivalent:@""];
    [menu addItem:pasteItem];

    [menu addItem:[NSMenuItem separatorItem]];

    NSMenuItem* selectAllItem = [[NSMenuItem alloc] initWithTitle:@"Select All"
                                                           action:@selector(selectAll:)
                                                    keyEquivalent:@""];
    [menu addItem:selectAllItem];

    [menu addItem:[NSMenuItem separatorItem]];

    // THIS IS CRITICAL: Add Services submenu manually
    NSMenuItem* servicesItem = [[NSMenuItem alloc] initWithTitle:@"Services"
                                                          action:nil
                                                   keyEquivalent:@""];
    NSMenu* servicesMenu = [[NSMenu alloc] initWithTitle:@"Services"];
    [servicesItem setSubmenu:servicesMenu];

    // Register this menu with the services
    [NSApplication sharedApplication].servicesMenu = servicesMenu;

    [menu addItem:servicesItem];

    NSLog(@"Showing context menu with Services submenu");

    // Show the menu
    [NSMenu popUpContextMenu:menu withEvent:event forView:self];
}

// MARK: - NSServicesMenuRequestor Protocol
// This is the KEY to Writing Tools integration!

- (id)validRequestorForSendType:(NSPasteboardType)sendType
                     returnType:(NSPasteboardType)returnType {

    NSLog(@"validRequestorForSendType called - sendType: %@, returnType: %@", sendType, returnType);

    // Support plain text and RTF
    if ([sendType isEqualToString:NSPasteboardTypeString] ||
        [sendType isEqualToString:NSPasteboardTypeRTF]) {
        // We can provide text to Writing Tools
        if (_widget && !_widget->getText().empty()) {
            NSLog(@"✅ Returning self as valid requestor for text services");
            return self;
        }
    }

    id result = [super validRequestorForSendType:sendType returnType:returnType];
    NSLog(@"⚠️ Returning super result: %@", result);
    return result;
}

- (BOOL)writeSelectionToPasteboard:(NSPasteboard *)pboard
                             types:(NSArray<NSPasteboardType> *)types {

    NSLog(@"📤 writeSelectionToPasteboard called with types: %@", types);

    if (!_widget) {
        NSLog(@"❌ No widget available");
        return NO;
    }

    // Get the selected text (or all text if nothing selected)
    std::string selectedText = _widget->getSelectedText();
    NSString* nsSelectedText = [NSString stringWithUTF8String:selectedText.c_str()];

    if (!nsSelectedText || [nsSelectedText length] == 0) {
        NSLog(@"❌ No text to write");
        return NO;
    }

    NSLog(@"📝 Writing %lu characters to pasteboard: %@", (unsigned long)[nsSelectedText length],
          [nsSelectedText length] > 50 ? [[nsSelectedText substringToIndex:50] stringByAppendingString:@"..."] : nsSelectedText);

    [pboard clearContents];

    BOOL success = NO;

    // Provide plain text
    if ([types containsObject:NSPasteboardTypeString]) {
        success = [pboard setString:nsSelectedText forType:NSPasteboardTypeString];
        NSLog(@"✅ Wrote plain text: %@", success ? @"YES" : @"NO");
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
            NSLog(@"✅ Wrote RTF data: %lu bytes", (unsigned long)[rtfData length]);
        }
    }

    return success;
}

- (BOOL)readSelectionFromPasteboard:(NSPasteboard *)pboard {
    NSLog(@"📥 readSelectionFromPasteboard called");

    if (!_widget) {
        NSLog(@"❌ No widget available");
        return NO;
    }

    // Read the text modified by Writing Tools
    NSString* nsText = [pboard stringForType:NSPasteboardTypeString];

    if (!nsText) {
        NSLog(@"⚠️ No plain text, trying RTF...");
        // Try RTF
        NSData* rtfData = [pboard dataForType:NSPasteboardTypeRTF];
        if (rtfData) {
            NSAttributedString* attrString = [[NSAttributedString alloc]
                initWithRTF:rtfData documentAttributes:nil];
            nsText = [attrString string];
            NSLog(@"📄 Extracted text from RTF: %lu characters", (unsigned long)[nsText length]);
        }
    }

    if (nsText) {
        std::string cppText = [nsText UTF8String];
        _widget->replaceSelection(cppText);
        [self setNeedsDisplay:YES];

        NSLog(@"✅ Writing Tools updated text (%lu chars): %@",
              (unsigned long)[nsText length],
              [nsText length] > 100 ? [[nsText substringToIndex:100] stringByAppendingString:@"..."] : nsText);
        return YES;
    }

    NSLog(@"❌ No text found in pasteboard");
    return NO;
}

// MARK: - Standard Text Operations

- (void)copy:(id)sender {
    if (!_widget) return;

    std::string selectedText = _widget->getSelectedText();
    NSString* nsText = [NSString stringWithUTF8String:selectedText.c_str()];

    if (nsText && [nsText length] > 0) {
        NSPasteboard* pb = [NSPasteboard generalPasteboard];
        [pb clearContents];
        [pb setString:nsText forType:NSPasteboardTypeString];

        NSLog(@"Copied %lu characters to pasteboard", (unsigned long)[nsText length]);
    }
}

- (void)paste:(id)sender {
    if (!_widget) return;

    NSPasteboard* pb = [NSPasteboard generalPasteboard];
    NSString* nsText = [pb stringForType:NSPasteboardTypeString];

    if (nsText) {
        std::string cppText = [nsText UTF8String];
        _widget->replaceSelection(cppText);
        [self setNeedsDisplay:YES];

        NSLog(@"Pasted %lu characters from pasteboard", (unsigned long)[nsText length]);
    }
}

- (void)selectAll:(id)sender {
    if (!_widget) return;

    std::string text = _widget->getText();
    _widget->setSelection(0, text.length());
    [self setNeedsDisplay:YES];

    NSLog(@"Selected all text (%zu characters)", text.length());
}

// MARK: - Keyboard Shortcuts

- (void)keyDown:(NSEvent *)event {
    // Handle Command+A to select all
    if ([event modifierFlags] & NSEventModifierFlagCommand) {
        if ([[event characters] isEqualToString:@"a"]) {
            [self selectAll:nil];
            return;
        }
        if ([[event characters] isEqualToString:@"c"]) {
            [self copy:nil];
            return;
        }
        if ([[event characters] isEqualToString:@"v"]) {
            [self paste:nil];
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
        [view setNeedsDisplay:YES];  // Trigger initial draw
    }

    void* GetViewPointer(void* viewPtr) {
        return viewPtr;
    }
}
