
def validate_class_teacher(df, config, cross_data=None):
    print("🔍 Running validate_class_teacher()")
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

    # 📌 Rule 3: Source ID must match Class file
    if rules.get("source_id_class_check", True):
        if "Source ID" in df.columns and cross_data:
            class_df = cross_data.get("class")
            if class_df is not None and "Source ID" in class_df.columns:
                valid_sources = set(class_df["Source ID"])
                invalid = ~df["Source ID"].isin(valid_sources)
                add_error(invalid, "Source ID missing in Class file")
            else:
                print("⚠️ Class data missing or Source ID column not found")

    # 📌 Rule 4: Teacher Name must match a Faculty record
    if rules.get("class_teacher_name_faculty_check", True):
        required_cols = ["Teacher First Name", "Teacher Last Name"]
        if all(col in df.columns for col in required_cols) and cross_data:
            faculty_df = cross_data.get("faculty")
            if faculty_df is not None and all(col in faculty_df.columns for col in ["Faculty First Name", "Faculty Last Name"]):
                teacher_names = set(zip(
                    faculty_df["Faculty First Name"].str.strip(),
                    faculty_df["Faculty Last Name"].str.strip()
                ))

                # Only validate rows where both first and last name are not blank
                valid_rows = (df["Teacher First Name"].str.strip() != "") & (df["Teacher Last Name"].str.strip() != "")
                df_names = list(zip(
                    df.loc[valid_rows, "Teacher First Name"].str.strip(),
                    df.loc[valid_rows, "Teacher Last Name"].str.strip()
                ))

                invalid = [i for i, name in zip(df.loc[valid_rows].index, df_names) if name not in teacher_names]
                add_error(df.index.isin(invalid), "Teacher name missing in Faculty data")
            else:
                print("⚠️ Faculty data missing or name columns not found")

    return df
