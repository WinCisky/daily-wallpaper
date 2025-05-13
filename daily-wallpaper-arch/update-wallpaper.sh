#!/bin/bash
# Helper script to detect Hyprland sessions and call the Python script

# First run the python script to download the wallpaper and set up configurations
/usr/local/bin/daily-wallpaper.py

# Additionally, try to find active Hyprland sessions and reload the wallpaper directly
WALLPAPER_PATH="/usr/share/backgrounds/daily-wallpaper-background.jpg"

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
    for socket in /run/user/$uid/hypr/*/hyprpaper.sock; do
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
