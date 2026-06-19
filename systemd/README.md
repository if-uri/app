# Running ifURI as a service (node/daemon mode)

Keep the local runtime / LAN node (`ifuri-app serve`, port 8765) running across
reboots. Three platforms, one command each. Adjust the `ifuri-app` path to your
install (venv / pipx / system).

## Linux (systemd --user)
```sh
cp systemd/ifuri-runtime-user.service ~/.config/systemd/user/ifuri-runtime.service
systemctl --user daemon-reload
systemctl --user enable --now ifuri-runtime.service
loginctl enable-linger "$USER"      # survive logout
```
Override defaults in `~/.config/ifuri/runtime.env` (see `ifuri-runtime.env.example`).
The existing `ifuri-voice-user.service` runs the voice UI on 8766 — they coexist.

## macOS (launchd)
```sh
sed "s|USERNAME|$USER|g" systemd/com.ifuri.runtime.plist \
  > ~/Library/LaunchAgents/com.ifuri.runtime.plist
launchctl load ~/Library/LaunchAgents/com.ifuri.runtime.plist
```

## Windows (NSSM)
```bat
nssm install ifURI-runtime "C:\path\to\venv\Scripts\ifuri-app.exe" serve --host 0.0.0.0 --port 8765
nssm start ifURI-runtime
```

## Verify
```sh
curl -fsS http://127.0.0.1:8765/health
```
