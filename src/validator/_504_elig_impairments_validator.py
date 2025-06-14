from src.acceptable_values_loader import load_acceptable_values

def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())


ACCEPTABLE_VALUES = load_acceptable_values()
exceptionality_values = ACCEPTABLE_VALUES.get("504_ELIG_IMPAIRMENTS", {}).get("EXCEPTIONALITY", [])
exceptional_student_placement_values = ACCEPTABLE_VALUES.get("504_ELIG_IMPAIRMENTS", {}).get("EXCEPTIONAL_STUDENT_PLACEMENT", [])

def validate_504_elig_impairments(df, config, cross_data=None):
    print("🔍 Running validate_504_elig_impairments()")
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


    # 📌 Rule #2 – Student ID must exist in Students file
    if rules.get("student_id_check", True):
        if "Local Student ID" in df.columns and cross_data:
            students_df = cross_data.get("students")
            if students_df is not None and "Local Student ID" in students_df.columns:
                valid_ids = set(students_df["Local Student ID"])
                mask = (df["Local Student ID"] != "") & (~df["Local Student ID"].isin(valid_ids))
                add_error(mask, "Local Student ID not found in Student file")
            else:
                print("⚠️ Could not validate Student ID: missing students file or column")


    # 📌 Rule #3: Unique fields (optional, if defined in config)
    if rules.get("unique_fields", True):
        for field in config.get("unique_fields", []):
            if field in df.columns:
                dupes = df.duplicated(field, keep=False)
                add_error(dupes, f"{field} must be unique")


    # 📌 Rule #4: Acceptable Values
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("Exceptionality", exceptionality_values, True),
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
