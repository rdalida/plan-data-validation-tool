import pandas as pd
import re

from src.acceptable_values_loader import load_acceptable_values

ACCEPTABLE_VALUES = load_acceptable_values()
gender_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("GENDER", [])
english_learner_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("ENGLISH_LEARNER", [])
living_arrangement_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("LIVING_ARRANGEMENT", [])
blood_type_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("BLOOD_TYPE", [])
race_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("RACE", [])
ethnicity_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("ETHNICITY", [])
membership_type_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("MEMBERSHIP_TYPE", [])
grade_level_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("GRADE_LEVEL", [])
boolean_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("BOOLEAN", [])

def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())


def validate_students(df, config, cross_data=None):
    print("🔍 Running validate_students()")
    df["Validation_Errors"] = ""

    def add_error(mask, message):
        df.loc[mask, "Validation_Errors"] += message + "; "

    rules = config.get("rules_enabled", {})

    # ----------------------------
    # 📌 Rule #1 – Required fields (based on config["required_fields"])
    if rules.get("required_fields", True):
        for field in config.get("required_fields", []):
            if field in df.columns:
                missing = df[field].isna() | (df[field] == "")
                add_error(missing, f"{field} is required")
            else:
                print(f"⚠️ Column not found: {field}")

    # ----------------------------
    # 📌 Rule #2 (acceptable values)
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("Student Gender", gender_values, True),
            ("English Learner", english_learner_values, False),
            ("Living Arrangement", living_arrangement_values, False),
            ("Student Blood Type", blood_type_values, False),
            ("Student Race", race_values, False),
            ("Student Ethnicity", ethnicity_values, False),
            ("Membership Type", membership_type_values, False),
            ("Grade Level", grade_level_values, True),
            ("Alert Active", boolean_values, False),
            ("Alert Never Expires", boolean_values, False),
        ]

        normalized_valid_values_dict = {
        col: set(normalize(v) for v in valid_values)
        for col, valid_values, _ in enum_checks
        }

        for col, valid_values, required in enum_checks:
            if col in df.columns:
                series = df[col].fillna("").astype(str).str.strip().str.title()

                # Normalize each value in the column
                normalized_series = series.apply(normalize)

                # Lookup normalized valid values
                normalized_valids = normalized_valid_values_dict[col]

                if required:
                    mask = ~normalized_series.isin(normalized_valids)
                else:
                    mask = (normalized_series != "") & ~normalized_series.isin(normalized_valids)
                add_error(mask, f"{col} not valid")

    # 📌 Rule #3 Duplicate Student ID
    if rules.get("duplicate_records_check", True):
        if "Student ID" in df.columns:
            df["Student ID"] = df["Student ID"].astype(str).str.strip()

            # Get all rows where Student ID appears more than once
            dupes = df[df.duplicated("Student ID", keep=False)].copy()

            allowed_diff_cols = {"School ID", "Membership Type", "General Alert"}
            check_cols = [col for col in df.columns if col not in allowed_diff_cols and col != "Validation_Errors"]

            # Group by Student ID and compare rows
            for student_id, group in dupes.groupby("Student ID"):
                if len(group[check_cols].drop_duplicates()) > 1:
                    # These records have conflicting non-allowed fields
                    conflict_mask = (df["Student ID"] == student_id)
                    add_error(conflict_mask, "Duplicate Student ID")

    # 📌 Rule #4 If Alert Never Expires is “No”, Alert Active must be present
    if rules.get("alert_never_expires_check", True):
        if "Alert Never Expires" in df.columns and "Alert Active" in df.columns:
            never_expires = df["Alert Never Expires"].fillna("").str.strip().str.lower()
            alert_active = df["Alert Active"].fillna("").str.strip()

            missing_required = (never_expires == "no") & (alert_active == "")
            add_error(missing_required, "Alert Active is required")

    # 📌 Rule #5 Alert Start Date must be before Alert End Date
    if rules.get("alert_start_date_check", True):
        if "Alert Start Date" in df.columns and "Alert End Date" in df.columns:
            start_dates = pd.to_datetime(df["Alert Start Date"], errors="coerce", format="%m/%d/%Y")
            end_dates = pd.to_datetime(df["Alert End Date"], errors="coerce", format="%m/%d/%Y")

            # Compare only if both dates exist
            invalid_order = (start_dates.notna() & end_dates.notna()) & (start_dates > end_dates)
            add_error(invalid_order, "Alert Start Date must be before Alert End Date")

    # 📌 Rule #6 Student ID must not appear in Faculty ID or Contact ID
    if rules.get("student_id_not_facult_contact_check", True):
        if "Student ID" in df.columns and cross_data:
            student_ids = df["Student ID"].fillna("").astype(str).str.strip()

            for file_key, id_column in [("faculty", "Faculty ID"), ("contacts", "Contact ID")]:
                ref_df = cross_data.get(file_key)
                if ref_df is not None and id_column in ref_df.columns:
                    ref_ids = ref_df[id_column].fillna("").astype(str).str.strip()
                    conflict_mask = student_ids.isin(ref_ids)
                    add_error(conflict_mask, f"Student ID used in {file_key.capitalize()} file as {id_column}")

    # 📌 Rule #7 School ID must exist in School Data
    if rules.get("school_id_check", True):
        if "School ID" in df.columns and cross_data:
            school_df = cross_data.get("school")
            if school_df is not None and "School ID" in school_df.columns:
                valid_school_ids = school_df["School ID"].fillna("").astype(str).str.strip()
                student_school_ids = df["School ID"].fillna("").astype(str).str.strip()
                missing = ~student_school_ids.isin(valid_school_ids)
                add_error(missing, "School ID missing in School file")

    # 📌 Rule #8 Student Email should not match Faculty or Contact emails
    if rules.get("student_email_not_facult_contact_check", True):
        if "Email Address" in df.columns and cross_data:
            student_emails = df["Email Address"].fillna("").astype(str).str.lower().str.strip()

            for file_key in ["faculty", "contacts"]:
                ref_df = cross_data.get(file_key)
                if ref_df is not None and "Email Address" in ref_df.columns:
                    ref_emails = ref_df["Email Address"].fillna("").astype(str).str.lower().str.strip()
                    match = student_emails.isin(ref_emails)
                    add_error(match, f"Email address used in {file_key.capitalize()} file")

    # 📌 Rule #9 Duplicate Medicaid ID (only for non-empty values)
    if rules.get("duplicate_med_id_check", True):
        if "Student Medicaid ID" in df.columns:
            df["Student Medicaid ID"] = df["Student Medicaid ID"].astype(str).str.strip()

            # Filter out blanks
            non_blank = df["Student Medicaid ID"] != ""
            subset = df[non_blank]

            dupes = subset[subset.duplicated("Student Medicaid ID", keep=False)].copy()

            allowed_diff_cols = {"School ID", "Membership Type", "General Alert"}
            check_cols = [col for col in df.columns if col not in allowed_diff_cols and col != "Validation_Errors"]

            for medicaid_id, group in dupes.groupby("Student Medicaid ID"):
                if len(group[check_cols].drop_duplicates()) > 1:
                    conflict_mask = (df["Student Medicaid ID"] == medicaid_id)
                    add_error(conflict_mask, "Duplicate Medicaid ID")

    # 📌 Rule #10 General Alert must not contain HTML markup
    if rules.get("general_alert_no_html_check", True):
        if "General Alert" in df.columns:
            pattern = re.compile(r"<[^>]+>")  # matches any HTML tag like <div>, <br>, etc.
            has_html = df["General Alert"].astype(str).str.contains(pattern)
            add_error(has_html, "General Alert must not contain HTML markup")

    # 📌 Rule #11 Postal Code must be 5 digits or ZIP+4 format
    if rules.get("postal_code_format_check", True):
        if "Postal Code" in df.columns:
            pattern = r"^\d{5}(-\d{4})?$"
            postal_codes = df["Postal Code"].fillna("").astype(str).str.strip()
            invalid = (postal_codes != "") & ~postal_codes.str.match(pattern)
            add_error(invalid, "Postal Code must be 5 digits or ZIP+4 format")

    return df
