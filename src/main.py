import customtkinter as ctk
from splash import SplashScreen

def start_main_app(splash_parent):
    from gui import SHMValidationApp
    app = SHMValidationApp()
    app.after(0, app.deiconify)  # Show immediately when ready
    app.mainloop()

if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()  # dummy root for splash only

    splash = SplashScreen(root, duration=5000)

    
    def after_splash():
        root.destroy()  
        start_main_app(root)  # now load and launch main app

    splash.on_finish = after_splash
    root.mainloop()
