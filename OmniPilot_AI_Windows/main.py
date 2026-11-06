from __future__ import annotations
import sys
import tkinter as tk
from tkinter import messagebox
from omnipilot.config import load_config
from omnipilot.ui import OmniPilotApp

def main() -> int:
    try:
        config=load_config()
        root=tk.Tk()
        app=OmniPilotApp(root,config)
        root.mainloop()
        return 0
    except Exception as exc:
        try:
            messagebox.showerror("OmniPilot startup error",str(exc))
        except Exception:
            print(f"OmniPilot startup error: {exc}",file=sys.stderr)
        return 1

if __name__=="__main__":
    raise SystemExit(main())
