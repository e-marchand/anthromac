#import <Cocoa/Cocoa.h>
#import <objc/runtime.h>
#include "CustomTextWidget.h"
#include <string>

// Forward declare the coordinator and delegate protocol (macOS 15+)
@class NSWritingToolsCoordinator;
@protocol NSWritingToolsCoordinatorDelegate;

// Objective-C++ NSView subclass using the NEW Writing Tools Coordinator API
// This provides inline Writing Tools UI (macOS 15+)
@interface CoordinatorTextWidgetView : NSView <NSTextInputClient>
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

    // Writing Tools Coordinator (macOS 15+)
    NSWritingToolsCoordinator* _writingToolsCoordinator;
    BOOL _isWritingToolsActive;
}

- (instancetype)initWithFrame:(NSRect)frameRect;
- (void)setWidget:(CustomTextWidget*)widget;
- (CustomTextWidget*)widget;

// Helper methods for text selection
- (NSUInteger)characterIndexForPoint:(NSPoint)point;
- (NSRect)textRect;

@end

@implementation CoordinatorTextWidgetView

- (instancetype)initWithFrame:(NSRect)frameRect {
    self = [super initWithFrame:frameRect];
    if (self) {
        _widget = nullptr;
        _font = [NSFont systemFontOfSize:14.0];
        // Use explicit colors for debugging (black text on white background)
        _textColor = [NSColor blackColor];
        _backgroundColor = [NSColor whiteColor];
        _selectionColor = [NSColor selectedTextBackgroundColor];

        // Initialize mouse tracking state
        _isDragging = NO;
        _mouseDownPoint = NSZeroPoint;
        _mouseDownCharIndex = 0;
        _isWritingToolsActive = NO;

        // Initialize Writing Tools Coordinator (macOS 15+)
        if (@available(macOS 15.0, *)) {
            // Create coordinator with self as delegate
            Class coordinatorClass = NSClassFromString(@"NSWritingToolsCoordinator");
            if (coordinatorClass) {
                // Use performSelector to avoid compile-time checks
                SEL initSel = NSSelectorFromString(@"initWithDelegate:");
                if ([coordinatorClass instancesRespondToSelector:initSel]) {
                    _writingToolsCoordinator = [[coordinatorClass alloc] performSelector:initSel withObject:self];
                    NSLog(@"[Coordinator] Created NSWritingToolsCoordinator: %@", _writingToolsCoordinator);
                }
            }
        }
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

// MARK: - NSTextViewDelegate for Writing Tools (macOS 15+)

- (void)textViewWritingToolsWillBegin:(NSTextView *)textView API_AVAILABLE(macos(15.0)) {
    _isWritingToolsActive = YES;
    NSLog(@"🟢 Writing Tools session STARTED (Coordinator API)");
}

- (void)textViewWritingToolsDidEnd:(NSTextView *)textView API_AVAILABLE(macos(15.0)) {
    _isWritingToolsActive = NO;
    NSLog(@"🔴 Writing Tools session ENDED (Coordinator API)");
}

- (NSArray<NSValue *> *)textView:(NSTextView *)textView
        writingToolsIgnoredRangesInEnclosingRange:(NSRange)enclosingRange API_AVAILABLE(macos(15.0)) {
    // Return ranges to ignore (e.g., code blocks, URLs)
    // For now, don't ignore anything
    NSLog(@"📋 Writing Tools requesting ignored ranges");
    return @[];
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
    if (firstDraw) {
        NSLog(@"[Coordinator] drawRect called - text length: %lu, text: %@", (unsigned long)[nsText length], nsText);
        firstDraw = NO;
    }

    NSRect textRect = [self textRect];

    // STEP 1: Draw background
    // Highlight differently when Writing Tools is active
    if (_isWritingToolsActive) {
        NSColor* highlightColor = [[NSColor systemYellowColor] colorWithAlphaComponent:0.1];
        [highlightColor setFill];
    } else {
        [_backgroundColor setFill];
    }
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
                NSColor* selectionFillColor = [_selectionColor colorWithAlphaComponent:0.4];
                [selectionFillColor setFill];
                NSRectFill(selectionRect);
            }
        }];
    }

    // STEP 3: Draw text on top of selection
    NSRange glyphRange = [layoutManager glyphRangeForTextContainer:textContainer];
    [layoutManager drawGlyphsForGlyphRange:glyphRange atPoint:textRect.origin];

    // STEP 4: Draw border around text area when focused
    NSColor* borderColor;
    if (_isWritingToolsActive) {
        borderColor = [NSColor systemYellowColor]; // Yellow when Writing Tools active
    } else if ([[self window] firstResponder] == self) {
        borderColor = [NSColor systemBlueColor]; // Blue when focused
    } else {
        borderColor = nil;
    }

    if (borderColor) {
        [borderColor setStroke];
        NSBezierPath* border = [NSBezierPath bezierPathWithRect:NSInsetRect(self.bounds, 2, 2)];
        [border setLineWidth:2.0];
        [border stroke];
    }

    // Draw label if Writing Tools active
    if (_isWritingToolsActive) {
        NSDictionary* labelAttrs = @{
            NSFontAttributeName: [NSFont boldSystemFontOfSize:10],
            NSForegroundColorAttributeName: [NSColor systemYellowColor]
        };
        [@"✨ Writing Tools Active" drawAtPoint:NSMakePoint(5, 5) withAttributes:labelAttrs];
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

    return charIndex;
}

