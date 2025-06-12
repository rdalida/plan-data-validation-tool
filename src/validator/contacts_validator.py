
from src.acceptable_values_loader import load_acceptable_values
from datetime import datetime

ACCEPTABLE_VALUES = load_acceptable_values()
gender_values = ACCEPTABLE_VALUES.get("CONTACTS", {}).get("GENDER", [])
boolean_values = ACCEPTABLE_VALUES.get("CONTACTS", {}).get("BOOLEAN", [])

def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())

def validate_contacts(df, config, cross_data=None):
    df["Validation_Errors"] = ""

    def add_error(mask, message):
        df.loc[mask, "Validation_Errors"] += message + "; "
        
    rules = config.get("rules_enabled", {})

    # 📌 Rule #1 – Required fields (based on config["required_fields"])
    if rules.get("required_fields", True):
        for field in config.get("required_fields", []):
            if field in df.columns:
                missing = df[field].isna() | (df[field] == "")
                add_error(missing, f"{field} is required")
            else:
                print(f"⚠️ Column not found: {field}")

    # 📌 2. Unique fields (optional, if defined in config)
    if rules.get("unique_fields", True):
        for field in config.get("unique_fields", []):
            if field in df.columns:
                dupes = df.duplicated(field, keep=False)
                add_error(dupes, f"{field} must be unique")        

    # 📌 Rule 3: Student ID must exist in Students file
    if rules.get("student_id_check", True):
        if "Student ID" in df.columns and cross_data:
            students_df = cross_data.get("students")
            if students_df is not None and "Student ID" in students_df.columns:
                valid_ids = set(students_df["Student ID"])
                invalid = ~df["Student ID"].isin(valid_ids)
                add_error(invalid, "Student ID missing in Students file")
            else:
                print("⚠️ Missing student data or Student ID column for cross-check")

    # 📌 4. Acceptable Values
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("Gender", gender_values, False),
            ("Parent or Legal Guardian", boolean_values, False),
            ("Pickup Rights", boolean_values, False),
            ("Resides With", boolean_values, False),
            ("Access to Records", boolean_values, False),
            ("Emergency Contact", boolean_values, False),
            ("Legal Custody", boolean_values, False),
            ("Primary Care Provider", boolean_values, False),
            ("Disciplinary Contact", boolean_values, False)
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

    # 📌 Rule 5: Birth Date format
    if rules.get("contacts_bday_format_check", True):
        if "Birth Date" in df.columns:
            def invalid_date(val):
                try:
                    if val == "":
                        return False
                    datetime.strptime(val, "%m/%d/%Y")
                    return False
                except:
                    return True

            bad_dates = df["Birth Date"].apply(invalid_date)
            add_error(bad_dates, "Birth Date must be in MM/DD/YYYY format")

    # 📌 Rule 6: Email Address should not match Students
    if rules.get("contacts_student_email_check", True):
        if "Email Address" in df.columns and cross_data:
            students_df = cross_data.get("students")
            if students_df is not None and "Email Address" in students_df.columns:
                student_emails = set(students_df["Email Address"])
                mask = (df["Email Address"] != "") & (df["Email Address"].isin(student_emails))
                add_error(mask, "Email Address used in student's email")
            else:
                print("⚠️ Missing student email data for contact email check")

    # 📌 Rule 7: Comments length check
    if rules.get("contacts_comments_len_check", True):
        if "Comments" in df.columns:
            too_long = df["Comments"].str.len() > 1000
            add_error(too_long, "Exceeds Char Limit")

    # 📌 Rule 8: Combined Rule: Enforce uniqueness depending on presence of Contact ID
    if rules.get("contacts_combo_id_check", True):
        base_fields = ["Student ID", "Contact Last Name", "Contact First Name"]
        extended_fields = ["Student ID", "Contact ID", "Contact Last Name", "Contact First Name"]

        missing_cols = [col for col in set(extended_fields) if col not in df.columns]
        if missing_cols:
            print(f"⚠️ Missing required columns for uniqueness check: {missing_cols}")
        else:
            # Trim whitespace from Contact ID to ensure accurate null check
            df["Contact ID"] = df["Contact ID"].astype(str).str.strip()

            # Two groups: with and without Contact ID
            has_contact_id = df["Contact ID"] != ""
            no_contact_id = ~has_contact_id

            # Check duplicates separately
            dupes_with_id = df[has_contact_id].duplicated(extended_fields, keep=False)
            dupes_without_id = df[no_contact_id].duplicated(base_fields, keep=False)

            # Combine duplicate flags and apply error messages
            duplicate_flags = dupes_with_id.combine_first(dupes_without_id).fillna(False)

            add_error(duplicate_flags, "Duplicate Contact record")

    # 📌 Rule 9: Rows with same Contact ID must be identical across key fields
    if rules.get("contacts_combo_id_integrity_check", True):
        consistency_fields = [
            "Contact ID", "Contact Last Name", "Contact First Name", "Email Address",
            "Phone Number 1"
        ]

        if "Contact ID" in df.columns and df["Contact ID"].str.strip().any():
            if all(col in df.columns for col in consistency_fields):
                dupes = df[df.duplicated("Contact ID", keep=False)].copy()

                group_cols = [col for col in consistency_fields if col != "Contact ID"]
                for contact_id, group in dupes.groupby("Contact ID"):
                    if len(group[group_cols].drop_duplicates()) > 1:
                        conflict_mask = (df["Contact ID"] == contact_id)
                        add_error(conflict_mask, f"Inconsistent data for Contact ID")
            else:
                print("⚠️ Missing columns for Rule 17 consistency check")

    return df