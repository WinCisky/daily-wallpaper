#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- CONFIGURATION ---
IMAGE_URL="https://wallpapers.opentrust.it"
WALLPAPER_DIR="/usr/share/dynamic-wallpaper"
WALLPAPER_PATH="$WALLPAPER_DIR/current_wallpaper.jpg"
TMP_WALLPAPER_PATH="$WALLPAPER_PATH.tmp"
# --- END CONFIGURATION ---

# Ensure the target directory exists
mkdir -p "$WALLPAPER_DIR"

# Download the new wallpaper
echo "Downloading wallpaper from $IMAGE_URL to $TMP_WALLPAPER_PATH"
if curl -sSfL "$IMAGE_URL" -o "$TMP_WALLPAPER_PATH"; then
    # Move the temporary file to the final destination if download was successful
    mv "$TMP_WALLPAPER_PATH" "$WALLPAPER_PATH"
    chmod 644 "$WALLPAPER_PATH" # Ensure it's readable by all users
    echo "Wallpaper downloaded and saved to $WALLPAPER_PATH"
else
    echo "Failed to download wallpaper from $IMAGE_URL."
    # Clean up temp file if it exists
    [ -f "$TMP_WALLPAPER_PATH" ] && rm "$TMP_WALLPAPER_PATH"
    exit 1
fi

# Find active Hyprland sessions and set wallpaper for each
# We look for Hyprland's IPC socket directory
find /run/user/ -maxdepth 2 -type d -name 'hypr' 2>/dev/null | while read -r HYPR_DIR; do
    USER_UID=$(stat -c '%u' "$HYPR_DIR")
    USERNAME=$(id -nu "$USER_UID")

    if [ -n "$USERNAME" ] && [ -d "/run/user/$USER_UID" ]; then
        echo "Attempting to set wallpaper for user $USERNAME (UID $USER_UID)"
        # The HYPRLAND_INSTANCE_SIGNATURE is usually found by hyprctl automatically if XDG_RUNTIME_DIR is set.
        # The command structure for hyprpaper is `hyprctl hyprpaper wallpaper "MONITOR,PATH"`
        # Using an empty MONITOR field (e.g., ",PATH") applies to the current/default.
        # We run this as the target user.
        if sudo -u "$USERNAME" \
             env XDG_RUNTIME_DIR="/run/user/$USER_UID" \
             DISPLAY=:0 \ # Often needed for GUI context, though hyprctl might not strictly require it for this
             hyprctl hyprpaper wallpaper ",$WALLPAPER_PATH"; then
            echo "Wallpaper set for $USERNAME."
        else
            echo "Failed to set wallpaper for $USERNAME. Is hyprpaper running for this user?"
        fi
    else
        echo "Could not determine username for UID from $HYPR_DIR"
    fi
done

echo "Dynamic wallpaper script finished."