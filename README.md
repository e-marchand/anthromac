# Apple Intelligence Writing Tools - Custom C++ GUI Widget Demo

This project demonstrates how to integrate **Apple Intelligence Writing Tools** (Summarize, Proofread, Rewrite, etc.) with a **custom C++ GUI text widget** on macOS, without using standard AppKit controls like `NSTextField` or `NSTextView`.

## 🎯 What This Demo Does

- Implements a custom text widget in **C++** with custom rendering
- Bridges to macOS **Objective-C++** to access native Writing Tools
- Uses **NSServicesMenuRequestor protocol** to enable AI features
- Demonstrates the complete integration pipeline

## 📋 Requirements

- **macOS 15.0+** (Sequoia or later) - Writing Tools is only available on macOS 15+
- **Apple Intelligence enabled** in System Settings
- **Xcode Command Line Tools** installed
- Compatible Mac with Apple Silicon (M1/M2/M3) or Intel with macOS 15+

## 🏗️ Project Structure

```
anthromac/
├── include/
│   └── CustomTextWidget.h          # C++ text widget interface
├── src/
│   ├── CustomTextWidget.cpp        # C++ text widget implementation
│   ├── CustomTextWidgetView.mm     # Objective-C++ NSView bridge
│   └── main.mm                     # Application entry point
├── Makefile                        # Build configuration
└── README.md                       # This file
```

## 🔧 Building the Project

```bash
# Build the application
make

# Build and run
make run

# Clean build artifacts
make clean

# Show project information
make info
```

## 🚀 How to Use

1. **Build and run** the application:
   ```bash
   make run
   ```

2. **Click on the text** in the window to select it

3. **Right-click** (or Control+click) to open the context menu

4. Navigate to **Services → Writing Tools**

5. Choose an AI option:
   - **Summarize** - Create a summary of the text
   - **Proofread** - Check grammar and spelling
   - **Rewrite** - Rewrite in different styles (Professional, Friendly, Concise)
   - **Make Key Points** - Extract key points as bullet points
   - And more!

6. The AI-modified text will **replace the original text** in the custom widget

## 🔑 Key Implementation Details

### The Magic: NSServicesMenuRequestor Protocol

The core integration happens in `src/CustomTextWidgetView.mm`. Here's how it works:

#### 1. Declare Protocol Support
```objc
@interface CustomTextWidgetView : NSView <NSServicesMenuRequestor>
```

#### 2. Tell macOS This View Can Use Services
```objc
- (id)validRequestorForSendType:(NSPasteboardType)sendType
                     returnType:(NSPasteboardType)returnType {
    if ([sendType isEqualToString:NSPasteboardTypeString] ||
        [sendType isEqualToString:NSPasteboardTypeRTF]) {
        return self;  // We can participate!
    }
    return [super validRequestorForSendType:sendType returnType:returnType];
}
```

#### 3. Provide Text to Writing Tools
```objc
- (BOOL)writeSelectionToPasteboard:(NSPasteboard *)pboard
                             types:(NSArray<NSPasteboardType> *)types {
    // Get text from C++ widget
    std::string selectedText = _widget->getSelectedText();
    NSString* nsText = [NSString stringWithUTF8String:selectedText.c_str()];

    // Write to pasteboard
    [pboard setString:nsText forType:NSPasteboardTypeString];
    return YES;
}
```

#### 4. Receive Modified Text from Writing Tools
```objc
- (BOOL)readSelectionFromPasteboard:(NSPasteboard *)pboard {
    // Read AI-modified text
    NSString* nsText = [pboard stringForType:NSPasteboardTypeString];

    // Update C++ widget
    std::string cppText = [nsText UTF8String];
    _widget->replaceSelection(cppText);

    return YES;
}
```

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Your Custom C++ GUI (CustomTextWidget)            │
│  - Stores text as std::string                      │
│  - Manages selection                               │
│  - Platform-independent text logic                 │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Bridge via Objective-C++
                  │
┌─────────────────▼───────────────────────────────────┐
│  NSView + NSServicesMenuRequestor                  │
│  (CustomTextWidgetView.mm)                         │
│  - Implements protocol methods                     │
│  - Handles pasteboard communication                │
│  - Renders text using C++ widget data              │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ macOS Services/Pasteboard
                  │
┌─────────────────▼───────────────────────────────────┐
│  Apple Intelligence Writing Tools                   │
│  - Summarize, Proofread, Rewrite, etc.            │
│  - Runs on-device with Apple Silicon               │
└─────────────────────────────────────────────────────┘
```

## 🧩 Adapting for Your Own GUI

To integrate Writing Tools into **your own custom GUI widget**:

1. **Keep your C++ GUI logic separate** (like `CustomTextWidget.h/cpp`)
   - Store text content
   - Manage selection/cursor
   - Handle rendering

2. **Create an Objective-C++ bridge** (like `CustomTextWidgetView.mm`)
   - Subclass `NSView`
   - Adopt `NSServicesMenuRequestor` protocol
   - Implement three key methods:
     - `validRequestorForSendType:returnType:`
     - `writeSelectionToPasteboard:types:`
     - `readSelectionFromPasteboard:`

3. **Connect the bridge to your C++ widget**
   - Pass text from C++ to pasteboard
   - Receive AI results back from pasteboard
   - Update your C++ widget's text

4. **Make the view focusable**
   - Override `acceptsFirstResponder` to return `YES`
   - Override `canBecomeKeyView` to return `YES`

## 📝 Notes

- **macOS 15+ only**: Writing Tools is not available on older macOS versions
- **No private APIs**: This uses only public APIs via `NSServicesMenuRequestor`
- **No NSTextField/NSTextView**: Completely custom rendering
- **Works with any GUI**: OpenGL, Metal, SDL, custom rasterizers, etc.
- **On-device processing**: Apple Intelligence runs locally (when available)

## 🎓 Learning Resources

- [WWDC24: Get started with Writing Tools](https://developer.apple.com/videos/play/wwdc2024/10168/)
- [Apple Developer: Adding Writing Tools support to a custom NSView](https://developer.apple.com/documentation/appkit/adding-writing-tools-support-to-a-custom-nsview)
- [NSServicesMenuRequestor Protocol Reference](https://developer.apple.com/documentation/appkit/nsservicesmenurequestor)

## 🐛 Troubleshooting

**Writing Tools menu doesn't appear:**
- Ensure you're running macOS 15.0+
- Check that Apple Intelligence is enabled in System Settings
- Make sure the view is first responder (click on it first)
- Verify there's text selected or available

**Text doesn't update after AI processing:**
- Check that `readSelectionFromPasteboard:` is being called
- Verify the callback to refresh the view is working
- Look for errors in Console.app

**Build errors:**
- Ensure Xcode Command Line Tools are installed: `xcode-select --install`
- Check that you're targeting macOS 15.0+
- Verify Objective-C ARC is enabled (`-fobjc-arc`)

## 📄 License

This is a demonstration/educational project. Feel free to adapt it for your own use!

## 🤝 Contributing

This is a test project to demonstrate Writing Tools integration. If you have improvements or find issues, feel free to experiment!

---

**Happy coding with Apple Intelligence! 🎉**