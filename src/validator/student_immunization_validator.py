from datetime import datetime
from src.acceptable_values_loader import load_acceptable_values

ACCEPTABLE_VALUES = load_acceptable_values()
vaccine_values = ACCEPTABLE_VALUES.get("IMMUNIZATIONS", {}).get("VACCINES", [])

def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())

def validate_student_immunization(df, config, cross_data=None):
    print("🔍 Running validate_student_immunization()")
    df["Validation_Errors"] = ""

    def add_error(mask, message):
        count = mask.sum()
        if count:
            print(f"📝 {message} → {count} rows")
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

    # 📌 Rule #2 Unique fields (optional, if defined in config)
    if rules.get("unique_fields", True):
        for field in config.get("unique_fields", []):
            if field in df.columns:
                dupes = df.duplicated(field, keep=False)
                add_error(dupes, f"{field} must be unique") 

    # 📌 Rule #3 Vaccine must be from acceptable list
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("Vaccine", vaccine_values, True)
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

    # 📌 Rule 4: Dose Date must be valid MM/DD/YYYY
    if rules.get("dose_date_check", True):
        if "Dose Date" in df.columns:
            def invalid_date(val):
                try:
                    if val == "":
                        return False
                    datetime.strptime(val, "%m/%d/%Y")
                    return False
                except:
                    return True

            bad_dates = df["Dose Date"].apply(invalid_date)
            add_error(bad_dates, "Dose Date must be a valid date in MM/DD/YYYY format")

    # 📌 Rule 5: Student ID must match Students file
    if rules.get("student_id_check", True):
        if "Student ID" in df.columns and cross_data:
            student_df = cross_data.get("students")
            if student_df is not None and "Student ID" in student_df.columns:
                valid_ids = set(student_df["Student ID"])
                invalid = ~df["Student ID"].isin(valid_ids)
                add_error(invalid, "Student ID missing in Students file")
            else:
                print("⚠️ Students data missing for cross-reference")

    return df
