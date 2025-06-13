
from src.acceptable_values_loader import load_acceptable_values
from datetime import datetime

ACCEPTABLE_VALUES = load_acceptable_values()
relationship_values = ACCEPTABLE_VALUES.get("STUDENT_CONTACT", {}).get("RELATIONSHIP", [])

def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())

def validate_contacts(df, config, cross_data=None):
    df["Validation_Errors"] = ""

    def add_error(mask, message):
        df.loc[mask, "Validation_Errors"] += message + "; "
        
    rules = config.get("rules_enabled", {})

    # 📌 Rule #1: Required fields (based on config["required_fields"])
    if rules.get("required_fields", True):
        for field in config.get("required_fields", []):
            if field in df.columns:
                missing = df[field].isna() | (df[field] == "")
                add_error(missing, f"{field} is required")
            else:
                print(f"⚠️ Column not found: {field}")


    # 📌 Rule #2: Unique fields (optional, if defined in config)
    if rules.get("unique_fields", True):
        for field in config.get("unique_fields", []):
            if field in df.columns:
                dupes = df.duplicated(field, keep=False)
                add_error(dupes, f"{field} must be unique")        


    # 📌 Rule 3: Student ID must exist in Students file
    if rules.get("student_id_check", True):
        if "Local Student ID" in df.columns and cross_data:
            students_df = cross_data.get("students")
            if students_df is not None and "Local Student ID" in students_df.columns:
                valid_ids = set(students_df["Local Student ID"])
                invalid = ~df["Local Student ID"].isin(valid_ids)
                add_error(invalid, "Student ID missing in Students file")
            else:
                print("⚠️ Missing student data or Student ID column for cross-check")


    # 📌 Rule #4: Phone fields if not null must contain exactly 10 digits
    if rules.get("phone_number_format_check", True):
        phone_fields = ["Home Phone", "Mobile Phone", "Work Phone"]

        for col in phone_fields:
            if col in df.columns:
                non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")

                digits_only = df[col].astype(str).str.replace(r"\D", "", regex=True)
                valid_format = digits_only.str.len() == 10

                invalid_mask = non_empty_mask & ~valid_format

                add_error(invalid_mask, f"{col} must contain exactly 10 digits")


    # 📌 Rule #5: Email if not null must be a valid email address
    if rules.get("email_format_check", True):
        col = "Email"

        if col in df.columns:
            # Only validate non-empty values
            non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")

            # Simple email regex pattern
            email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            email_series = df[col].astype(str).str.strip()

            valid_format = email_series.str.match(email_pattern)

            # Flag invalid formats only for rows with data
            invalid_mask = non_empty_mask & ~valid_format

            add_error(invalid_mask, f"{col} must be a valid email address")


    # 📌 Rule #6: Zip Code must be 5 digits or ZIP+4 format
    if rules.get("zip_code_format_check", True):
        if "Zip Code" in df.columns:
            pattern = r"^\d{5}(-\d{4})?$"
            postal_codes = df["Zip Code"].fillna("").astype(str).str.strip()
            invalid = (postal_codes != "") & ~postal_codes.str.match(pattern)
            add_error(invalid, "Zip Code must be 5 digits or ZIP+4 format")


    # 📌 Rule #7: Acceptable Values
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("Relationship", relationship_values, True)
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







    return df