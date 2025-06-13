import os
import sys
import ctypes
import json
import customtkinter as ctk
from tkinter import filedialog
from tkinter import StringVar
import pandas as pd
from src.file_handler import load_file, save_file, save_all_heatmaps
from src.config_loader import load_all_configs
import difflib
import tkinter.messagebox as mb
from src.version import APP_VERSION
from PIL import Image
import time
from utils import get_resource_path
from src.step_progress_bar import StepProgressBar
from src.validator import dispatch_validation
# ? import platform
import win32com.client as win32
# ? from pathlib import Path

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

MAPPING_CACHE_PATH = os.path.expanduser("~/.shm_validation_mappings.json")

def load_cached_mappings():
    if os.path.exists(MAPPING_CACHE_PATH):
        with open(MAPPING_CACHE_PATH, "r") as f:
            return json.load(f)
    return {}

def save_cached_mappings(cache):
    with open(MAPPING_CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)

EXPECTED_ROLES = [
    "School_Year", "Schools", "Students", "Faculty", "Class",
    "Class_Teacher", "Class_Roster", "Student_Immunization", "Medical_Alerts"
]

class SHMValidationApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(F"SHM Data Validation Tool v{APP_VERSION}")

        # TODO: Update app name and icon
        # 🔧 Set app icon
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"shm.validation.tool")
        icon_path = get_resource_path("shm_icon2.ico")
        self.iconbitmap(icon_path)

        self.geometry("700x800")
        self.selected_folder = ""
        self.file_options = []
        self.file_vars = {}
        self.file_mappings = {}       # role -> filename
        self.file_column_headers = {} # role -> list of actual column headers
        self.column_mappings = {}     # role -> {expected: selected}
        self.current_mapping_index = 0
        self.mapped_roles = []
        self.configs = load_all_configs()
        self.mapping_cache = load_cached_mappings()

        self.init_ui()

    def init_ui(self):
        # --- Top frame (Frontline Logo) ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", pady=(10, 0))

        logo_path = get_resource_path("assets/Frontline-Logo-2Color.png")
        pil_image = Image.open(logo_path)
        self.logo_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(200, 80))
        self.logo_label = ctk.CTkLabel(self.top_frame, image=self.logo_image, text="")
        self.logo_label.pack(pady=(20, 10), anchor="center")

        # ---Progress bar Persistent header ---
        steps = ["Folder", "Files", "Mappings", "Validate", "Summary"]
        self.progress_bar = StepProgressBar(self, steps=steps, current_step=1)
        self.progress_bar.pack(pady=(0, 10))
        self.current_step = 1

        # --- header container ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        bold_font = ctk.CTkFont(family="Arial", size=14, weight="bold")

        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="📄 Source: ",
            font=bold_font,
            text_color="white",
            anchor="w",
            justify="left"
        )

        self.show_header("Use Search to load csv, xlsx, xls files")

        # --- Dynamic content area ---
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(padx=20, pady=10, fill="both", expand=True)

        #Load initial screen
        self.render_file_selection_page()

        # --- Bottom navigation bar ---
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(side="bottom", fill="x", pady=(0, 0))

        # Nav bar inner frame
        self.icon_row = ctk.CTkFrame(
            self.nav_frame,
            fg_color="transparent"
        )
        self.icon_row.pack(pady=5)

        self.render_navigation_bar()

    def render_navigation_bar(self):
        # Home Icon
        home_icon_path = get_resource_path("assets/home_icon.png")
        home_icon = Image.open(home_icon_path)
        self.home_icon = ctk.CTkImage(light_image=home_icon, dark_image=home_icon, size=(30,30))

        # Folder Icon
        folder_icon_path = get_resource_path("assets/folder_icon.png")
        folder_icon = Image.open(folder_icon_path)
        self.folder_icon = ctk.CTkImage(light_image=folder_icon, dark_image=folder_icon, size=(30,30))

        # Next Icon
        back_icon_path = get_resource_path("assets/back_icon.png")
        back_icon = Image.open(back_icon_path)
        self.back_icon = ctk.CTkImage(light_image=back_icon, dark_image=back_icon, size=(30,30))

        # Next Icon
        next_icon_path = get_resource_path("assets/next_icon.png")
        next_icon = Image.open(next_icon_path)
        self.next_icon = ctk.CTkImage(light_image=next_icon, dark_image=next_icon, size=(30,30))

        # Step 1 Folder selection
        self.home_button = ctk.CTkButton(
            self.icon_row,
            image=self.home_icon,
            text="Home",
            text_color="#6bccb3",
            compound="top",
            command=self.restart_app,
            width=40,
            height=30,
            fg_color="transparent",
            hover_color="#65727d",
        )
        self.home_button.pack(side="left", padx=10, pady=10)

        # Step 1 Folder selection
        self.folder_button = ctk.CTkButton(
            self.icon_row,
            image=self.folder_icon,
            text="Search",
            text_color="#6bccb3",
            compound="top",
            command=self.select_folder,
            width=40,
            height=30,
            fg_color="transparent",
            hover_color="#65727d",
        )
        self.folder_button.pack(side="left", padx=10, pady=10)

        # "Back" button to proceed to column mapping
        self.back_button = ctk.CTkButton(
            self.icon_row,
            image=self.back_icon,
            text="back",
            compound="top",
            text_color="#6bccb3",
            command=self.back_step,
            fg_color="transparent",
            width=40,
            height=30,
            hover_color="#65727d",
        )
        self.back_button.pack(side="left", padx=10, pady=20)

        # "Next" button to proceed to column mapping
        self.next_button = ctk.CTkButton(
            self.icon_row,
            image=self.next_icon,
            text="Next",
            compound="top",
            text_color="#6bccb3",
            command=self.next_step,
            fg_color="transparent",
            width=40,
            height=30,
            hover_color="#65727d",
        )
        self.next_button.pack(side="left", padx=10, pady=20)

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.update_idletasks()

    def render_file_selection_page(self):
        self.clear_content()

        # Frame for dynamic file mapping dropdowns
        self.mapping_frame = ctk.CTkFrame(self.content_frame)
        self.mapping_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.current_step = 1
        self.progress_bar.update_step(self.current_step)

    # Step 2 Called when user clicks on Select folder button 
    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return

        self.selected_folder = folder
        self.file_options = [f for f in os.listdir(folder) if f.endswith(('.csv', '.xls', '.xlsx'))]
        self.current_step = 2
        self.progress_bar.update_step(self.current_step)
        self.render_mapping_dropdowns()
        if hasattr(self, "download_button") and self.download_button.winfo_ismapped():
            self.download_button.pack_forget()

    # Step 3 Called when User clicks on Select folder button Allows user to select file
    def render_mapping_dropdowns(self):
        self.clear_content()
        self.file_vars.clear()

        self.show_header("Select files to validate from the drop-down options")

        # Create frame inside content_frame to hold dropdowns
        mapping_frame = ctk.CTkFrame(self.content_frame)
        mapping_frame.pack(padx=20, pady=10, fill="both", expand=True)

        for role in EXPECTED_ROLES:
            row = ctk.CTkFrame(mapping_frame)
            row.pack(pady=5, anchor="w", fill="x")

            label = ctk.CTkLabel(row, text=role, width=200, anchor="w")
            label.pack(side="left", padx=10)

            var = StringVar(value="")
            dropdown = ctk.CTkOptionMenu(
                row,
                variable=var,
                values=[""] + self.file_options,
                fg_color="#6bccb3",
                button_color="#52a38f",
                text_color="black",
                dropdown_hover_color="#52a38f",
                button_hover_color="#85dec8"
            )
            dropdown.pack(side="left", fill="x", expand=True, padx=10)

            self.file_vars[role] = var

    # Step 4 Called when User clicks on Next button to go to Columns Mapping
    def next_step_to_column_mapping(self):
        # Store file mappings
        self.file_mappings = {role: var.get() for role, var in self.file_vars.items() if var.get()}
        self.mapped_roles = list(self.file_mappings.keys())

        if not self.mapped_roles:
            print("❗ No files mapped. Please select at least one file to continue.")
            return

        # Load headers from each file
        for role, file in self.file_mappings.items():
            df = load_file(os.path.join(self.selected_folder, file))
            self.file_column_headers[role] = list(df.columns)

        self.current_mapping_index = 0
        self.show_column_mapping_page(self.mapped_roles[0])

    # Step 5 Called when user clicks on Next button
    def show_column_mapping_page(self, role):
        self.clear_content()
        filename = os.path.basename(self.file_mappings[role])

        self.show_header(f"Map Columns: for {role} → {filename}")
        
        self.current_step = 3
        self.progress_bar.update_step(self.current_step)

        self.column_mappings[role] = {}
        self.mapping_vars = {}

        # Scrollable container for dropdowns
        scrollable_container = ctk.CTkScrollableFrame(
            self.content_frame,
            width=700,
            height=400)
        scrollable_container.pack(padx=20, pady=10, fill="both", expand=True)

        actual_columns = self.file_column_headers.get(role, [])
        expected_fields = self.configs.get(role.lower(), {}).get("column_mapping", {})
        expected_field_names = list(expected_fields.keys())
        cached_mapping = self.mapping_cache.get(filename, {})

        for col in actual_columns:
            row = ctk.CTkFrame(scrollable_container)
            row.pack(anchor="w", fill="x", pady=5)

            label = ctk.CTkLabel(row, text=col, width=250, anchor="w")
            label.pack(side="left", padx=10)

            suggested = cached_mapping.get(col, "") if cached_mapping else suggest_column_match(col, expected_field_names)

            var = StringVar(value=suggested)
            dropdown = ctk.CTkOptionMenu(
                row,
                variable=var,
                values=[""] + expected_field_names,
                fg_color="#6bccb3",
                button_color="#52a38f",
                text_color="black",
                dropdown_hover_color="#52a38f",
                button_hover_color="#85dec8"
                )
            dropdown.pack(side="left", fill="x", expand=True, padx=10)

            self.mapping_vars[col] = var

    # Step 6 Called when user clicks on Next in Columns Mapping
    def save_and_advance(self, role=None):
        role = self.mapped_roles[self.current_mapping_index]
        selected_mapping = {k: v.get() for k, v in self.mapping_vars.items() if v.get()}

        # Validate required fields are mapped
        selected_expected_fields = {var.get() for var in self.mapping_vars.values()}
        expected_config = self.configs[role.lower()]["column_mapping"]

        missing_required = [
            field for field, props in expected_config.items()
            if props["required"] and field not in selected_expected_fields
        ]

        if missing_required:
            mb.showerror("Missing Required Mappings", f"Please map required fields: {', '.join(missing_required)}")
            return

        # Step 1: Collect selections
        selected_mapping = {
            actual_col: var.get()
            for actual_col, var in self.mapping_vars.items()
            if var.get()
        }

        # Step 2: Check for duplicates in selected expected fields
        used_expected = list(selected_mapping.values())
        duplicates = [val for val in set(used_expected) if used_expected.count(val) > 1]

        if duplicates:
            mb.showerror("Duplicate Mappings",
                        f"The following expected fields were mapped more than once: {', '.join(duplicates)}")
            return

        # Step 3: Save mapping if all checks pass
        self.column_mappings[role] = selected_mapping

        self.current_mapping_index += 1
        
        if self.current_mapping_index < len(self.mapped_roles):
            self.show_column_mapping_page(self.mapped_roles[self.current_mapping_index])
        else:
            self.show_validation_summary()

        filename = os.path.basename(self.file_mappings[role])
        self.mapping_cache[filename] = self.column_mappings[role]
        save_cached_mappings(self.mapping_cache)

    # Step 7 Called when user clicks on Back button in Columns Mapping
    def go_back(self):
        self.current_mapping_index = max(0, self.current_mapping_index - 1)
        self.show_column_mapping_page(self.mapped_roles[self.current_mapping_index])

    # Step 8 called when Columns mapping is done
    def show_validation_summary(self):
        self.clear_content()

        self.show_header("Mappings completed. Proceed to validate data")

        self.current_step = 4
        self.progress_bar.update_step(self.current_step)

        # Add output display box for validation logs
        self.validation_output = ctk.CTkTextbox(
            self.content_frame,
            width=700,
            height=400,
            corner_radius=6
        )
        self.validation_output.pack(pady=(0, 20))

    def append_validation_log(self, message):
        self.validation_output.insert("end", message + "\n")
        self.validation_output.see("end")  # Auto-scroll to latest
        self.update_idletasks()  # Ensures UI updates immediately

    # Step 9 called when user clicks on Run Validation button
    def execute_validation(self):
        validated_dfs = {}
        heatmaps = {}
        cross_data = {}
        start_time = time.time()

        # Clear previous validation output
        self.validation_output.delete("1.0", "end")

        # ✅ Sort roles by dependency priority
        PRIORITY_ORDER = [
            "school_year", "schools", "faculty", "contacts",
            "class", "class_teacher", "class_roster",
            "medical_alerts", "student_immunization"
        ]
        self.mapped_roles.sort(
            key=lambda r: PRIORITY_ORDER.index(r.lower()) if r.lower() in PRIORITY_ORDER else 999
        )

        for role in self.mapped_roles:
            role_key = normalize_role(role)
            file_path = os.path.join(self.selected_folder, self.file_mappings[role])
            df = load_file(file_path)

            # Rename columns from actual to expected using mapping
            col_map = self.column_mappings[role]
            df_renamed = df.rename(columns=col_map)

            config = self.configs.get(role.lower(), {})
            cross_data[role.lower()] = df_renamed.copy()

            # Run validation
            self.append_validation_log(f"🚀 Validating role: {role} → {role_key}")
            self.append_validation_log(f"🛠️ Running validate_{role_key}")
            df_validated = dispatch_validation(role.lower(), df_renamed, config, cross_data)
            validated_dfs[role.lower()] = df_validated

            # Define output folder
            self.output_folder = os.path.join(self.selected_folder, "output")
            os.makedirs(self.output_folder, exist_ok=True)

            output_path = os.path.join(
                self.output_folder, f"{role.lower().replace(' ', '_')}_validated.xlsx"
            )

            # Save file and capture heatmap grid
            heatmap_grid = save_file(df_validated, output_path)
            heatmaps[role.lower()] = heatmap_grid

        # ✅ Save all heatmaps to one Excel file
        heatmap_output_path = os.path.join(self.output_folder, "validation_heatmaps.xlsx")
        save_all_heatmaps(heatmaps, heatmap_output_path)

        # ✅ Generate validation summary report
        summary = {}
        for role_key, df in validated_dfs.items():
            total = len(df)
            invalid = df["Validation_Errors"].astype(str).str.strip().ne("").sum()
            valid = total - invalid
            valid_rate = f"{(1 - (invalid / total)) * 100:.0f}%" if total > 0 else "N/A"

            summary[role_key] = {
                "Total Rows": total,
                "Valid": valid,
                "Invalid": invalid,
                "Valid Rate": valid_rate
            }

        summary_df = pd.DataFrame.from_dict(summary, orient="index")
        elapsed = time.time() - start_time
        duration_str = self.format_duration(elapsed)
        self.show_validation_summary_table(summary_df, duration_str)

    def format_duration(self, seconds):
        if seconds < 60:
            return f"in {seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            return f"in {minutes}m {seconds}s"

    # Step 10 called after all files are validated
    def show_validation_summary_table(self, summary_df, duration_str=""):
        # Clear existing widgets
        self.clear_content()

        # Title
        self.show_header(f"⏱ Validation completed {duration_str}")

        self.current_step = 5
        self.progress_bar.update_step(self.current_step)

        # Create a scrollable frame
        summary_frame = ctk.CTkFrame(self.content_frame, width=700, height=400)
        summary_frame.pack(padx=20, pady=10, fill="both", expand=True)
        summary_frame.grid_columnconfigure(0, weight=1)

        # Header row
        headers = list(summary_df.columns)
        for j in range(len(headers) + 1):  # +1 for the "File" column
            summary_frame.grid_columnconfigure(j, weight=1)
        ctk.CTkLabel(summary_frame, text="File", font=("Arial", 14, "bold"), width=150).grid(row=0, column=0, padx=10, pady=5)
        for j, col in enumerate(headers, start=1):
            ctk.CTkLabel(summary_frame, text=col, font=("Arial", 14, "bold"), width=100).grid(row=0, column=j, padx=10, pady=5)

        # Table rows
        for i, (role, row) in enumerate(summary_df.iterrows(), start=1):
            ctk.CTkLabel(summary_frame, text=role, font=("Arial", 12), width=150).grid(row=i, column=0, padx=10, pady=3)
            for j, value in enumerate(row, start=1):
                ctk.CTkLabel(summary_frame, text=str(value), font=("Arial", 12), width=100).grid(row=i, column=j, padx=10, pady=3)

        # Download Icon
        download_icon_path = get_resource_path("assets/download_icon2.png")
        download_icon = Image.open(download_icon_path)
        self.download_icon = ctk.CTkImage(light_image=download_icon, dark_image=download_icon, size=(30,30))

        # "Download Report" button
        self.download_button = ctk.CTkButton(
            self.icon_row,
            image=self.download_icon,
            text="Download",
            compound="top",
            text_color="#6bccb3",
            command=self.download_report,
            fg_color="transparent",
            width=40,
            height=30,
            hover_color="#65727d",
        )
        self.download_button.pack(side="right", padx=10, pady=20)   
        
    def download_report(self):
        try:
            template_path = get_resource_path("assets/SHM Validation Dashboard.xltx")
            output_folder = os.path.normpath(self.output_folder).replace("/", "\\")
            output_file_path = os.path.normpath(os.path.join(self.output_folder, "SHM Validation Dashboard.xlsx"))

            print(f"📁 Output folder: {output_folder}")
            print(f"📥 Dashboard path: {output_file_path}")

            try:
                excel = win32.gencache.EnsureDispatch("Excel.Application")
            except Exception:
                print("⚠️ EnsureDispatch failed, falling back to Dispatch")
                excel = win32.Dispatch("Excel.Application")

            excel.Visible = True
            excel.DisplayAlerts = False

            # ✅ CASE 1: Dashboard already exists
            if os.path.exists(output_file_path):
                print("📄 Dashboard already exists. Opening existing file.")
                excel.Workbooks.Open(output_file_path)
                return

            # ✅ CASE 2: Create it from the template
            if not os.path.exists(template_path):
                print("🚫 Template not found!")
                return

            print("📂 Opening template to create new dashboard...")
            workbook = excel.Workbooks.Open(template_path)

            try:
                named_range = workbook.Names("FolderPath").RefersToRange
                named_range.Value = output_folder
                print("📝 Set FolderPath via named range")
            except Exception:
                settings_sheet = workbook.Sheets("Settings")
                settings_sheet.Range("B1").Value = output_folder
                print("📝 Set FolderPath in Settings!B1")

            # Save as .xlsx in output folder
            workbook.SaveAs(output_file_path, FileFormat=51)
            workbook.Close(SaveChanges=True)

            print(f"✅ Dashboard saved to {output_file_path}")
            excel.Workbooks.Open(output_file_path)

        except Exception as e:
            print(f"❌ Error during download_report: {e}")

    # Step 11 called when user clicks on Start Over button
    def restart_app(self):
        # Clear widgets
        self.clear_content()

        # Reset internal state
        self.selected_folder = ""
        self.file_options = []
        self.file_vars = {}
        self.file_mappings = {}
        self.file_column_headers = {}
        self.column_mappings = {}
        self.current_mapping_index = 0
        self.mapped_roles = []
        self.show_header("Use Search to load csv, xlsx, xls files")
        if hasattr(self, "download_button") and self.download_button.winfo_ismapped():
            self.download_button.pack_forget()

        # Reset header and return to file selection
        self.render_file_selection_page()
        self.progress_bar.update_step(1)
        self.current_step = 1

    def next_step(self):
        if self.current_step == 1:
            self.render_mapping_dropdowns()
            self.current_step = 2

        elif self.current_step == 2:
            self.next_step_to_column_mapping()
            self.current_step = 3

        elif self.current_step == 3:
            self.save_and_advance()
        elif self.current_step == 4:
            self.execute_validation()

    def back_step(self):
        if self.current_step == 1:
            return

        elif self.current_step == 2:
            self.restart_app()
            self.current_step = 1
            self.progress_bar.update_step(self.current_step)

        elif self.current_step == 3:
            if self.mapped_roles:
                self.go_back()
                self.current_step = 3
                self.progress_bar.update_step(self.current_step)
            else:
                self.render_mapping_dropdowns()
                self.current_step = 2
                self.progress_bar.update_step(self.current_step)

        elif self.current_step == 4:
            if self.mapped_roles:
                role = self.mapped_roles[-1]
                self.current_mapping_index = len(self.mapped_roles) - 1
                self.show_column_mapping_page(role)
                self.current_step = 3
                self.progress_bar.update_step(self.current_step)
            else:
                self.render_mapping_dropdowns()
                self.current_step = 2
                self.progress_bar.update_step(self.current_step)

        elif self.current_step == 5:
            self.render_validation_page()
            self.current_step = 4
            self.progress_bar.update_step(self.current_step)

    def show_header(self, text):
        self.header_label.configure(text=text)
        self.header_frame.pack(fill="x")
        self.header_label.pack(fill="x", padx=50, pady=(15, 0), anchor="w")

    # TODO May need to delete
    # ? def hide_header(self):
        # ?self.header_frame.pack_forget()

def suggest_column_match(expected_field, actual_columns):
    """Return the closest column name from actual_columns using fuzzy matching."""
    matches = difflib.get_close_matches(expected_field, actual_columns, n=1, cutoff=0.6)
    return matches[0] if matches else ""

def normalize_role(role):
    return role.lower().replace(" ", "_")

if __name__ == "__main__":
    app = SHMValidationApp()
    app.mainloop()
