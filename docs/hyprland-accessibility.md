# Hyprland Accessibility: TTS, Zoom, and Visual Aids

A guide to building accessibility support on Hyprland using text-to-speech, screen magnification, and visual enhancements — and an honest explanation of where traditional screen readers fall short.

---

## The Short Version on Screen Readers

If you need full GUI screen reader support (Orca, NVDA-equivalent), **Hyprland is not the right compositor**. Orca requires D-Bus interfaces that Hyprland doesn't implement. This is an architectural limitation, not a configuration issue.

What works well on Hyprland:
- TTS reading of clipboard and selected text
- Screen zoom/magnification
- Visual enhancements (high contrast, larger cursors, reduced motion)
- Window and workspace announcements
- Fenrir for terminal/TTY work

If you need full Orca support, GNOME Wayland is the only compositor that provides it reliably.

---

## TTS Architecture

The approach uses a layered TTS setup with automatic fallback:

```
Piper (neural voice) → espeak-ng (fast) → speech-dispatcher (spd-say)
```

**Piper** produces natural, human-like speech. Good for reading longer passages.
**espeak-ng** is near-instant. Good for short announcements ("workspace 3", window titles).
**speech-dispatcher** is the fallback when neither is available.

### Required Packages

```bash
# Arch / AUR
sudo pacman -S espeak-ng speech-dispatcher
paru -S piper-tts   # or yay -S piper-tts

# Download a voice model (en_US-lessac-medium is a good starting point)
mkdir -p ~/.local/share/piper/voices/en_US
cd ~/.local/share/piper/voices/en_US
curl -LO "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
curl -LO "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
```

### The TTS Wrapper Script

The scripts in [`accessibility/`](../accessibility/) provide a unified interface. The core wrapper (`tts-speak.sh`) checks for Piper first, falls back to espeak-ng, then spd-say:

```bash
# Read text from argument
tts-speak.sh "Hello, this is a test"

# Force a specific backend
TTS_BACKEND=espeak tts-speak.sh "Quick announcement"
TTS_BACKEND=piper tts-speak.sh "Longer passage to read"
```

---

## Hyprland Keybindings for Accessibility

These bindings are defined in `~/.config/hypr/conf.d/40-binds.conf`. All use `$mainMod` (Super key) as the modifier.

### TTS Controls

| Keybinding | Action |
|------------|--------|
| `Super + Ctrl + C` | Read clipboard / selected text (Piper) |
| `Super + Ctrl + S` | Speak current window title and app name |
| `Super + Ctrl + W` | Speak current workspace number |
| `Super + Ctrl + X` | Stop all speech immediately |

### Workspace Navigation with Announcements

| Keybinding | Action |
|------------|--------|
| `Super + Shift + Alt + Left` | Previous workspace with TTS announcement |
| `Super + Shift + Alt + Right` | Next workspace with TTS announcement |

### Visual Accessibility Toggles

| Keybinding | Action |
|------------|--------|
| `Super + Shift + H` | High contrast mode (white/magenta borders) |
| `Super + Shift + T` | Large text mode |
| `Super + Shift + A` | Reduce motion (disable animations) |
| `Super + Ctrl + B` | Toggle blur effects |
| `Super + Ctrl + F` | Flash highlight on active window |
| `Super + Ctrl + L` | Move cursor to center of active window |

### Zoom / Magnification

Hyprland has built-in zoom support:

| Keybinding | Action |
|------------|--------|
| `Super + Mouse Scroll Up` | Zoom in |
| `Super + Mouse Scroll Down` | Zoom out |

### Emergency / Reset

| Keybinding | Action |
|------------|--------|
| `Super + Ctrl + Shift + E` | Emergency maximum contrast mode |
| `Super + Ctrl + Shift + R` | Reset to default theme |

### Terminal Screen Reader

| Keybinding | Action |
|------------|--------|
| `Super + Ctrl + O` | Toggle Fenrir (TTY screen reader) |

---

## Implementing the Keybindings

Example bindings from `40-binds.conf`:

```bash
# TTS - read clipboard
bind = $mainMod CTRL, C, exec, ~/.config/hypr/scripts/read-clipboard.sh  # Read clipboard/selection

# TTS - speak window
bind = $mainMod CTRL, S, exec, ~/.config/hypr/scripts/speak-window.sh    # Speak window title

# TTS - stop
bind = $mainMod CTRL, X, exec, ~/.config/hypr/scripts/stop-speech.sh     # Stop speech

# Zoom (built into Hyprland - no script needed)
bindm = $mainMod, mouse:272, movewindow
bind = $mainMod, mouse_down, exec, hyprctl keyword misc:cursor_zoom_factor $(echo "$(hyprctl getoption misc:cursor_zoom_factor | grep float | awk '{print $2}') * 1.1" | bc)
bind = $mainMod, mouse_up, exec, hyprctl keyword misc:cursor_zoom_factor $(echo "$(hyprctl getoption misc:cursor_zoom_factor | grep float | awk '{print $2}') / 1.1" | bc)
```

---

## Fenrir for Terminal Work

Fenrir is a TTY/console screen reader that works independently of Wayland. It reads terminal content using speech-dispatcher.

```bash
# Install
paru -S fenrir  # or yay -S fenrir

# Start manually
fenrir

# Or toggle via the Super + Ctrl + O keybinding
```

Fenrir reads terminal applications, text editors in terminal mode, and virtual console TTYs (Ctrl+Alt+F1-F6). It does **not** read Wayland GUI applications.

---

## Notification Speaking

For notifications to be read aloud as they arrive, a systemd user service can pipe `notify-send` output through speech-dispatcher:

```bash
# The dbus-notify-speak service listens for notifications and speaks them
systemctl --user enable --now dbus-notify-speak.service
```

The `dbus-notify-speak.service` unit and the script it wraps are in the [`accessibility/`](../accessibility/) directory.

---

## Troubleshooting

**TTS not working:**
```bash
# Test each layer
espeak-ng "test"
spd-say "test"
echo "test" | piper -m ~/.local/share/piper/voices/en_US/en_US-lessac-medium.onnx -f - | aplay

# Check speech-dispatcher is running
systemctl --user status speech-dispatcher
```

**Fenrir won't start:**
```bash
which fenrir
systemctl --user status speech-dispatcher
speech-dispatcher -d   # start manually
```

**No audio output:**
```bash
wpctl status                                      # check pipewire
wpctl get-volume @DEFAULT_AUDIO_SINK@             # check volume
aplay /usr/share/sounds/alsa/Front_Center.wav     # test playback
```

---

## Additional Piper Voices

Voice models are stored in `~/.local/share/piper/voices/` (path varies by setup). Download from [rhasspy/piper-voices on Hugging Face](https://huggingface.co/rhasspy/piper-voices).

```bash
# Example: Ryan (male US English)
cd ~/.local/share/piper/voices/en_US
curl -LO "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
curl -LO "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"
```

Set the voice by pointing `TTS_VOICE` at the `.onnx` file, or update the default in your TTS wrapper script.

---

## References

- [Piper TTS](https://github.com/rhasspy/piper) — neural TTS engine
- [Piper voices (Hugging Face)](https://huggingface.co/rhasspy/piper-voices) — downloadable voice models
- [Fenrir](https://github.com/chrys87/fenrir) — TTY screen reader
- [Hyprland misc options](https://wiki.hyprland.org/Configuring/Variables/#misc) — `cursor_zoom_factor` and other misc settings
- [speech-dispatcher](https://freebsoft.org/speechd) — TTS abstraction layer
- See also: [docs/hyprland-modular-config.md](hyprland-modular-config.md) — the config structure these scripts integrate with
