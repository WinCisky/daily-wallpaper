#!/usr/bin/env python3
import os
import pwd
import requests
import subprocess

# Configuration
endpoint = "https://wallpapers.opentrust.it"
IMAGE_PATH = "/usr/share/backgrounds/daily-wallpaper-background.jpg" # Define image path globally

def get_user_dbus_session_bus_address(username):
    """
    Finds the DBUS_SESSION_BUS_ADDRESS for a given user's GNOME session.
    """
    try:
        # Find a PID for a GNOME session process owned by the user.
        # 'gnome-session' is a common process name. Using -f to match full command line.
        # Also try 'gnome-shell' as it's often the main session process.
        for session_proc_name in ["gnome-session", "gnome-shell"]:
            pgrep_cmd = ["pgrep", "-u", username, "-f", session_proc_name]
            result = subprocess.run(pgrep_cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip().split('\n')[0]
                env_path = f"/proc/{pid}/environ"
                if os.path.exists(env_path):
                    with open(env_path, "r", encoding='utf-8', errors='replace') as f:
                        env_vars = f.read().split('\0') 
                    for var in env_vars:
                        if var.startswith("DBUS_SESSION_BUS_ADDRESS="):
                            return var.split("=", 1)[1]
        
        print(f"No active GNOME session or DBUS_SESSION_BUS_ADDRESS found for user {username}.")
        return None
    except FileNotFoundError:
        print(f"Error: 'pgrep' command not found. Please ensure it is installed.")
        return None
    except Exception as e:
        print(f"Error getting D-Bus session for {username}: {e}")
        return None

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
            users.append(p.pw_name)
    return users

def set_wallpaper_for_user(username, dbus_address, image_path):
    """
    Sets the wallpaper for a specific user.
    """
    try:
        sudo_prefix = ["sudo", "-u", username, f"DBUS_SESSION_BUS_ADDRESS={dbus_address}"]

        # Set for light mode
        gsettings_set_cmd_light = sudo_prefix + [
            "gsettings", "set",
            "org.gnome.desktop.background", "picture-uri",
            f"file://{image_path}"
        ]
        subprocess.run(gsettings_set_cmd_light, check=True)

        # Set for dark mode
        gsettings_set_cmd_dark = sudo_prefix + [
            "gsettings", "set",
            "org.gnome.desktop.background", "picture-uri-dark",
            f"file://{image_path}"
        ]
        subprocess.run(gsettings_set_cmd_dark, check=True)

        print(f"Wallpaper updated successfully for user {username} for both light and dark modes.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing gsettings command for user {username}: {e}")
        if e.stderr:
            print(f"gsettings stderr for {username}: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"Failed to update wallpaper for user {username}: {e}")
        return False

def main():
    try:
        response = requests.get(endpoint)
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

    target_users = get_target_users()
    if not target_users:
        print("No target users found.")
        return

    print(f"Attempting to update wallpaper for users: {', '.join(target_users)}")

    for username in target_users:
        print(f"\nProcessing user: {username}")
        dbus_address = get_user_dbus_session_bus_address(username)

        if dbus_address:
            set_wallpaper_for_user(username, dbus_address, IMAGE_PATH)
        else:
            print(f"Skipping wallpaper update for {username}: Could not find D-Bus session address or user not logged in graphically.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("This script needs to be run as root to change wallpapers for other users.")
        # exit(1) # Optionally exit if not root, though sudo in commands handles permissions
    main()
    