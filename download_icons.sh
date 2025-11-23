#!/bin/bash

# Script to download AI service icons from Lobe Hub CDN
# These will be added to the Assets.xcassets folder

echo "Downloading AI service icons from Lobe Hub CDN..."

# Create directory for downloaded icons
ICON_DIR="AIWebAppHub/AIWebAppHub/Resources/Assets.xcassets/ServiceIcons"
mkdir -p "$ICON_DIR"

# Base URL for Lobe Hub icons
BASE_URL="https://registry.npmmirror.com/@lobehub/icons-static-png/latest/files/dark"

# Array of services to download
declare -A SERVICES=(
    ["chatgpt"]="ChatGPT"
    ["claude"]="Claude"
    ["gemini"]="Gemini"
    ["grok"]="Grok"
    ["github"]="GitHub"
)

# Download each icon
for icon in "${!SERVICES[@]}"; do
    name="${SERVICES[$icon]}"
    echo "Downloading $name icon..."

    # Create icon set directory
    ICONSET_DIR="$ICON_DIR/${icon}.imageset"
    mkdir -p "$ICONSET_DIR"

    # Download PNG files (1x, 2x, 3x)
    curl -L -o "$ICONSET_DIR/${icon}.png" "$BASE_URL/${icon}.png" 2>/dev/null
    curl -L -o "$ICONSET_DIR/${icon}@2x.png" "$BASE_URL/${icon}.png" 2>/dev/null
    curl -L -o "$ICONSET_DIR/${icon}@3x.png" "$BASE_URL/${icon}.png" 2>/dev/null

    # Create Contents.json for the image set
    cat > "$ICONSET_DIR/Contents.json" <<EOF
{
  "images" : [
    {
      "filename" : "${icon}.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "${icon}@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "${icon}@3x.png",
      "idiom" : "universal",
      "scale" : "3x"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  },
  "properties" : {
    "template-rendering-intent" : "original"
  }
}
EOF

    echo "✓ Downloaded $name icon"
done

echo ""
echo "✅ All icons downloaded successfully!"
echo "Icons are located in: $ICON_DIR"
echo ""
echo "To use these icons in your app:"
echo "1. Open the Xcode project"
echo "2. The icons will appear in Assets.xcassets/ServiceIcons"
echo "3. Use them in code with: Image(\"chatgpt\"), Image(\"claude\"), etc."
