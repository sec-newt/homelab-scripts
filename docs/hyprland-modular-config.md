# Hyprland Modular Configuration Guide

A practical guide to splitting a monolithic `hyprland.conf` into focused, maintainable modules.

---

## Overview

Instead of a single large config file, the Hyprland configuration is split into focused modules using numbered prefixes. Each file handles one concern: variables, colors, keybindings, etc.

The main `hyprland.conf` becomes a minimal bootstrap that sources the modules in order:

```bash
~/.config/hypr/
├── hyprland.conf          # Minimal bootstrap (~36 lines)
├── conf.d/
│   ├── 00-vars.conf       # Variables & environment
│   ├── 10-colors.conf     # Color scheme & window borders
│   ├── 20-autostart.conf  # Startup applications (exec-once)
│   ├── 30-input.conf      # Keyboard, mouse, touchpad
│   ├── 40-binds.conf      # All keybindings
│   ├── 50-rules.conf      # Window rules
│   └── 60-appearance.conf # Layout, decorations, animations
├── hyprlock.conf
├── hypridle.conf
└── hyprpaper.conf
```

---

## How It Works

`hyprland.conf` contains only the monitor definition, xwayland settings, and a series of `source` statements:

```bash
source = ~/.config/hypr/conf.d/00-vars.conf
source = ~/.config/hypr/conf.d/10-colors.conf
source = ~/.config/hypr/conf.d/20-autostart.conf
source = ~/.config/hypr/conf.d/30-input.conf
source = ~/.config/hypr/conf.d/40-binds.conf
source = ~/.config/hypr/conf.d/50-rules.conf
source = ~/.config/hypr/conf.d/60-appearance.conf
```

The numeric prefixes enforce load order. Variables defined in `00-vars.conf` are available to every subsequent file.

---

## Module Descriptions

### `00-vars.conf` — Variables & Environment
All `$variable` definitions and `env =` declarations. This loads first because every other module references these variables.

```bash
$mainMod = SUPER
$terminal = alacritty
$browser = zen-browser
env = XCURSOR_THEME,Bibata-Modern-Classic
env = XCURSOR_SIZE,36
```

### `10-colors.conf` — Color Scheme
Border colors and theme variables referenced in `60-appearance.conf`.

```bash
$active_border = rgba(b4befeff) rgba(7287fdff) 45deg
$inactive_border = rgba(181926ff)
```

### `20-autostart.conf` — Startup Applications
All `exec-once` lines. Easy to add/remove startup items without touching anything else.

```bash
exec-once = hyprpanel
exec-once = swww-daemon
exec-once = waypaper --restore
exec-once = hypridle
```

### `30-input.conf` — Input Devices
The `input {}`, `gestures {}`, and `binds {}` blocks.

### `40-binds.conf` — Keybindings
All `bind` statements. The largest module. Organized into sections:
- Application launchers
- Window management
- Workspace switching
- Volume and media controls
- Screenshots
- Accessibility keybindings

Adding a keybind comment convention makes bindings self-documenting:
```bash
bind = $mainMod, Return, exec, $terminal     # Terminal
bind = $mainMod, B, exec, $browser           # Browser
bind = $mainMod SHIFT, S, exec, grimblast copy area  # Screenshot to clipboard
```

### `50-rules.conf` — Window Rules
`windowrulev2` rules for floating windows, workspace assignments, and idle inhibition.

### `60-appearance.conf` — Layout & Decorations
The `general {}`, `decoration {}`, `animations {}`, `dwindle {}`, `master {}`, and `misc {}` blocks.

---

## Why Modular?

**Faster editing:** Open `40-binds.conf` to change a keybind — no scrolling through 330 lines to find it.

**Cleaner git history:** A commit that changes `60-appearance.conf` clearly modified appearance settings, not keybindings.

**Easier debugging:** Config errors point to a specific module and line number.

**Selective sharing:** Share just your keybinding or color configuration without exposing the whole file.

---

## Converting an Existing Config

1. Back up your current config:
   ```bash
   cp ~/.config/hypr/hyprland.conf ~/.config/hypr/hyprland.conf.backup
   ```

2. Create the `conf.d/` directory:
   ```bash
   mkdir -p ~/.config/hypr/conf.d
   ```

3. Move sections of `hyprland.conf` into the appropriate module files.

4. Replace the moved content in `hyprland.conf` with `source` statements.

5. Reload to verify:
   ```bash
   hyprctl reload
   ```
   Check for errors with `hyprctl configerrors`.

---

## Important Notes

- **Do not rename the files** — numeric prefixes enforce load order. If you rename `00-vars.conf`, variables won't be defined when other modules try to use them.
- **Hyprland auto-reloads on save** when you write to a config file — you rarely need to run `hyprctl reload` manually.
- **Debugging:** `hyprctl configerrors` shows active configuration errors. `hyprctl reload` forces a reload and prints any parse errors to stdout.

---

## References

- [Hyprland Configuration Wiki](https://wiki.hyprland.org/Configuring/Configuring-Hyprland/)
- [Hyprland Keywords Reference](https://wiki.hyprland.org/Configuring/Keywords/)
- See also: [docs/hyprland-accessibility.md](hyprland-accessibility.md) — accessibility features built on top of this config structure
