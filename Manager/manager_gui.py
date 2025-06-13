# Manager/manager_gui.py

import customtkinter as ctk
from tkinter import filedialog
import sys
from pathlib import Path
import json
import sys
import ctypes
from pathlib import Path

# Ensure project root is in sys.path so we can import utils.py
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils import get_config_dir
from utils import get_resource_path

CONFIG_DIR = get_config_dir()

from Manager.config_editor import ConfigEditor
from Manager.schema_model import ColumnMetadata

# Global UI theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

READABLE_RULE_LABELS = {
    "required_fields": "Required fields based on config",
    "unique_fields": "Unique fields based on config",
    "state_reporting_start_check": "State Reporting Start Date must start with 07/01",
    "start_year_match_check": "State Reporting Start Date year must match the starting year in School Year",
    "last_day_check": "Last Day of School must start with 06/30",
    "end_year_match_check": "State Reporting End Date year must match the ending year in School Year",
    "first_day_match_check": "First Day of School year must match the starting year in School Year",
    "last_day_year_match_check": "Last Day of School year must match the ending year in School Year",
    "school_year_format_check": "School Year format must be 'YYYY-YYYY'",
    "date_format_check": "Date fields format must be MM/DD/YYYY",
    "school_year_difference_check": "School Year must span exactly 1 year",
    "school_year_suffix_check": "Date pairs must be 1 year apart",
    "date_order_check": "Start date must come before end date",
    "acceptable_values_check" : "Values must be in the acceptable values list",
    "zip_code_format_check": "Zip Code must be 5 digits or ZIP+4 format",
    "phone_number_format_check": "Phone number must be 10 digits",
    "school_id_check": "School ID must exist in School Data",
}

class ConfigManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Validation Config Manager")
        self.geometry("800x800")

        # 🔧 Set app icon
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"config.editor")
        icon_path = get_resource_path("favicon.ico")
        self.iconbitmap(icon_path)
        
        self.editor = ConfigEditor()
        self.field_rows = []

        self.rule_switches = {}

        self.build_gui()

    def on_dropdown_change(self, selected_filename):
        if selected_filename == "Select a config...":
            return

        # ✅ Track current config
        self.current_config_filename = selected_filename

        # ✅ Sync dropdowns
        if self.config_dropdown and self.config_dropdown.get() != selected_filename:
            self.config_dropdown.set(selected_filename)

        if self.config_dropdown_rules and self.config_dropdown_rules.get() != selected_filename:
            self.config_dropdown_rules.set(selected_filename)

        # ✅ Load the selected config
        self.load_selected_config(selected_filename)

    def build_gui(self):
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.field_tab = self.tabs.add("File Configuration")
        self.rule_tab = self.tabs.add("Validation Rules")
        self.acceptables_tab = self.tabs.add("Acceptable Values")

        self.config_dropdown = None
        self.config_dropdown_rules = None

        self.build_field_tab()
        self.build_rule_tab()         # ✅ must happen before...
        self.build_acceptables_tab()
        self.load_config_file_list() 

    def build_field_tab(self):
        # Replaces: self.open_button = ...
        self.config_dropdown = ctk.CTkComboBox(
            self.field_tab,
            width=300,
            command=self.on_dropdown_change
        )
        self.config_dropdown.pack(pady=5)

        self.fields_frame = ctk.CTkScrollableFrame(self.field_tab, width=750, height=400)
        self.fields_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Column Headers (will be rebuilt in populate_field_tab, but safe here too)
        ctk.CTkLabel(self.fields_frame, text="Field Name", width=200, text_color="white").grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(self.fields_frame, text="Required", width=70, text_color="white").grid(row=0, column=1, padx=5)
        ctk.CTkLabel(self.fields_frame, text="Data Type", width=100, text_color="white").grid(row=0, column=2, padx=5)
        ctk.CTkLabel(self.fields_frame, text="Unique", width=70, text_color="white").grid(row=0, column=3, padx=5)
        ctk.CTkLabel(self.fields_frame, text="Delete", width=50).grid(row=0, column=4)

        self.add_button = ctk.CTkButton(self.field_tab, text="Add New Field", command=self.add_field_row)
        self.add_button.pack(pady=5)

        self.save_button = ctk.CTkButton(self.field_tab, text="Save Config", command=self.save_config)
        self.save_button.pack(pady=10)

        self.fields_frame.grid_columnconfigure(1, weight=1)
        self.fields_frame.grid_columnconfigure(3, weight=1)

        # Finally, populate the dropdown with config files
        self.load_config_file_list()  # <- fills and sets dropdown

    def build_acceptables_tab(self):
        self.acceptable_values = {}
        self.current_group = None
        self.current_key = None

        self.group_dropdown = ctk.CTkOptionMenu(
            self.acceptables_tab, 
            values=[], 
            command=self.on_group_select
        )
        self.group_dropdown.set("File")
        self.group_dropdown.pack(pady=(10, 5))

        self.key_dropdown = ctk.CTkOptionMenu(
            self.acceptables_tab, 
            values=[], 
            command=self.on_key_select
        )
        self.key_dropdown.set("Column")
        self.key_dropdown.pack(pady=(0, 10))

        self.values_box = ctk.CTkTextbox(self.acceptables_tab, height=200, width=400)
        self.values_box.pack(pady=5)

        self.save_acceptables_button = ctk.CTkButton(
            self.acceptables_tab,
            text="Save Changes",
            command=self.save_acceptable_values
        )
        self.save_acceptables_button.pack(pady=10)

        self.load_acceptable_values_json()

    def build_rule_tab(self):
        # Shared dropdown to select config
        self.config_dropdown_rules = ctk.CTkComboBox(
            master=self.rule_tab,
            width=300,
            command=self.on_dropdown_change
        )
        self.config_dropdown_rules.grid(row=0, column=0, columnspan=2, pady=(10, 0), padx=10, sticky="e")

        # Container frame for rule toggles
        self.rule_switch_frame = ctk.CTkFrame(self.rule_tab)
        self.rule_switch_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

        self.rule_switches = {}  # This will hold {key: CTkSwitch}

        # Save button
        self.save_button = ctk.CTkButton(self.rule_tab, text="Save Config", command=self.save_config)
        self.save_button.grid(row=2, column=0, padx=10, pady=5, sticky="w")

    def populate_field_tab(self):
        if not self.editor.schema or not hasattr(self.editor.schema, "column_mapping"):
            print("⚠️ Schema is empty or malformed.")
            return

        # Clear previous rows
        for widget in self.fields_frame.winfo_children():
            widget.destroy()
        self.field_rows.clear()

        # Rebuild headers
        ctk.CTkLabel(self.fields_frame, text="Field Name", width=200, text_color="white").grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(self.fields_frame, text="Required", width=70, text_color="white").grid(row=0, column=1, padx=5)
        ctk.CTkLabel(self.fields_frame, text="Data Type", width=100, text_color="white").grid(row=0, column=2, padx=5)
        ctk.CTkLabel(self.fields_frame, text="Unique", width=70, text_color="white").grid(row=0, column=3, padx=5)
        ctk.CTkLabel(self.fields_frame, text="Delete", width=50).grid(row=0, column=4)

        column_mapping = self.editor.schema.column_mapping
        required_fields = set(self.editor.schema.required_fields)
        unique_fields = set(self.editor.schema.unique_fields)

        for field_name, meta in column_mapping.items():
            field_type = meta.type
            required = meta.required
            is_unique = field_name in unique_fields
            self.add_field_row(field_name, required, field_type, is_unique)

    def add_field_row(self, field_name="", required=False, field_type="text", is_unique=False):
        row = len(self.field_rows) + 1

        name_entry = ctk.CTkEntry(self.fields_frame, width=200)
        name_entry.insert(0, field_name)
        name_entry.grid(row=row, column=0, padx=5, pady=2)

        req_frame, req_checkbox = create_centered_checkbox(self.fields_frame, required)
        req_frame.grid(row=row, column=1, padx=5, pady=2, sticky="nsew")

        type_menu = ctk.CTkOptionMenu(self.fields_frame, values=["text", "int", "float", "bool", "date"])
        type_menu.set(field_type)
        type_menu.grid(row=row, column=2, padx=5)

        # Unique Checkbox
        uniq_frame, uniq_checkbox = create_centered_checkbox(self.fields_frame, is_unique)
        uniq_frame.grid(row=row, column=3, padx=5, pady=2, sticky="nsew")

        # 🗑️ Delete button
        delete_button = ctk.CTkButton(self.fields_frame, text="❌", width=30, command=lambda: self.delete_field_row(row))
        delete_button.grid(row=row, column=4, padx=5)

        # Store all widgets
        self.field_rows.append((name_entry, req_checkbox, type_menu, uniq_checkbox, delete_button))

    def delete_field_row(self, row_index):
        # Destroy the widgets and remove from list
        if 0 <= row_index - 1 < len(self.field_rows):
            widgets = self.field_rows[row_index - 1]
            for widget in widgets:
                widget.destroy()
            self.field_rows[row_index - 1] = None  # Mark as deleted

        # Optionally: compact the list afterward (not required unless you reindex)

    def save_config(self):
        if not hasattr(self, "current_config_filename") or not self.current_config_filename.endswith(".json"):
            print("⚠️ No valid config selected to save.")
            return

        config_path = get_config_dir() / self.current_config_filename

        new_config = {
            "column_mapping": {},
            "required_fields": [],
            "unique_fields": [],
            "rules_enabled": {},
        }

        # 📦 Gather field rows
        for row in self.field_rows:
            if row is None:
                continue

            name_entry, req_checkbox, type_menu, uniq_checkbox, *_ = row
            field_name = name_entry.get().strip()
            if not field_name:
                continue

            field_type = type_menu.get()
            is_required = req_checkbox.get() == 1
            is_unique = uniq_checkbox.get() == 1

            new_config["column_mapping"][field_name] = {
                "required": is_required,
                "type": field_type
            }

            if is_required:
                new_config["required_fields"].append(field_name)
            if is_unique:
                new_config["unique_fields"].append(field_name)

        # 📦 Gather rule switches
        for key, switch in self.rule_switches.items():
            new_config["rules_enabled"][key] = switch.get() == 1

        # 💾 Save to file
        try:
            with open(config_path, "w") as f:
                json.dump(new_config, f, indent=2)
            print(f"✅ Saved config to {config_path}")
        except Exception as e:
            print(f"❌ Failed to save config: {e}")


    def load_acceptable_values_json(self):
        path = get_config_dir() / "acceptable_values.json"
        try:
            with open(path, "r") as f:
                self.acceptable_values = json.load(f)
            self.group_dropdown.configure(values=list(self.acceptable_values.keys()))
        except Exception as e:
            print(f"⚠️ Failed to load acceptable_values.json: {e}")

    def on_group_select(self, group):
        self.current_group = group
        keys = list(self.acceptable_values.get(group, {}).keys())
        self.key_dropdown.configure(values=keys)
        if keys:
            self.key_dropdown.set(keys[0])
            self.on_key_select(keys[0])

    def on_key_select(self, key):
        self.current_key = key
        self.populate_value_list()

    def populate_value_list(self):
        self.values_box.delete("0.0", "end")
        values = self.acceptable_values.get(self.current_group, {}).get(self.current_key, [])
        for val in values:
            self.values_box.insert("end", f"{val}\n")

    def add_value(self):
        val = self.add_entry.get().strip()
        if not val or not self.current_group or not self.current_key:
            return
        current_values = self.acceptable_values[self.current_group][self.current_key]
        if val not in current_values:
            current_values.append(val)
            self.populate_value_list()
            self.add_entry.delete(0, "end")

    def clear_values(self):
        if self.current_group and self.current_key:
            self.acceptable_values[self.current_group][self.current_key] = []
            self.populate_value_list()

    def save_acceptable_values(self):
        path = Path(__file__).resolve().parent.parent / "User Configs" / "acceptable_values.json"
        try:
            if self.current_group and self.current_key:
                edited_text = self.values_box.get("0.0", "end").strip()
                edited_values = [line.strip() for line in edited_text.split("\n") if line.strip()]
                self.acceptable_values[self.current_group][self.current_key] = edited_values

            with open(path, "w") as f:
                json.dump(self.acceptable_values, f, indent=4)
            print("✅ Acceptable values saved.")
        except Exception as e:
            print(f"❌ Failed to save acceptable_values.json: {e}")

    def populate_rule_tab(self):
        if not self.editor.schema:
            return

        rules_enabled = self.editor.schema.rules_enabled

        # 🔁 Clear any old switches
        for widget in self.rule_switch_frame.winfo_children():
            widget.destroy()

        self.rule_switches.clear()

        for i, (key, value) in enumerate(rules_enabled.items()):
            label_text = READABLE_RULE_LABELS.get(key, key.replace("_", " ").title())

            switch = ctk.CTkSwitch(self.rule_switch_frame, text=label_text)
            switch.grid(row=i, column=0, sticky="w", padx=5, pady=5)

            if value:
                switch.select()
            else:
                switch.deselect()

            self.rule_switches[key] = switch

    def load_selected_config(self, filename):
        config_path = get_config_dir() / filename
        try:
            self.editor.load_config(config_path)  # sets self.schema
            self.populate_field_tab()     # ← calls your current method
            self.populate_rule_tab()      # ← we’ll refactor next
        except Exception as e:
            print(f"⚠️ Failed to load config {filename}: {e}")

    def load_config_file_list(self):
        config_dir = get_config_dir()
        exclude = {"acceptable_values.json", "validation_rules.json"}
        json_files = [f.name for f in config_dir.glob("*.json") if f.name not in exclude]

        values = ["Select a config..."] + json_files if json_files else ["No config files found"]
        default_value = values[0]

        # ✅ Only update dropdowns if they've been built
        if self.config_dropdown is not None:
            self.config_dropdown.configure(values=values)
            self.config_dropdown.set(default_value)

        if self.config_dropdown_rules is not None:
            self.config_dropdown_rules.configure(values=values)
            self.config_dropdown_rules.set(default_value)












def create_centered_checkbox(parent, checked=False):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    checkbox = ctk.CTkCheckBox(frame, text="", width=0)
    if checked:
        checkbox.select()
    checkbox.pack(anchor="center", pady=2)
    return frame, checkbox    
    


if __name__ == "__main__":
    app = ConfigManagerApp()
    app.mainloop()