// MARK: - Mouse Handling (same as Services version)

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

    NSLog(@"[Coordinator] Mouse down at character %lu", (unsigned long)_mouseDownCharIndex);
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
}

- (void)mouseUp:(NSEvent *)event {
    if (!_widget) {
        return;
    }

    _isDragging = NO;

    size_t selStart, selLength;
    _widget->getSelectionRange(selStart, selLength);

    // Handle double-click to select all
    if ([event clickCount] == 2) {
        std::string text = _widget->getText();
        _widget->setSelection(0, text.length());
        [self setNeedsDisplay:YES];
        NSLog(@"[Coordinator] Double-click: selected all %zu characters", text.length());
    }
}

- (void)rightMouseDown:(NSEvent *)event {
    [[self window] makeFirstResponder:self];

    if (_widget) {
        // Check if there's already a selection
        size_t selStart, selLength;
        _widget->getSelectionRange(selStart, selLength);

        // If no selection, select all for context menu
        if (selLength == 0) {
            std::string text = _widget->getText();
            if (text.length() > 0) {
                _widget->setSelection(0, text.length());
                [self setNeedsDisplay:YES];
                NSLog(@"[Coordinator] Right-click with no selection: selecting all text");
            }
        }
    }

    // Create context menu with inline Writing Tools trigger
    NSMenu* menu = [[NSMenu alloc] initWithTitle:@""];

    // Add standard editing items
    [menu addItemWithTitle:@"Copy" action:@selector(copy:) keyEquivalent:@""];
    [menu addItemWithTitle:@"Paste" action:@selector(paste:) keyEquivalent:@""];
    [menu addItem:[NSMenuItem separatorItem]];
    [menu addItemWithTitle:@"Select All" action:@selector(selectAll:) keyEquivalent:@""];

    [menu addItem:[NSMenuItem separatorItem]];

    // Add Writing Tools menu item (triggers coordinator)
    if (@available(macOS 15.0, *)) {
        if (_writingToolsCoordinator) {
            [menu addItemWithTitle:@"✨ Writing Tools..."
                            action:@selector(showWritingTools:)
                     keyEquivalent:@""];
        }
    }

    NSLog(@"[Coordinator] Showing context menu with inline Writing Tools");

    // Show the menu
    [NSMenu popUpContextMenu:menu withEvent:event forView:self];
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

        NSLog(@"[Coordinator] Copied %lu characters", (unsigned long)[nsText length]);
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

        NSLog(@"[Coordinator] Pasted %lu characters", (unsigned long)[nsText length]);
    }
}

- (void)selectAll:(id)sender {
    if (!_widget) return;

    std::string text = _widget->getText();
    _widget->setSelection(0, text.length());
    [self setNeedsDisplay:YES];

    NSLog(@"[Coordinator] Selected all text (%zu characters)", text.length());
}

// MARK: - Writing Tools Trigger

