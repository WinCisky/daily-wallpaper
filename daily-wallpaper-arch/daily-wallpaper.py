#!/usr/bin/env python3
import os
import pwd
import requests
import subprocess
import shutil
from pathlib import Path

# Configuration
endpoint = "https://wallpapers.opentrust.it"
IMAGE_PATH = "/usr/share/backgrounds/daily-wallpaper-background.jpg"  # Define image path globally
HYPRPAPER_CONFIG_TEMPLATE = """preload = {image_path}
wallpaper = ,{image_path}
"""

# Hyprland autostart configuration to ensure hyprpaper runs
HYPR_AUTOSTART_LINE = "exec-once = hyprpaper"

def get_target_users():
    """
    Gets a list of non-system users who might have a graphical session.
    Filters by UID >= 1000 and a common shell.
    """
    users = []
    min_uid = 1000 
    common_shells = ['/bin/bash', '/bin/sh', '/bin/zsh', '/usr/bin/bash', '/usr/bin/sh', '/usr/bin/zsh']
    
    for p in pwd.getpwall():
        if p.pw_uid >= min_uid and p.pw_shell in common_shells and os.path.isdir(p.pw_dir):
            users.append((p.pw_name, p.pw_dir))
    return users

def setup_hyprpaper_for_user(username, home_dir, image_path):
    """
    Sets up hyprpaper config for a specific user.
    """
    try:
        config_dir = os.path.join(home_dir, ".config", "hypr")
        os.makedirs(config_dir, exist_ok=True)
        
        # Create or update hyprpaper.conf
        config_path = os.path.join(config_dir, "hyprpaper.conf")
        config_content = HYPRPAPER_CONFIG_TEMPLATE.format(image_path=image_path)
        
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Set proper ownership
        shutil.chown(config_path, username, username)
        
        # Make sure hyprpaper is in the hyprland.conf startup
        hyprland_conf_path = os.path.join(config_dir, "hyprland.conf")
        if os.path.exists(hyprland_conf_path):
            # Read the current config
            with open(hyprland_conf_path, 'r') as f:
                content = f.read()
            
            # Check if hyprpaper is already in autostart
            if HYPR_AUTOSTART_LINE not in content:
                # Add it to the config
                with open(hyprland_conf_path, 'a') as f:
                    f.write(f"\n# Added by daily-wallpaper\n{HYPR_AUTOSTART_LINE}\n")
                print(f"Added hyprpaper to autostart in {username}'s hyprland.conf")
                # Fix ownership
                shutil.chown(hyprland_conf_path, username, username)
        else:
            # Create the hyprland.conf with just the autostart line
            with open(hyprland_conf_path, 'w') as f:
                f.write(f"# Created by daily-wallpaper\n{HYPR_AUTOSTART_LINE}\n")
            print(f"Created default hyprland.conf for {username}")
            # Fix ownership
            shutil.chown(hyprland_conf_path, username, username)
        
        # Get the user's Hyprland and hyprpaper socket if available
        try:
            # Find HYPRLAND_INSTANCE_SIGNATURE from user environment
            cmd = f"sudo -u {username} bash -c 'echo $HYPRLAND_INSTANCE_SIGNATURE'"
            hypr_instance = subprocess.check_output(cmd, shell=True, text=True).strip()
            
            if hypr_instance:
                # The user has Hyprland running, reload the wallpaper using the user's session
                reload_cmd = f"sudo -u {username} bash -c 'HYPRLAND_INSTANCE_SIGNATURE={hypr_instance} hyprctl hyprpaper preload \"{image_path}\" && HYPRLAND_INSTANCE_SIGNATURE={hypr_instance} hyprctl hyprpaper wallpaper \",{image_path}\"'"
                subprocess.run(reload_cmd, shell=True, check=False)
                print(f"Wallpaper reloaded for {username}'s active Hyprland session")
            else:
                # Start hyprpaper if it's not running
                subprocess.run([
                    "sudo", "-u", username, 
                    "bash", "-c", "if ! pgrep -x hyprpaper > /dev/null; then hyprpaper & fi"
                ], check=False)
                print(f"Started hyprpaper for user {username}")
        except Exception as e:
            print(f"Could not reload wallpaper for user {username}: {e}")
            # Fallback: restart hyprpaper to pick up the new config
            subprocess.run([
                "sudo", "-u", username, 
                "bash", "-c", "if pgrep -x hyprpaper > /dev/null; then killall hyprpaper && hyprpaper & fi || hyprpaper &"
            ], check=False)
        
        print(f"Hyprpaper configuration updated for user {username}")
        return True
    except Exception as e:
        print(f"Failed to update Hyprpaper configuration for user {username}: {e}")
        return False

def main():
    try:
        # First make sure the directory exists
        os.makedirs(os.path.dirname(IMAGE_PATH), exist_ok=True)
        
        # Download the new wallpaper
        response = requests.get(endpoint)
        response.raise_for_status()
        image_url = response.text.strip()

        img_data = requests.get(image_url).content
        with open(IMAGE_PATH, 'wb') as f:
            f.write(img_data)
        print(f"Image downloaded to {IMAGE_PATH}")

    except requests.exceptions.RequestException as e:
        print(f"Network or HTTP error downloading image: {e}")
        return  # Exit if image download fails
    except Exception as e:
        print(f"Failed to download image: {e}")
        return

    target_users = get_target_users()
    if not target_users:
        print("No target users found.")
        return

    print(f"Attempting to update wallpaper for users: {', '.join([user[0] for user in target_users])}")

    for username, home_dir in target_users:
        print(f"\nProcessing user: {username}")
        setup_hyprpaper_for_user(username, home_dir, IMAGE_PATH)

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script needs to be run as root to change wallpapers for all users.")
        exit(1)  # Exit if not root
    
    # Create the background directory if it doesn't exist
    os.makedirs(os.path.dirname(IMAGE_PATH), exist_ok=True)
    
    main()