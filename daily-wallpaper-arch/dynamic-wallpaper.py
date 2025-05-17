#!/usr/bin/env python3
"""
Dynamic Wallpaper for Hyprland
Downloads a wallpaper from a URL and sets it as the background for all Hyprland users.
"""

import os
import sys
import subprocess
import shutil
import time
import pwd
import requests
from pathlib import Path

# --- CONFIGURATION ---
endpoint = "https://wallpapers.opentrust.it"
IMAGE_PATH = "/usr/share/backgrounds/daily-wallpaper-background.jpg" # De
# --- END CONFIGURATION ---

def get_user_wayland_session(username):
    """Detect if a user has a Wayland session and get session information."""
    try:
        uid = pwd.getpwnam(username).pw_uid
        xdg_runtime_dir = f"/run/user/{uid}"
        
        # Method 1: Check if Hyprland is running for this user
        hyprland_cmd = ["sudo", "-u", username, "pgrep", "-x", "Hyprland"]
        if subprocess.run(hyprland_cmd, capture_output=True, text=True).returncode == 0:
            print(f"Hyprland is running for user {username}")
            has_session = True
        # Method 2: Check if there's a wayland socket
        elif os.path.exists(f"{xdg_runtime_dir}/wayland-0") or os.path.exists(f"{xdg_runtime_dir}/wayland-1"):
            print(f"Wayland socket found for user {username}")
            has_session = True
        # Method 3: Try to detect through process environment
        else:
            ps_cmd = ["ps", "-u", username, "-o", "cmd"]
            ps_output = subprocess.run(ps_cmd, capture_output=True, text=True).stdout
            has_session = "WAYLAND_DISPLAY=" in ps_output
            if has_session:
                print(f"Wayland environment detected in processes for user {username}")
            else:
                print(f"No Wayland session found for user {username}, skipping...")
                return None
        
        # Determine WAYLAND_DISPLAY
        wayland_display = None
        if os.path.exists(f"{xdg_runtime_dir}/wayland-0"):
            wayland_display = "wayland-0"
        elif os.path.exists(f"{xdg_runtime_dir}/wayland-1"):
            wayland_display = "wayland-1"
        
        return {
            "username": username,
            "uid": uid,
            "xdg_runtime_dir": xdg_runtime_dir,
            "wayland_display": wayland_display
        }
    
    except Exception as e:
        print(f"Error checking Wayland session for {username}: {e}")
        return None

def set_wallpaper_for_user(user_info):
    """Set wallpaper for a user with a Wayland session."""
    if not user_info:
        return False
    
    username = user_info["username"]
    xdg_runtime_dir = user_info["xdg_runtime_dir"]
    wayland_display = user_info["wayland_display"]
    
    print(f"Setting wallpaper for {username} using swww...")
    
    # Try to set the wallpaper with proper environment
    max_attempts = 3
    attempt = 1
    success = False
    
    while attempt <= max_attempts and not success:
        print(f"Attempt {attempt} to set wallpaper for {username}...")
        
        env = {
            "XDG_RUNTIME_DIR": xdg_runtime_dir,
        }
        
        if wayland_display:
            env["WAYLAND_DISPLAY"] = wayland_display
        
        # Check if swww-daemon is already running
        check_daemon_cmd = ["sudo", "-u", username, "pgrep", "-x", "swww-daemon"]
        daemon_running = subprocess.run(check_daemon_cmd, capture_output=True).returncode == 0
        
        if not daemon_running:
            print(f"Starting swww-daemon for user {username}...")
            # Start the daemon as the user
            start_daemon_cmd = [
                "sudo", "-u", username, 
                "bash", "-c", 
                f"export XDG_RUNTIME_DIR={xdg_runtime_dir}; "
                f"{'export WAYLAND_DISPLAY=' + wayland_display + '; ' if wayland_display else ''}"
                f"nohup swww-daemon > /dev/null 2>&1 &"
            ]
            subprocess.run(start_daemon_cmd)
            time.sleep(3)  # Give time for the daemon to start
        else:
            print(f"swww-daemon is already running for user {username}")
        
        # Set the wallpaper
        set_wallpaper_cmd = [
            "sudo", "-u", username, 
            "bash", "-c", 
            f"export XDG_RUNTIME_DIR={xdg_runtime_dir}; "
            f"{'export WAYLAND_DISPLAY=' + wayland_display + '; ' if wayland_display else ''}"
            f"swww img '{IMAGE_PATH}' --transition-fps 60 --transition-type grow --transition-pos center"
        ]
        
        try:
            result = subprocess.run(set_wallpaper_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Successfully set wallpaper for {username}'s session using swww")
                success = True
            else:
                print(f"Attempt {attempt} failed for {username}: {result.stderr}")
                time.sleep(2)
                attempt += 1
        except Exception as e:
            print(f"Error setting wallpaper for {username}: {e}")
            time.sleep(2)
            attempt += 1
    
    if not success:
        print(f"Failed to set wallpaper for {username} after {max_attempts} attempts")
        return False
    
    return True

def get_active_users():
    """Get a list of active users with sessions."""
    try:
        who_output = subprocess.run(["who"], capture_output=True, text=True).stdout
        users = set()
        for line in who_output.splitlines():
            if line.strip():
                username = line.split()[0]
                users.add(username)
        return list(users)
    except Exception as e:
        print(f"Error getting active users: {e}")
        return []

def main():
    """Main function."""

    try:
        response = requests.get(endpoint, timeout=10)
        response.raise_for_status()
        image_url = response.text.strip()

        img_data = requests.get(image_url).content
        with open(IMAGE_PATH, 'wb') as f:
            f.write(img_data)
        print(f"Image downloaded to {IMAGE_PATH}")

    except requests.exceptions.RequestException as e:
        print(f"Network or HTTP error downloading image: {e}")
        return # Exit if image download fails
    except Exception as e:
        print(f"Failed to download image: {e}")
        return
    
    # Loop through users with active sessions
    active_users = get_active_users()
    if not active_users:
        print("No active user sessions found")
        return
    
    for username in active_users:
        user_info = get_user_wayland_session(username)
        if user_info:
            set_wallpaper_for_user(user_info)

if __name__ == "__main__":
    main()
