#!/bin/bash

# Script to download AI service icons
# You can manually add PNG/JPEG icons to Assets.xcassets/ServiceIcons/

echo "Creating icon asset structure..."

# Create directory for service icons
ICON_DIR="AIWebAppHub/AIWebAppHub/Resources/Assets.xcassets/ServiceIcons"
mkdir -p "$ICON_DIR"

# Function to create an image set
create_imageset() {
    local name=$1
    local iconset_dir="$ICON_DIR/${name}.imageset"

    mkdir -p "$iconset_dir"

    # Create Contents.json
    cat > "$iconset_dir/Contents.json" <<EOF
{
  "images" : [
    {
      "filename" : "${name}.png",
      "idiom" : "universal",
      "scale" : "1x"
    },
    {
      "filename" : "${name}@2x.png",
      "idiom" : "universal",
      "scale" : "2x"
    },
    {
      "filename" : "${name}@3x.png",
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

    echo "✓ Created imageset structure for: $name"
    echo "  📁 $iconset_dir"
    echo "  → Add your icon files: ${name}.png, ${name}@2x.png, ${name}@3x.png"
    echo ""
}

# Create image sets for each service
echo ""
echo "Creating image sets for all services..."
echo "========================================"
echo ""

create_imageset "chatgpt"
create_imageset "claude"
create_imageset "gemini"
create_imageset "grok"
create_imageset "github"

echo "========================================"
echo "✅ Icon structure created!"
echo ""
echo "📝 Next Steps:"
echo "1. Download or create icons for each service (PNG format recommended)"
echo "2. Place them in the respective .imageset folders:"
echo "   - chatgpt.png, chatgpt@2x.png, chatgpt@3x.png (or just one)"
echo "   - claude.png, claude@2x.png, claude@3x.png"
echo "   - gemini.png, gemini@2x.png, gemini@3x.png"
echo "   - grok.png, grok@2x.png, grok@3x.png"
echo "   - github.png, github@2x.png, github@3x.png"
echo ""
echo "💡 Tips:"
echo "   - Recommended size: 512x512px for @1x (will be scaled down)"
echo "   - If you only have one size, copy it as all three (@1x, @2x, @3x)"
echo "   - PNG format with transparency works best"
echo "   - You can find icons at: https://lobehub.com/icons or create your own"
echo ""
echo "🔍 Where to find icons:"
echo "   - Lobe Hub: https://lobehub.com/icons"
echo "   - Official websites (save favicons)"
echo "   - Icon libraries: flaticon.com, icons8.com"
echo ""
