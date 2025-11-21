# Makefile for Custom Text Widget with Apple Intelligence Writing Tools
# Requires macOS 15+ (Sequoia) for Writing Tools support

# Compiler and flags
CXX = clang++
OBJCXX = clang++
CXXFLAGS = -std=c++17 -Wall -Wextra -Iinclude
OBJCXXFLAGS = -std=c++17 -Wall -Wextra -Iinclude -fobjc-arc
LDFLAGS = -framework Cocoa -framework Foundation
TARGET_MACOS = -mmacosx-version-min=15.0

# Directories
SRC_DIR = src
INC_DIR = include
BUILD_DIR = build
APP_NAME = WritingToolsDemo
APP_BUNDLE = $(BUILD_DIR)/$(APP_NAME).app
APP_CONTENTS = $(APP_BUNDLE)/Contents
APP_MACOS = $(APP_CONTENTS)/MacOS
APP_RESOURCES = $(APP_CONTENTS)/Resources

# Source files
CPP_SOURCES = $(SRC_DIR)/CustomTextWidget.cpp
OBJCXX_SOURCES = $(SRC_DIR)/CustomTextWidgetView.mm $(SRC_DIR)/main.mm

# Object files
CPP_OBJECTS = $(BUILD_DIR)/CustomTextWidget.o
OBJCXX_OBJECTS = $(BUILD_DIR)/CustomTextWidgetView.o $(BUILD_DIR)/main.o

# Targets
.PHONY: all clean run info

all: $(APP_BUNDLE)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(APP_MACOS):
	mkdir -p $(APP_MACOS)
	mkdir -p $(APP_RESOURCES)

# Compile C++ sources
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(TARGET_MACOS) -c $< -o $@

# Compile Objective-C++ sources
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.mm | $(BUILD_DIR)
	$(OBJCXX) $(OBJCXXFLAGS) $(TARGET_MACOS) -c $< -o $@

# Link the application
$(APP_MACOS)/$(APP_NAME): $(CPP_OBJECTS) $(OBJCXX_OBJECTS) | $(APP_MACOS)
	$(OBJCXX) $(TARGET_MACOS) $(CPP_OBJECTS) $(OBJCXX_OBJECTS) $(LDFLAGS) -o $@

# Create Info.plist
$(APP_CONTENTS)/Info.plist: | $(APP_MACOS)
	@echo '<?xml version="1.0" encoding="UTF-8"?>' > $@
	@echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">' >> $@
	@echo '<plist version="1.0">' >> $@
	@echo '<dict>' >> $@
	@echo '    <key>CFBundleExecutable</key>' >> $@
	@echo '    <string>$(APP_NAME)</string>' >> $@
	@echo '    <key>CFBundleIdentifier</key>' >> $@
	@echo '    <string>com.example.writingtoolsdemo</string>' >> $@
	@echo '    <key>CFBundleName</key>' >> $@
	@echo '    <string>$(APP_NAME)</string>' >> $@
	@echo '    <key>CFBundlePackageType</key>' >> $@
	@echo '    <string>APPL</string>' >> $@
	@echo '    <key>CFBundleShortVersionString</key>' >> $@
	@echo '    <string>1.0</string>' >> $@
	@echo '    <key>CFBundleVersion</key>' >> $@
	@echo '    <string>1</string>' >> $@
	@echo '    <key>LSMinimumSystemVersion</key>' >> $@
	@echo '    <string>15.0</string>' >> $@
	@echo '    <key>NSHighResolutionCapable</key>' >> $@
	@echo '    <true/>' >> $@
	@echo '    <key>NSPrincipalClass</key>' >> $@
	@echo '    <string>NSApplication</string>' >> $@
	@echo '</dict>' >> $@
	@echo '</plist>' >> $@

# Build the app bundle
$(APP_BUNDLE): $(APP_MACOS)/$(APP_NAME) $(APP_CONTENTS)/Info.plist
	@echo "Built app bundle: $(APP_BUNDLE)"
	@echo "You can run it with: open $(APP_BUNDLE)"

# Run the application
run: $(APP_BUNDLE)
	@echo "Launching $(APP_NAME)..."
	open $(APP_BUNDLE)

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)

# Show info about the project
info:
	@echo "=============================================="
	@echo "Writing Tools Demo - Custom C++ Text Widget"
	@echo "=============================================="
	@echo ""
	@echo "This project demonstrates how to integrate"
	@echo "Apple Intelligence Writing Tools with a"
	@echo "custom C++ GUI text widget on macOS."
	@echo ""
	@echo "Requirements:"
	@echo "  - macOS 15.0+ (Sequoia)"
	@echo "  - Apple Intelligence enabled"
	@echo "  - Xcode Command Line Tools"
	@echo ""
	@echo "Build commands:"
	@echo "  make        - Build the application"
	@echo "  make run    - Build and run the application"
	@echo "  make clean  - Clean build artifacts"
	@echo ""
	@echo "Usage:"
	@echo "  1. Click on the text to select it"
	@echo "  2. Right-click to open context menu"
	@echo "  3. Go to Services > Writing Tools"
	@echo "  4. Choose an AI option (Summarize, etc.)"
	@echo ""
	@echo "=============================================="
