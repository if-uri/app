"""PyInstaller entrypoint (absolute imports only)."""

from ifuri_app.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
