import pandas as pd
import re

from src.acceptable_values_loader import load_acceptable_values

ACCEPTABLE_VALUES = load_acceptable_values()
gender_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("GENDER", [])
grade_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("GRADE", [])
race_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("RACE", [])
language_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("LANGUAGE", [])
status_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("STATUS", [])
eb_el_status_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("EB_EL_STATUS", [])
ethnicity_values = ACCEPTABLE_VALUES.get("STUDENTS", {}).get("ETHNICITY", [])
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

    
    # 📌 2. Unique fields (optional, if defined in config)
    if rules.get("unique_fields", True):
        for field in config.get("unique_fields", []):
            if field in df.columns:
                dupes = df.duplicated(field, keep=False)
                add_error(dupes, f"{field} must be unique")


    # TODO: Figure out how to handle this for Excel files. Rows in MM/DD/YYYY format fail this rule.
    # 📌 Rule #3: Date fields must be formatted as MM/DD/YYYY
    if rules.get("date_format_check", True):
        date_fields = [
            "Birthdate",
        ]

        for col in date_fields:
            if col in df.columns:
                # Skip empty cells (leave them for required field rule)
                non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")

                parsed_dates = pd.to_datetime(df[col], errors="coerce")
                formatted_dates = parsed_dates.dt.strftime("%m/%d/%Y")
                original_series = df[col].astype(str).str.strip()

                valid_format = original_series == formatted_dates

                # Only flag invalid values that are not empty
                invalid_mask = non_empty_mask & (parsed_dates.isna() | ~valid_format)

                add_error(invalid_mask, f"{col} must be formatted as MM/DD/YYYY")


    # 📌 Rule #4 (acceptable values)
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("Sex", gender_values, True),
            ("Grade", grade_values, True),
            ("Race", race_values, False),
            ("Student Language", language_values, False),
            ("Home Language", language_values, False),
            ("Status", status_values, False),
            ("EB/EL Status", eb_el_status_values, False),
            ("Ethnicity", ethnicity_values, False),
            ("At Risk Indicator", boolean_values, False),
            ("Dyslexia Status", boolean_values, False),
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


    # 📌 Rule #5 School ID must exist in School Data
    if rules.get("school_id_check", True):
        if "School ID" in df.columns and cross_data:
            school_df = cross_data.get("schools")
            if school_df is not None and "School ID" in school_df.columns:
                valid_school_ids = school_df["School ID"].fillna("").astype(str).str.strip()
                student_school_ids = df["School ID"].fillna("").astype(str).str.strip()
                missing = ~student_school_ids.isin(valid_school_ids)
                add_error(missing, "School ID missing in School file")
    

    # 📌 Rule #6 Zip Code must be 5 digits or ZIP+4 format
    if rules.get("zip_code_format_check", True):
        if "Zip Code" in df.columns:
            pattern = r"^\d{5}(-\d{4})?$"
            postal_codes = df["Zip Code"].fillna("").astype(str).str.strip()
            invalid = (postal_codes != "") & ~postal_codes.str.match(pattern)
            add_error(invalid, "Zip Code must be 5 digits or ZIP+4 format")


    

    return df
