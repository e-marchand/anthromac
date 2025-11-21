#import <Cocoa/Cocoa.h>
#include "CustomTextWidget.h"
#include <iostream>

// Forward declarations from CustomTextWidgetView.mm (Services approach)
extern "C" {
    void* CreateCustomTextWidgetView(double x, double y, double width, double height);
    void SetWidgetForView(void* viewPtr, CustomTextWidget* widget);
}

// Forward declarations from CoordinatorTextWidgetView.mm (Coordinator API approach)
extern "C" {
    void* CreateCoordinatorTextWidgetView(double x, double y, double width, double height);
    void SetWidgetForCoordinatorView(void* viewPtr, CustomTextWidget* widget);
}

@interface AppDelegate : NSObject <NSApplicationDelegate>
@property (strong, nonatomic) NSWindow* window;
@property (assign, nonatomic) CustomTextWidget* widgetServices;
@property (assign, nonatomic) CustomTextWidget* widgetCoordinator;
@end

@implementation AppDelegate

- (void)setupMenuBar {
    // Create main menu bar
    NSMenu* mainMenu = [[NSMenu alloc] init];

    // App Menu
    NSMenuItem* appMenuItem = [[NSMenuItem alloc] init];
    NSMenu* appMenu = [[NSMenu alloc] init];
    [appMenu addItemWithTitle:@"Quit" action:@selector(terminate:) keyEquivalent:@"q"];
    [appMenuItem setSubmenu:appMenu];
    [mainMenu addItem:appMenuItem];

    // Edit Menu (CRITICAL for Services!)
    NSMenuItem* editMenuItem = [[NSMenuItem alloc] initWithTitle:@"Edit" action:nil keyEquivalent:@""];
    NSMenu* editMenu = [[NSMenu alloc] initWithTitle:@"Edit"];

    [editMenu addItemWithTitle:@"Copy" action:@selector(copy:) keyEquivalent:@"c"];
    [editMenu addItemWithTitle:@"Paste" action:@selector(paste:) keyEquivalent:@"v"];
    [editMenu addItemWithTitle:@"Select All" action:@selector(selectAll:) keyEquivalent:@"a"];

    [editMenu addItem:[NSMenuItem separatorItem]];

    // THIS IS CRITICAL: Services submenu
    NSMenuItem* servicesMenuItem = [[NSMenuItem alloc] initWithTitle:@"Services" action:nil keyEquivalent:@""];
    NSMenu* servicesMenu = [[NSMenu alloc] initWithTitle:@"Services"];
    [servicesMenuItem setSubmenu:servicesMenu];
    [editMenu addItem:servicesMenuItem];

    // Register the services menu with NSApplication
    [[NSApplication sharedApplication] setServicesMenu:servicesMenu];

    [editMenuItem setSubmenu:editMenu];
    [mainMenu addItem:editMenuItem];

    // Set the main menu
    [[NSApplication sharedApplication] setMainMenu:mainMenu];

    NSLog(@"✅ Menu bar set up with Services submenu");
}

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    // Set up application menu with Services
    [self setupMenuBar];

    // Create main window - wider to fit two widgets side by side
    NSRect frame = NSMakeRect(0, 0, 1200, 600);
    NSWindowStyleMask style = NSWindowStyleMaskTitled |
                              NSWindowStyleMaskClosable |
                              NSWindowStyleMaskMiniaturizable |
                              NSWindowStyleMaskResizable;

    self.window = [[NSWindow alloc] initWithContentRect:frame
                                              styleMask:style
                                                backing:NSBackingStoreBuffered
                                                  defer:NO];

    [self.window setTitle:@"Writing Tools Demo: Two Approaches Side-by-Side"];
    [self.window center];

    // Create container view
    NSView* containerView = [[NSView alloc] initWithFrame:frame];

    // =================================================================
    // LEFT WIDGET: NSServicesMenuRequestor (Services menu approach)
    // =================================================================

    self.widgetServices = new CustomTextWidget();
    std::string servicesText =
        "LEFT: NSServicesMenuRequestor\n\n"
        "This widget uses the Services menu approach.\n\n"
        "To test:\n"
        "1. Click and drag to select text\n"
        "2. Right-click → Services\n"
        "3. Choose Writing Tools options\n\n"
        "This is the traditional way to integrate with macOS Services.";

    self.widgetServices->setText(servicesText);

    void* servicesViewPtr = CreateCustomTextWidgetView(0, 70, 590, 480);
    SetWidgetForView(servicesViewPtr, self.widgetServices);

    NSView* servicesView = (__bridge NSView*)servicesViewPtr;
    servicesView.autoresizingMask = NSViewHeightSizable | NSViewMaxXMargin;

    // Label for services widget
    NSTextField* servicesLabel = [[NSTextField alloc] initWithFrame:NSMakeRect(10, 555, 580, 40)];
    [servicesLabel setStringValue:@"📋 SERVICES APPROACH: NSServicesMenuRequestor\nRight-click → Services → Writing Tools"];
    [servicesLabel setBezeled:YES];
    [servicesLabel setDrawsBackground:YES];
    [servicesLabel setBackgroundColor:[[NSColor systemBlueColor] colorWithAlphaComponent:0.1]];
    [servicesLabel setEditable:NO];
    [servicesLabel setSelectable:NO];
    [servicesLabel setFont:[NSFont boldSystemFontOfSize:10]];
    [servicesLabel setTextColor:[NSColor systemBlueColor]];
    servicesLabel.autoresizingMask = NSViewMaxXMargin | NSViewMaxYMargin;

    // =================================================================
    // RIGHT WIDGET: NSWritingToolsCoordinator (modern inline approach)
    // =================================================================

    self.widgetCoordinator = new CustomTextWidget();
    std::string coordinatorText =
        "RIGHT: NSWritingToolsCoordinator\n\n"
        "This widget uses the modern Writing Tools Coordinator API.\n\n"
        "To test:\n"
        "1. Click and drag to select text\n"
        "2. Right-click for inline UI\n"
        "3. Yellow border when active\n\n"
        "This is the modern API with inline Writing Tools UI and delegate callbacks.";

    self.widgetCoordinator->setText(coordinatorText);

    void* coordinatorViewPtr = CreateCoordinatorTextWidgetView(610, 70, 590, 480);
    SetWidgetForCoordinatorView(coordinatorViewPtr, self.widgetCoordinator);

    NSView* coordinatorView = (__bridge NSView*)coordinatorViewPtr;
    coordinatorView.autoresizingMask = NSViewHeightSizable | NSViewMinXMargin;

    // Label for coordinator widget
    NSTextField* coordinatorLabel = [[NSTextField alloc] initWithFrame:NSMakeRect(610, 555, 580, 40)];
    [coordinatorLabel setStringValue:@"✨ COORDINATOR APPROACH: NSWritingToolsCoordinator\nInline UI + Delegate callbacks (macOS 15+)"];
    [coordinatorLabel setBezeled:YES];
    [coordinatorLabel setDrawsBackground:YES];
    [coordinatorLabel setBackgroundColor:[[NSColor systemYellowColor] colorWithAlphaComponent:0.1]];
    [coordinatorLabel setEditable:NO];
    [coordinatorLabel setSelectable:NO];
    [coordinatorLabel setFont:[NSFont boldSystemFontOfSize:10]];
    [coordinatorLabel setTextColor:[NSColor systemYellowColor]];
    coordinatorLabel.autoresizingMask = NSViewMinXMargin | NSViewMaxYMargin;

    // Add top instruction label
    NSTextField* instructionsLabel = [[NSTextField alloc] initWithFrame:NSMakeRect(10, 5, 1180, 60)];
    [instructionsLabel setStringValue:@"Two different approaches to integrating Apple Intelligence Writing Tools:\n🔹 LEFT uses Services menu (traditional) • RIGHT uses Coordinator API (modern inline)\nBoth work with custom C++ GUI widgets without NSTextField/NSTextView!"];
    [instructionsLabel setBezeled:NO];
    [instructionsLabel setDrawsBackground:YES];
    [instructionsLabel setBackgroundColor:[NSColor controlBackgroundColor]];
    [instructionsLabel setEditable:NO];
    [instructionsLabel setSelectable:NO];
    [instructionsLabel setFont:[NSFont systemFontOfSize:11]];
    [instructionsLabel setTextColor:[NSColor secondaryLabelColor]];
    [instructionsLabel setAlignment:NSTextAlignmentCenter];
    instructionsLabel.autoresizingMask = NSViewWidthSizable | NSViewMaxYMargin;

    // Add all views to container
    [containerView addSubview:servicesView];
    [containerView addSubview:coordinatorView];
    [containerView addSubview:servicesLabel];
    [containerView addSubview:coordinatorLabel];
    [containerView addSubview:instructionsLabel];

    [self.window setContentView:containerView];
    [self.window makeKeyAndOrderFront:nil];

    // Force display of both widgets after window is visible
    [servicesView setNeedsDisplay:YES];
    [coordinatorView setNeedsDisplay:YES];

    // Log instructions
    NSLog(@"====================================================================");
    NSLog(@"Writing Tools Demo - Two Approaches Side-by-Side");
    NSLog(@"====================================================================");
    NSLog(@"LEFT:  NSServicesMenuRequestor (Services menu)");
    NSLog(@"RIGHT: NSWritingToolsCoordinator (inline UI + delegates)");
    NSLog(@"");
    NSLog(@"Both approaches work with custom C++ text widgets!");
    NSLog(@"====================================================================");
    NSLog(@"Requirements: macOS 15+ with Apple Intelligence enabled");
    NSLog(@"====================================================================");
}

- (void)applicationWillTerminate:(NSNotification *)notification {
    if (self.widgetServices) {
        delete self.widgetServices;
        self.widgetServices = nullptr;
    }
    if (self.widgetCoordinator) {
        delete self.widgetCoordinator;
        self.widgetCoordinator = nullptr;
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
