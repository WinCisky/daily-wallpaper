#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- CONFIGURATION ---
IMAGE_ENDPOINT="https://wallpapers.opentrust.it"
WALLPAPER_DIR="/usr/share/dynamic-wallpaper"
WALLPAPER_PATH="$WALLPAPER_DIR/current_wallpaper.jpg"
TMP_WALLPAPER_PATH="$WALLPAPER_PATH.tmp"
# --- END CONFIGURATION ---

# Ensure the target directory exists
mkdir -p "$WALLPAPER_DIR"

# First, get the actual wallpaper URL from the endpoint
echo "Fetching wallpaper URL from $IMAGE_ENDPOINT"
ACTUAL_IMAGE_URL=$(curl -sSfL "$IMAGE_ENDPOINT")
echo "Response headers: $ACTUAL_IMAGE_URL"

if [ -z "$ACTUAL_IMAGE_URL" ]; then
    echo "Failed to get a redirect URL from $IMAGE_ENDPOINT."
    exit 1
fi

echo "Got wallpaper URL: $ACTUAL_IMAGE_URL"

# Download the new wallpaper using the acquired URL
echo "Downloading wallpaper to $TMP_WALLPAPER_PATH"
if curl -sSfL "$ACTUAL_IMAGE_URL" -o "$TMP_WALLPAPER_PATH"; then
    # Move the temporary file to the final destination if download was successful
    mv "$TMP_WALLPAPER_PATH" "$WALLPAPER_PATH"
    chmod 644 "$WALLPAPER_PATH" # Ensure it's readable by all users
    echo "Wallpaper downloaded and saved to $WALLPAPER_PATH"
else
    echo "Failed to download wallpaper from $ACTUAL_IMAGE_URL."
    # Clean up temp file if it exists
    [ -f "$TMP_WALLPAPER_PATH" ] && rm "$TMP_WALLPAPER_PATH"
    exit 1
fi


# Loop through users with active sessions
for user in $(who | cut -d' ' -f1 | sort | uniq); do
  # Get user id
  uid=$(id -u "$user")
  
  # Try to get HYPRLAND_INSTANCE_SIGNATURE from user environment
  hypr_signature=$(sudo -u "$user" bash -c 'echo $HYPRLAND_INSTANCE_SIGNATURE')
  
  if [ -n "$hypr_signature" ]; then
    echo "Found active Hyprland session for user $user"
    
    # Use the user's Hyprland session to reload the wallpaper
    sudo -u "$user" bash -c "HYPRLAND_INSTANCE_SIGNATURE=$hypr_signature hyprctl hyprpaper preload \"$WALLPAPER_PATH\""
    sudo -u "$user" bash -c "HYPRLAND_INSTANCE_SIGNATURE=$hypr_signature hyprctl hyprpaper wallpaper \",${WALLPAPER_PATH}\""
    
    echo "Directly set wallpaper for $user's Hyprland session"
  fi
  
  # Also check if we can find the socket directly in XDG_RUNTIME_DIR
  if [ -d "/run/user/$uid" ]; then
    for socket in /run/user/$uid/hypr/*/.hyprpaper.sock; do
      if [ -S "$socket" ]; then
        echo "Found hyprpaper socket at $socket for user $user"
        
        # Extract the instance path from the socket path
        instance_dir=$(dirname "$socket")
        instance_id=$(basename "$instance_dir")
        
        # Use the socket to reload the wallpaper
        sudo -u "$user" bash -c "HYPRLAND_INSTANCE_SIGNATURE=$instance_id hyprctl hyprpaper preload \"$WALLPAPER_PATH\""
        sudo -u "$user" bash -c "HYPRLAND_INSTANCE_SIGNATURE=$instance_id hyprctl hyprpaper wallpaper \",${WALLPAPER_PATH}\""
        
        echo "Used socket to set wallpaper for $user's Hyprland session"
      fi
    done
  fi
done

exit 0
