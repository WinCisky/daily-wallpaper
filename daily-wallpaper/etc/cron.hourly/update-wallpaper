#!/usr/bin/env python3
import requests
import subprocess

endpoint = "https://wallpapers.opentrust.it"

try:
    response = requests.get(endpoint)
    response.raise_for_status()
    image_url = response.text.strip()
    image_path = "/tmp/background.jpg"

    # Download the image
    img_data = requests.get(image_url).content
    with open(image_path, 'wb') as f:
        f.write(img_data)

    # Check the current color scheme
    color_scheme = subprocess.check_output([
        "gsettings", "get", "org.gnome.desktop.interface", "color-scheme"
    ]).decode().strip().strip("'")

    # Use picture-uri-dark if prefer-dark, else picture-uri
    if color_scheme == "prefer-dark":
        key = "picture-uri-dark"
    else:
        key = "picture-uri"

    # Set as background (GNOME desktop)
    subprocess.run([
        "gsettings", "set",
        "org.gnome.desktop.background", key,
        f"file://{image_path}"
    ], check=True)

except Exception as e:
    print(f"Failed to update wallpaper: {e}")
