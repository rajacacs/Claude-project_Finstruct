"""FinStruct — standalone entry point."""

import sys
import logging
import tkinter as tk
from pathlib import Path
import os

# Ensure bundled libs are found when running as PyInstaller .exe
if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
    sys.path.insert(0, str(base))

# In windowed .exe sys.stdout is None — use a log file instead
_frozen = getattr(sys, "frozen", False)
if _frozen:
    _log_dir = Path(os.environ.get("APPDATA", Path.home())) / "FinStruct"
    _log_dir.mkdir(parents=True, exist_ok=True)
    _log_handler = logging.FileHandler(_log_dir / "app.log", encoding="utf-8")
else:
    _log_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[_log_handler],
)

def main():
    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    from gui.main_window import MainWindow
    app = MainWindow(root)          # noqa: F841

    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()


if __name__ == "__main__":
    main()
