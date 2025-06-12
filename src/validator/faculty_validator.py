
from src.acceptable_values_loader import load_acceptable_values

ACCEPTABLE_VALUES = load_acceptable_values()
gender_values = ACCEPTABLE_VALUES.get("FACULTY", {}).get("GENDER", [])
boolean_values = ACCEPTABLE_VALUES.get("FACULTY", {}).get("BOOLEAN", [])

def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())

def validate_faculty(df, config, cross_data=None):
    print("🔍 Running validate_faculty()")
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

    # 📌 3. School ID must exist in Schools file
    if rules.get("school_id_check", True):
        if "School ID" in df.columns and cross_data:
            schools_df = cross_data.get("schools")
            if schools_df is not None and "School ID" in schools_df.columns:
                valid_ids = set(schools_df["School ID"])
                # Only validate rows where School ID is not blank
                mask = (df["School ID"] != "") & (~df["School ID"].isin(valid_ids))
                add_error(mask, "School ID missing in School file")
            else:
                print("⚠️ Could not validate School ID: missing schools file or School ID column")

    # 📌 4. Acceptable Values
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("Gender", gender_values, True),
            ("Examiner", boolean_values, False),
            ("ActiveUser", boolean_values, False)
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
