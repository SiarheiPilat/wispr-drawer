import tkinter as tk
import threading
import math
import time


class RecordingOverlay:
    """Shows a pulsing red dot in the top-right corner while recording."""

    def __init__(self):
        self._root = None
        self._canvas = None
        self._thread = None
        self._running = False
        self._pulse_phase = 0.0

    def show(self):
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-transparentcolor", "black")
        self._root.configure(bg="black")

        size = 60
        screen_w = self._root.winfo_screenwidth()
        self._root.geometry(f"{size}x{size}+{screen_w - size - 20}+20")

        self._canvas = tk.Canvas(self._root, width=size, height=size, bg="black", highlightthickness=0)
        self._canvas.pack()

        self._animate()
        self._root.mainloop()

    def _animate(self):
        if not self._running or not self._root:
            return
        self._canvas.delete("all")
        self._pulse_phase += 0.15
        scale = 0.8 + 0.2 * math.sin(self._pulse_phase)
        r = int(15 * scale)
        cx, cy = 30, 30
        alpha_hex = format(int(200 + 55 * math.sin(self._pulse_phase)), "02x")
        color = f"#ff{alpha_hex[0]}0{alpha_hex[1]}0"
        # Simplified: just pulse between red shades
        brightness = int(200 + 55 * math.sin(self._pulse_phase))
        color = f"#{brightness:02x}0000"
        self._canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color, outline="")
        self._root.after(50, self._animate)

    def hide(self):
        self._running = False
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
        self._root = None
        self._canvas = None


class DrawingOverlay:
    """Fullscreen transparent canvas for freehand drawing."""

    def __init__(self):
        self._root = None
        self._canvas = None
        self._thread = None
        self._running = False
        self._lines = []  # List of line segments: [(x1,y1,x2,y2), ...]
        self._last_x = None
        self._last_y = None
        self._ready = threading.Event()

    def show(self):
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._lines = []
        self._ready.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=3)

    def _run(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.3)
        self._root.configure(bg="white")

        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()
        self._root.geometry(f"{screen_w}x{screen_h}+0+0")

        self._canvas = tk.Canvas(
            self._root,
            width=screen_w,
            height=screen_h,
            bg="white",
            highlightthickness=0,
            cursor="crosshair",
        )
        self._canvas.pack()

        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._canvas.bind("<ButtonPress-1>", self._on_press)

        self._ready.set()
        self._root.mainloop()

    def _on_press(self, event):
        self._last_x = event.x
        self._last_y = event.y

    def _on_drag(self, event):
        if self._last_x is not None:
            self._canvas.create_line(
                self._last_x, self._last_y, event.x, event.y,
                fill="red", width=3, capstyle=tk.ROUND, smooth=True,
            )
            self._lines.append((self._last_x, self._last_y, event.x, event.y))
        self._last_x = event.x
        self._last_y = event.y

    def _on_release(self, event):
        self._last_x = None
        self._last_y = None

    def get_drawing_lines(self) -> list:
        return list(self._lines)

    def hide(self):
        self._running = False
        if self._root:
            try:
                self._root.after(0, self._root.destroy)
            except Exception:
                pass
        self._root = None
        self._canvas = None
