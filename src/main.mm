#import <Cocoa/Cocoa.h>
#include "CustomTextWidget.h"
#include <iostream>

// Forward declarations from CustomTextWidgetView.mm
extern "C" {
    void* CreateCustomTextWidgetView(double x, double y, double width, double height);
    void SetWidgetForView(void* viewPtr, CustomTextWidget* widget);
}

@interface AppDelegate : NSObject <NSApplicationDelegate>
@property (strong, nonatomic) NSWindow* window;
@property (assign, nonatomic) CustomTextWidget* widget;
@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    // Create main window
    NSRect frame = NSMakeRect(0, 0, 800, 600);
    NSWindowStyleMask style = NSWindowStyleMaskTitled |
                              NSWindowStyleMaskClosable |
                              NSWindowStyleMaskMiniaturizable |
                              NSWindowStyleMaskResizable;

    self.window = [[NSWindow alloc] initWithContentRect:frame
                                              styleMask:style
                                                backing:NSBackingStoreBuffered
                                                  defer:NO];

    [self.window setTitle:@"Custom Text Widget - Apple Intelligence Writing Tools Demo"];
    [self.window center];

    // Create C++ widget
    self.widget = new CustomTextWidget();

    // Set initial text
    std::string initialText =
        "This is a custom C++ text widget that supports Apple Intelligence Writing Tools!\n\n"
        "To test Writing Tools:\n"
        "1. Click on the text to select it\n"
        "2. Right-click (or Control+click) to open the context menu\n"
        "3. Look for 'Writing Tools' in the Services submenu\n"
        "4. Select options like 'Summarize', 'Proofread', 'Rewrite', etc.\n\n"
        "The text will be sent to Apple Intelligence and the results will appear here!\n\n"
        "This demonstrates how to integrate Writing Tools with custom GUI widgets "
        "that don't use standard NSTextField or NSTextView. "
        "The implementation uses NSServicesMenuRequestor protocol to bridge "
        "between your custom C++ rendering and macOS native AI features.";

    self.widget->setText(initialText);

    // Create custom view (Objective-C++ NSView)
    void* viewPtr = CreateCustomTextWidgetView(0, 0, 800, 600);
    SetWidgetForView(viewPtr, self.widget);

    NSView* customView = (__bridge NSView*)viewPtr;
    customView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;

    // Add instructions label
    NSTextField* instructionsLabel = [[NSTextField alloc] initWithFrame:NSMakeRect(10, 560, 780, 30)];
    [instructionsLabel setStringValue:@"Click text, then right-click → Services → Writing Tools to test AI features (Summarize, Proofread, Rewrite, etc.)"];
    [instructionsLabel setBezeled:NO];
    [instructionsLabel setDrawsBackground:NO];
    [instructionsLabel setEditable:NO];
    [instructionsLabel setSelectable:NO];
    [instructionsLabel setFont:[NSFont boldSystemFontOfSize:12]];
    [instructionsLabel setTextColor:[NSColor secondaryLabelColor]];
    instructionsLabel.autoresizingMask = NSViewWidthSizable | NSViewMinYMargin;

    // Create container view
    NSView* containerView = [[NSView alloc] initWithFrame:frame];
    [containerView addSubview:customView];
    [containerView addSubview:instructionsLabel];

    [self.window setContentView:containerView];
    [self.window makeKeyAndOrderFront:nil];

    // Log instructions
    NSLog(@"===========================================");
    NSLog(@"Custom Text Widget with Writing Tools Demo");
    NSLog(@"===========================================");
    NSLog(@"To use Writing Tools:");
    NSLog(@"1. Click on the text area to select it");
    NSLog(@"2. Right-click to open context menu");
    NSLog(@"3. Navigate to Services > Writing Tools");
    NSLog(@"4. Choose an option (Summarize, Proofread, etc.)");
    NSLog(@"===========================================");
}

- (void)applicationWillTerminate:(NSNotification *)notification {
    if (self.widget) {
        delete self.widget;
        self.widget = nullptr;
    }
}

- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {
    return YES;
}

@end

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        NSApplication* app = [NSApplication sharedApplication];
        AppDelegate* delegate = [[AppDelegate alloc] init];
        [app setDelegate:delegate];
        [app run];
    }
    return 0;
}