- (void)showWritingTools:(id)sender {
    if (@available(macOS 15.0, *)) {
        if (!_writingToolsCoordinator) {
            NSLog(@"[Coordinator] ⚠️ No coordinator available");
            return;
        }

        if (!_widget) {
            NSLog(@"[Coordinator] ⚠️ No widget available");
            return;
        }

        // Get selection range
        size_t selStart, selLength;
        _widget->getSelectionRange(selStart, selLength);

        NSRange range = NSMakeRange(selStart, selLength);
        NSLog(@"[Coordinator] Triggering Writing Tools for range [%lu, %lu]", (unsigned long)selStart, (unsigned long)selLength);

        // Trigger Writing Tools using the coordinator
        // Try different method signatures
        BOOL invoked = NO;

        // Try: beginWritingToolsForRange:inView:
        SEL beginSel1 = NSSelectorFromString(@"beginWritingToolsForRange:inView:");
        if ([_writingToolsCoordinator respondsToSelector:beginSel1]) {
            NSMethodSignature *signature = [_writingToolsCoordinator methodSignatureForSelector:beginSel1];
            NSInvocation *invocation = [NSInvocation invocationWithMethodSignature:signature];
            [invocation setTarget:_writingToolsCoordinator];
            [invocation setSelector:beginSel1];
            [invocation setArgument:&range atIndex:2];
            id view = self;
            [invocation setArgument:&view atIndex:3];
            [invocation invoke];
            NSLog(@"[Coordinator] ✅ Writing Tools invoked via beginWritingToolsForRange:inView:");
            invoked = YES;
        }

        // Try: beginWritingTools
        if (!invoked) {
            SEL beginSel2 = NSSelectorFromString(@"beginWritingTools");
            if ([_writingToolsCoordinator respondsToSelector:beginSel2]) {
                [_writingToolsCoordinator performSelector:beginSel2];
                NSLog(@"[Coordinator] ✅ Writing Tools invoked via beginWritingTools");
                invoked = YES;
            }
        }

        // Try: showWritingTools
        if (!invoked) {
            SEL beginSel3 = NSSelectorFromString(@"showWritingTools");
            if ([_writingToolsCoordinator respondsToSelector:beginSel3]) {
                [_writingToolsCoordinator performSelector:beginSel3];
                NSLog(@"[Coordinator] ✅ Writing Tools invoked via showWritingTools");
                invoked = YES;
            }
        }

        if (!invoked) {
            NSLog(@"[Coordinator] ⚠️ Could not find begin method");
            // Log all available methods
            unsigned int methodCount;
            Method *methods = class_copyMethodList([_writingToolsCoordinator class], &methodCount);
            NSLog(@"[Coordinator] Available instance methods:");
            for (unsigned int i = 0; i < methodCount; i++) {
                SEL selector = method_getName(methods[i]);
                NSLog(@"  - %@", NSStringFromSelector(selector));
            }
            free(methods);
        }
    }
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

// MARK: - NSTextInputClient Protocol (Required for Writing Tools Coordinator)

- (void)insertText:(id)string replacementRange:(NSRange)replacementRange {
    if (!_widget) return;

    NSString* nsText = [string isKindOfClass:[NSAttributedString class]] ?
                      [(NSAttributedString*)string string] : (NSString*)string;

    if (replacementRange.location == NSNotFound) {
        // Replace current selection
        _widget->replaceSelection([nsText UTF8String]);
    } else {
        // Replace specific range
        _widget->setSelection(replacementRange.location, replacementRange.length);
        _widget->replaceSelection([nsText UTF8String]);
    }

    [self setNeedsDisplay:YES];
    NSLog(@"[Coordinator] Inserted text: %@", nsText);
}

- (void)setMarkedText:(id)string selectedRange:(NSRange)selectedRange replacementRange:(NSRange)replacementRange {
    // For IME input - not needed for Writing Tools, but required by protocol
}

- (void)unmarkText {
    // For IME input - not needed for Writing Tools, but required by protocol
}

- (NSRange)selectedRange {
    if (!_widget) return NSMakeRange(NSNotFound, 0);

    size_t selStart, selLength;
    _widget->getSelectionRange(selStart, selLength);
    return NSMakeRange(selStart, selLength);
}

- (NSRange)markedRange {
    // No marked text in our simple implementation
    return NSMakeRange(NSNotFound, 0);
}

- (BOOL)hasMarkedText {
    return NO;
}

- (nullable NSAttributedString *)attributedSubstringForProposedRange:(NSRange)range actualRange:(nullable NSRangePointer)actualRange {
    if (!_widget) return nil;

    std::string text = _widget->getText();
    NSString* nsText = [NSString stringWithUTF8String:text.c_str()];

    if (range.location >= [nsText length]) {
        if (actualRange) *actualRange = NSMakeRange(NSNotFound, 0);
        return nil;
    }

    // Clamp range to valid bounds
    NSRange validRange = range;
    if (NSMaxRange(validRange) > [nsText length]) {
        validRange.length = [nsText length] - validRange.location;
    }

    if (actualRange) *actualRange = validRange;

    NSString* substring = [nsText substringWithRange:validRange];
    return [[NSAttributedString alloc] initWithString:substring attributes:@{NSFontAttributeName: _font}];
}

- (NSArray<NSAttributedStringKey> *)validAttributesForMarkedText {
    return @[NSFontAttributeName, NSForegroundColorAttributeName];
}

- (NSRect)firstRectForCharacterRange:(NSRange)range actualRange:(nullable NSRangePointer)actualRange {
    // Return rectangle for character range (used by input methods)
    NSRect textRect = [self textRect];

    if (actualRange) *actualRange = range;

    // Return a rect at the selection position
    return NSMakeRect(textRect.origin.x, textRect.origin.y, 100, 20);
}

// MARK: - NSWritingToolsCoordinatorDelegate Methods (macOS 15+)

// Called when Writing Tools requests the current text context
- (void)writingToolsCoordinator:(id)coordinator
            requestsContextInRange:(NSRange)range
                        completion:(void (^)(id context))completion API_AVAILABLE(macos(15.0)) {
    if (!_widget) {
        completion(nil);
        return;
    }

    std::string text = _widget->getText();
    NSString* nsText = [NSString stringWithUTF8String:text.c_str()];

    // Get selection range
    size_t selStart, selLength;
    _widget->getSelectionRange(selStart, selLength);

    // Create attributed string with text context
    NSDictionary* attrs = @{NSFontAttributeName: _font};
    NSAttributedString* attrString = [[NSAttributedString alloc] initWithString:nsText attributes:attrs];

    // Create context object using runtime lookup (API may not be available at compile time)
    Class contextClass = NSClassFromString(@"NSWritingToolsContext");
    if (contextClass) {
        SEL initSel = NSSelectorFromString(@"initWithAttributedString:range:");
        if ([contextClass instancesRespondToSelector:initSel]) {
            id context = [[contextClass alloc] performSelector:initSel withObject:attrString withObject:[NSValue valueWithRange:NSMakeRange(selStart, selLength)]];
            NSLog(@"[Coordinator] Provided context: %lu chars, selection [%lu, %lu]", (unsigned long)[nsText length], (unsigned long)selStart, (unsigned long)selLength);
            completion(context);
            return;
        }
    }

    NSLog(@"[Coordinator] Could not create context - API not available");
    completion(nil);
}

// Called when Writing Tools wants to replace text
- (void)writingToolsCoordinator:(id)coordinator
                    replaceRange:(NSRange)range
                         inContext:(id)context
                       proposedText:(NSAttributedString *)proposedText
                            reason:(NSInteger)reason
                animationParameters:(id)animationParameters
                        completion:(void (^)(void))completion API_AVAILABLE(macos(15.0)) {
    if (!_widget) {
        if (completion) completion();
        return;
    }

    NSString* newText = [proposedText string];
    NSLog(@"[Coordinator] Replacing range [%lu, %lu] with %lu chars (reason: %ld)",
          (unsigned long)range.location, (unsigned long)range.length,
          (unsigned long)[newText length], (long)reason);

    // Replace the text in the widget
    _widget->setSelection(range.location, range.length);
    _widget->replaceSelection([newText UTF8String]);

    // Update display
    [self setNeedsDisplay:YES];

    if (completion) completion();
}

// Called when Writing Tools session begins
- (void)writingToolsCoordinatorWillBegin:(id)coordinator API_AVAILABLE(macos(15.0)) {
    _isWritingToolsActive = YES;
    [self setNeedsDisplay:YES];
    NSLog(@"[Coordinator] 🟢 Writing Tools session STARTED");
}

// Called when Writing Tools session ends
- (void)writingToolsCoordinatorDidEnd:(id)coordinator API_AVAILABLE(macos(15.0)) {
    _isWritingToolsActive = NO;
    [self setNeedsDisplay:YES];
    NSLog(@"[Coordinator] 🔴 Writing Tools session ENDED");
}

// Optional: Return ranges that should be ignored (e.g., code blocks, URLs)
- (NSArray *)writingToolsCoordinator:(id)coordinator
    ignoredRangesInEnclosingRange:(NSRange)enclosingRange API_AVAILABLE(macos(15.0)) {
    NSLog(@"[Coordinator] Ignored ranges requested");
    return @[]; // No ignored ranges for now
}

@end

// C interface for creating the coordinator view from C++
extern "C" {
    void* CreateCoordinatorTextWidgetView(double x, double y, double width, double height) {
        NSRect frame = NSMakeRect(x, y, width, height);
        CoordinatorTextWidgetView* view = [[CoordinatorTextWidgetView alloc] initWithFrame:frame];
        return (__bridge_retained void*)view;
    }

    void SetWidgetForCoordinatorView(void* viewPtr, CustomTextWidget* widget) {
        CoordinatorTextWidgetView* view = (__bridge CoordinatorTextWidgetView*)viewPtr;
        [view setWidget:widget];
        [view setNeedsDisplay:YES];  // Trigger initial draw
    }
}
