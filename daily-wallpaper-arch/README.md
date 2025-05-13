# Daily Wallpaper for Hyprland

A simple package that automatically changes your Hyprland wallpaper every hour.

## Features

- Automatically downloads daily wallpapers from https://wallpapers.opentrust.it
- Configures hyprpaper for all users
- Sets up systemd timer to change wallpaper hourly
- Runs in the background with no user intervention needed

## Installation

### From AUR

```bash
yay -S daily-wallpaper
```

### Manual Installation

1. Clone this repository
2. Navigate to the directory
3. Build and install the package

```bash
git clone https://github.com/your-username/daily-wallpaper.git
cd daily-wallpaper/daily-wallpaper-arch
makepkg -si
```

## How it works

1. The package installs a Python script to `/usr/local/bin/`
2. It creates a systemd service and timer to run hourly
3. It automatically configures hyprpaper for all users
4. It automatically adds hyprpaper to your Hyprland startup if not already present

No further configuration is needed!

## Troubleshooting

- Try saving the hyprland config file without changing anything once you've installed the package to reload the configs with the newly added option to run hyprpaper.

## License

MIT
