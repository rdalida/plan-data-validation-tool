import customtkinter as ctk
from utils import get_resource_path
from PIL import Image


class StepProgressBar(ctk.CTkFrame):
    def __init__(self, master, steps, current_step=1, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.steps = steps
        self.current_step = current_step
        self.step_circles = []
        self.step_labels = []

        # Load icons by step and state
        self.step_icons = {
            "Folder": {
                "current": ctk.CTkImage(Image.open(get_resource_path("assets/step1_current.png")), size=(20, 20)),
                "complete": ctk.CTkImage(Image.open(get_resource_path("assets/complete.png")), size=(20, 20)),
                "pending": ctk.CTkImage(Image.open(get_resource_path("assets/step1_pending.png")), size=(20, 20)),
            },
            "Files": {
                "current": ctk.CTkImage(Image.open(get_resource_path("assets/step2_current.png")), size=(20, 20)),
                "complete": ctk.CTkImage(Image.open(get_resource_path("assets/complete.png")), size=(20, 20)),
                "pending": ctk.CTkImage(Image.open(get_resource_path("assets/step2_pending.png")), size=(20, 20)),
            },
            "Mappings": {
                "current": ctk.CTkImage(Image.open(get_resource_path("assets/step3_current.png")), size=(20, 20)),
                "complete": ctk.CTkImage(Image.open(get_resource_path("assets/complete.png")), size=(20, 20)),
                "pending": ctk.CTkImage(Image.open(get_resource_path("assets/step3_pending.png")), size=(20, 20)),
            },
            "Validate": {
                "current": ctk.CTkImage(Image.open(get_resource_path("assets/step4_current.png")), size=(20, 20)),
                "complete": ctk.CTkImage(Image.open(get_resource_path("assets/complete.png")), size=(20, 20)),
                "pending": ctk.CTkImage(Image.open(get_resource_path("assets/step4_pending.png")), size=(20, 20)),
            },
            "Summary": {
                "current": ctk.CTkImage(Image.open(get_resource_path("assets/complete.png")), size=(20, 20)),
                "complete": ctk.CTkImage(Image.open(get_resource_path("assets/complete.png")), size=(20, 20)),
                "pending": ctk.CTkImage(Image.open(get_resource_path("assets/step5_pending.png")), size=(20, 20)),
            }
        }

        self.draw()

    def draw(self):
        for i, step in enumerate(self.steps):
            step_number = i + 1
            if step_number < self.current_step:
                state = "complete"
            elif step_number == self.current_step:
                state = "current"
            else:
                state = "pending"

            # Load icon for step and state
            icon = self.step_icons.get(step, {}).get(state)
            if icon is None:
                print(f"⚠️ Missing icon for step '{step}' and state '{state}'")

            # Icon label
            circle = ctk.CTkLabel(
                self,
                image=icon,
                text="",
                width=30,
                height=30,
                fg_color="transparent"
            )
            circle.grid(row=0, column=i * 2, padx=(10 if i > 0 else 0, 0))
            self.step_circles.append(circle)

            # Step name label
            text_color = {
                "complete": "#6bccb3",
                "current": "#52a38f",
                "pending": "#888888"
            }[state]

            label = ctk.CTkLabel(self, text=step, text_color=text_color, font=ctk.CTkFont(size=11))
            label.grid(row=1, column=i * 2, pady=(4, 0))
            self.step_labels.append(label)

            # Connector line (if not last step)
            if i < len(self.steps) - 1:
                line_canvas = ctk.CTkCanvas(
                    self,
                    width=80,
                    height=4,
                    bg="#212121",
                    highlightthickness=0
                )
                line_canvas.grid(row=0, column=i * 2 + 1, pady=(4, 0))

                line_color = "#6bccb3" if self.current_step > step_number else "#b0b0b0"
                line_canvas.create_line(0, 2, 80, 2, fill=line_color, width=1)

    def update_step(self, new_step):
        self.current_step = new_step
        for widget in self.winfo_children():
            widget.destroy()
        self.step_circles.clear()
        self.step_labels.clear()
        self.draw()
