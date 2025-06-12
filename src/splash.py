# splash.py
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
from utils import get_resource_path 


class SplashScreen(tk.Toplevel):
    def __init__(self, parent, gif_filename="matrix_shm_fadein.gif", duration=5000):
        super().__init__(parent)
        self.parent = parent
        self.duration = duration

        self.parent.withdraw()  

        # Load GIF frames
        gif_path = get_resource_path(f"assets/{gif_filename}")
        self.frames = [ImageTk.PhotoImage(img.copy()) for img in ImageSequence.Iterator(Image.open(gif_path))]

        self.label = tk.Label(self, bg="black")
        self.label.pack()

        self.frame_index = 0
        self.after_id = None
        self.update_frame()

        # Center splash screen
        self.overrideredirect(True)
        self.update_idletasks()
        width, height = self.winfo_reqwidth(), self.winfo_reqheight()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Auto-close after duration
        self.after(self.duration, self.close)

        # External callback to launch the main app
        self.on_finish = lambda: None

    def update_frame(self):
        if not self.winfo_exists():
            return  

        current_image = self.frames[self.frame_index]
        self.label.configure(image=current_image)
        self.label.image = current_image

        self.frame_index = (self.frame_index + 1) % len(self.frames)

        # Schedule next update only if the window still exists
        self.after_id = self.after(100, self.update_frame)

    def close(self):
        try:
            if self.after_id:
                self.after_cancel(self.after_id)
        except Exception:
            pass
        self.after(100, self._safe_finish)

    def _safe_finish(self):
        self.destroy()
        self.on_finish()