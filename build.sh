#!/bin/bash

# PathOpener Build Script
# This script builds the PathOpener macOS application

set -e

echo "🔨 Building PathOpener..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf ./build

# Build the project
echo "⚙️  Compiling..."
xcodebuild -project PathOpener/PathOpener.xcodeproj \
           -scheme PathOpener \
           -configuration Release \
           -derivedDataPath ./build \
           clean build

# Copy to convenient location
echo "📦 Packaging..."
cp -R ./build/Build/Products/Release/PathOpener.app ./PathOpener.app

echo "✅ Build complete!"
echo ""
echo "📍 Built app location: ./PathOpener.app"
echo ""
echo "To run:"
echo "  ./PathOpener.app/Contents/MacOS/PathOpener"
echo ""
echo "To install to Applications:"
echo "  cp -R ./PathOpener.app /Applications/"
