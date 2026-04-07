import tkinter as tk
import threading


def show_toast(message: str, duration_ms: int = 2500):
    """Show a brief toast notification in the bottom-right corner."""
    threading.Thread(target=_toast_thread, args=(message, duration_ms), daemon=True).start()


def _toast_thread(message: str, duration_ms: int):
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.9)
    root.configure(bg="#1e1e1e")

    frame = tk.Frame(root, bg="#1e1e1e", padx=16, pady=10)
    frame.pack()

    label = tk.Label(
        frame,
        text=message,
        bg="#1e1e1e",
        fg="#ffffff",
        font=("Segoe UI", 10),
        wraplength=350,
        justify="left",
    )
    label.pack()

    # Position bottom-right
    root.update_idletasks()
    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    x = screen_w - w - 20
    y = screen_h - h - 60
    root.geometry(f"+{x}+{y}")

    root.after(duration_ms, root.destroy)
    root.mainloop()
