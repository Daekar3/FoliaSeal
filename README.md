# Scratch

Utility for experimenting.

## Directory Mirror Sync

`dir_sync.py` provides a simple GUI tool to mirror a source directory to a target directory on Windows. It uses the `watchdog` package to detect file system changes and replicates them in real time.

### Usage

1. Install dependencies:
   ```bash
   pip install watchdog
   ```
2. Run the script:
   ```bash
   python dir_sync.py
   ```
3. Use the GUI buttons to choose the source and target folders, then start syncing. A log of actions appears in the status box.
