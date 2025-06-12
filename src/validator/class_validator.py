
def validate_class(df, config, cross_data=None):
    print("🔍 Running validate_class()")
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

    # 📌 2. Unique fields (optional, if defined in config)
    if rules.get("unique_fields", True):
        for field in config.get("unique_fields", []):
            if field in df.columns:
                dupes = df.duplicated(field, keep=False)
                add_error(dupes, f"{field} must be unique")

    # 📌 Rule 3: School ID must match from School file
    if rules.get("school_id_check", True):
        if "School ID" in df.columns and cross_data:
            school_df = cross_data.get("schools")
            if school_df is not None and "School ID" in school_df.columns:
                valid_ids = set(school_df["School ID"])
                invalid_ids = ~df["School ID"].isin(valid_ids)
                add_error(invalid_ids, "School ID missing in School file")
            else:
                print("⚠️ School data or School ID column missing")

    # 📌 Rule 4: Combo must be unique
    if rules.get("class_combo_id_check", True):
        combo_fields = [
            "Source ID", "Course ID", "Course Description", "Campus ID",
            "Section", "Period", "Room"
        ]
        if all(col in df.columns for col in combo_fields):
            dupes = df.duplicated(combo_fields, keep=False)
            add_error(dupes, "Duplicate Class record")
        else:
            print("⚠️ Missing one or more fields for combo uniqueness check")

    return df
