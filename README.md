## 📦 Releases

See the [Changelog](CHANGELOG.md) for version history.

# SHM Data Validation Tool

A standalone desktop application for validating structured data files (e.g., CSVs) against custom configuration rules. Built for reliability and ease of use, the tool is designed to streamline validation workflows for SHM-related data entry and auditing.

---

## 🖥️ What It Does

- Loads and validates data files like `Students.csv`, `Vaccines.csv`, etc.
- Applies rule-based validation based on project-specific JSON config files
- Provides real-time feedback and error logs in a GUI interface
- Supports dynamic rule sets like required columns, data types, acceptable values, and custom validators

---

## 🚀 How to Use It

Once the app is built as an `.exe`:

1. **Double-click** the executable to launch
2. **Load your CSV/XLSX file** via the file picker
3. The tool will automatically:
   - Load the corresponding config
   - Run validations
   - Display results with visual cues
4. Optionally export a validation log if errors are found

---

# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and adheres to [Semantic Versioning](https://semver.org/).

---

## [v0.0.0] - 2025-05-07

### Added
- Initial release of the SHM Data Validation Tool.
- GUI-based column mapping for multiple datasets using `customtkinter`.
- Fuzzy matching for column name suggestions (via `difflib`).
- Per-file JSON config system for required fields and types.
- Validation modules for:
  - Students
  - Schools
  - Faculty
  - Contacts
  - Class
  - Class Teacher
  - Class Roster
  - Medical Alerts
  - Student Immunization
- Excel highlighting of specific cells with validation errors using `openpyxl`.
- Summary Excel report with total/valid/invalid/error-rate statistics.
- Mapping memory (`shm_validation_mappings.json`) to recall prior mappings.
- Runtime progress tracking printed to terminal.
- Logo icon support (`shm_icon.ico`) and application title.
- Support for PyInstaller `.spec` packaging and standalone `.exe` generation.
- `version.py` file for version control in UI titles.
- Git integration with branch workflows.

### Added
- "Start Over" button for clean application reset.
- Validation progress logs displayed live in the GUI.
- `CHANGELOG.md` to track project history and updates.

### Changed
- Cross-file validations now skip blank values before checking for matches:
  - School ID in Faculty
  - Email in Contacts vs Students
  - Teacher name in Class Teacher vs Faculty

### Removed
- Terminal logging during validation (replaced with live GUI progress updates).
