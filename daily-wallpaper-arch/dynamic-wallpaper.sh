#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# --- CONFIGURATION ---
IMAGE_ENDPOINT="https://wallpapers.opentrust.it"
# Check if /share/dynamic-wallpaper exists, otherwise fallback to /usr/share/dynamic-wallpaper
if [ -d "/share/dynamic-wallpaper" ]; then
    WALLPAPER_DIR="/share/dynamic-wallpaper"
else
    WALLPAPER_DIR="/usr/share/dynamic-wallpaper"
fi
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


# Function to set wallpaper for a user
set_wallpaper_for_user() {
  local user=$1
  local home_dir=$(eval echo ~$user)
  local uid=$(id -u "$user")
  
  # Multiple methods to detect a Wayland session
  echo "Checking for Wayland session for user $user..."
  
  # Method 1: Check if Hyprland is running for this user
  if sudo -u "$user" pgrep -x Hyprland >/dev/null; then
    echo "Hyprland is running for user $user"
  # Method 2: Check if there's a wayland socket
  elif [ -e "/run/user/$uid/wayland-0" ] || [ -e "/run/user/$uid/wayland-1" ]; then
    echo "Wayland socket found for user $user"
  # Method 3: Try to detect through process environment
  elif ps -u "$user" -o cmd | grep -q "WAYLAND_DISPLAY="; then
    echo "Wayland environment detected in processes for user $user"
  else
    echo "No Wayland session found for user $user, skipping..."
    return 1
  fi
  
  echo "Setting wallpaper for $user using swww..."
  
  # Setup proper environment for the user
  local XDG_RUNTIME_DIR="/run/user/$uid"
  
  # Try to set the wallpaper with proper environment
  local max_attempts=3
  local attempt=1
  local success=false
  
  # Command to execute as the user with proper environment
  local cmd="export XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR; "
  
  # Try to detect WAYLAND_DISPLAY if not set
  if [ -e "$XDG_RUNTIME_DIR/wayland-0" ]; then
    cmd+="export WAYLAND_DISPLAY=wayland-0; "
  elif [ -e "$XDG_RUNTIME_DIR/wayland-1" ]; then
    cmd+="export WAYLAND_DISPLAY=wayland-1; "
  fi
  
  # Check if swww-daemon is already running, if not start it
  cmd+="if ! pgrep -x swww-daemon >/dev/null; then "
  cmd+="echo 'Starting swww-daemon...'; "
  cmd+="swww-daemon & "
  cmd+="sleep 3; " # Give more time for the daemon to start
  cmd+="else "
  cmd+="echo 'swww-daemon is already running'; "
  cmd+="fi; "
  
  # Command to set wallpaper
  cmd+="swww img '$WALLPAPER_PATH' --transition-fps 60 --transition-type grow --transition-pos center"
  
  echo "Executing: $cmd"
  
  while [ $attempt -le $max_attempts ] && [ "$success" = "false" ]; do
    echo "Attempt $attempt to set wallpaper for $user..."
    
    # Execute the command as the user
    if sudo -u "$user" bash -c "$cmd" 2>/dev/null; then
      echo "Successfully set wallpaper for $user's session using swww"
      success=true
    else
      echo "Attempt $attempt failed, waiting before retry..."
      sleep 2
      attempt=$((attempt + 1))
    fi
  done
  
  if [ "$success" = "false" ]; then
    echo "Failed to set wallpaper for $user after $max_attempts attempts"
    return 1
  fi
  
  return 0
}

# Loop through users with active sessions
for user in $(who | cut -d' ' -f1 | sort | uniq); do
  set_wallpaper_for_user "$user"
done

exit 0
