from datetime import datetime
import pandas as pd
from src.acceptable_values_loader import load_acceptable_values

def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())


ACCEPTABLE_VALUES = load_acceptable_values()
impairment_category_values = ACCEPTABLE_VALUES.get("IEP_DISABILITY", {}).get("IMPAIRMENT_CATEGORY", [])
priority_values = ACCEPTABLE_VALUES.get("IEP_DISABILITY", {}).get("PRIORITY", [])
exceptional_student_placement_values = ACCEPTABLE_VALUES.get("IEP_DISABILITY", {}).get("EXCEPTIONAL_STUDENT_PLACEMENT", [])



def validate_iep_disability(df, config, cross_data=None):
    print("🔍 Running validate_class_teacher()")
    df["Validation_Errors"] = ""

    def add_error(mask, message):
        count = mask.sum()
        if count:
            print(f"📝 {message} → {count} rows")
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


    # 📌 Rule #3: Student ID must exist in Students file
    if rules.get("student_id_check", True):
        if "Local Student ID" in df.columns and cross_data:
            students_df = cross_data.get("students")
            if students_df is not None and "Local Student ID" in students_df.columns:
                valid_ids = set(students_df["Local Student ID"])
                invalid = ~df["Local Student ID"].isin(valid_ids)
                add_error(invalid, "Local Student ID missing in Students file")
            else:
                print("⚠️ Missing student data or Student ID column for cross-check")


    # TODO: Figure out how to handle this for Excel files. Rows in MM/DD/YYYY format fail this rule.
    # 📌 Rule #4: Date fields must be formatted as MM/DD/YYYY
    if rules.get("date_format_check", True):
        date_fields = [
            "Consent Date",
            "Evaluation Date",
            "Eligibility Date",
            "Placement Date"
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


    # 📌 Rule #5: Acceptable Values
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("Impairment Category", impairment_category_values, True),
            ("Priority", priority_values, True),
            ("Exceptional Student Placement Status", exceptional_student_placement_values, True)
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
