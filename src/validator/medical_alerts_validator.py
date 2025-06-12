import re


def validate_medical_alerts(df, config, cross_data=None):
    print("🔍 Running validate_medical_alerts()")
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
        if "Student ID" in df.columns and cross_data:
            students_df = cross_data.get("students")
            if students_df is not None and "Student ID" in students_df.columns:
                valid_ids = set(students_df["Student ID"])
                mask = (df["Student ID"] != "") & (~df["Student ID"].isin(valid_ids))
                add_error(mask, "Student ID not found in Student file")
            else:
                print("⚠️ Could not validate Student ID: missing students file or column")

    # 📌 3. Unique fields (optional, if defined in config)
    if rules.get("unique_fields", True):
        for field in config.get("unique_fields", []):
            if field in df.columns:
                dupes = df.duplicated(field, keep=False)
                add_error(dupes, f"{field} must be unique")

    # 📌 Rule #4 – Alert ID should not start with 1 or 2
    if rules.get("alert_id_prefix_check", True) and "Alert ID" in df.columns:
        def is_bad_prefix(val):
            val_str = str(val).strip()
            return bool(re.match(r"^0*1\b", val_str) or re.match(r"^0*2\b", val_str))

        mask = df["Alert ID"].apply(is_bad_prefix)
        add_error(mask, "Alert ID cannot start with 1 or 2 (including 001, 0001, etc)")

    # 📌 Rule #5 – Alert Type and Alert Text should not match
    if rules.get("alert_type_text_mismatch", True):
        if "Alert Type" in df.columns and "Alert Text" in df.columns:
            mask = df["Alert Type"].astype(str).str.strip().str.lower() == \
                   df["Alert Text"].astype(str).str.strip().str.lower()
            add_error(mask, "Alert Type and Alert Text must differ")

    return df
