#!/bin/bash

# Build script for daily-wallpaper Arch package

echo "Building daily-wallpaper Arch package..."

# Change to the script directory
cd "$(dirname "$0")"

# Verify all necessary files exist
for file in daily-wallpaper.py daily-wallpaper.service daily-wallpaper.timer PKGBUILD daily-wallpaper.install; do
  if [ ! -f "$file" ]; then
    echo "Error: Required file $file not found!"
    exit 1
  fi
done

# Build the package
makepkg -f

echo ""
echo "Build complete. To install, run: sudo pacman -U daily-wallpaper-*.pkg.tar.zst"
echo "Or to build and install in one step, run: makepkg -si"
