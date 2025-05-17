# Wallpaper

A simple python script that changes the wallpaper daily.

## Debian
```bash
cd daily-wallpaper-deb
dpkg-deb --build daily-wallpaper-deb
```

## Arch
```bash
cd daily-wallpaper-arch
makepkg -si
# remember to add "exec-once = swww init" to "~/.config/hypr/hyprland.conf"
```