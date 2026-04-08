# Desktop Icon Manager (DIM)

Desktop Icon Manager (DIM) is a Python application designed to manage desktop icon positions on Windows. It often happens — after updating graphics card drivers or changing screen resolution — that Windows icons lose their original arrangement and end up grouped randomly. DIM lets you save the current position of all desktop icons and restore them from those saved snapshots.

The program features an intuitive graphical interface (built with `customtkinter`) and a core module, `icon_manager.py`, which directly queries the Windows OS graphics APIs to extract and precisely set the (x, y) position of each icon.

## Features
- **Save Positions**: Captures the exact coordinates of all Desktop icons in real time and stores them in small dynamically generated files.
- **Quick Restore**: If your icon layout gets scrambled, just select a backup and click "Restore".
- **Startup Backup**: Can be configured to run silently on Windows startup (`--silent`), so every time you turn on your PC a backup of your icon grid is saved automatically.
- **Registry Backup**: Exports the Windows registry tree that maps Desktop Bags, for diagnostic purposes or extra safety.

## Prerequisites

To run the application, **Python must be installed** on your computer.
You can download Python from the official website: [python.org](https://www.python.org/downloads/) (make sure to check "Add Python to PATH" during installation on Windows if you haven't already).

## Installation

1. Clone or download this repository to your computer.
2. Open the Command Prompt (or PowerShell) and navigate to the folder containing the files.
3. Install the requirements by running the following command in your terminal:

```bash
pip install -r requirements.txt
```

The only external module required is `customtkinter`. All other libraries used are part of Python's standard library (such as `ctypes`, `json`, etc).

## How to Use

1. Use the `start_dim.bat` file to conveniently launch the graphical interface. Alternatively, you can start the program from the terminal with:
   ```bash
   python dim.py
   ```
2. **To save**: Click **"Backup Positions Now"**. This will create a JSON file in the `/backups/` folder with the position and name of each icon.
3. **To restore**: Select a backup by its date and time, then click **"Restore"** next to it. Icons will snap back to their exact positions instantly (you may need to right-click on an empty area of your desktop and make sure `"Auto arrange icons"` is turned off to allow free icon movement).
4. **Other Options**:
   - Toggle "Run Backup on Windows Startup" to silently launch the program at boot, building a history of your desktop layouts.

---

## Support the Project

If DIM has been useful to you, consider buying me a coffee ☕

[[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/odo1969)
