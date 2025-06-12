
def validate_class_roster(df, config, cross_data=None):
    print("🔍 Running validate_class_roster()")
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

    # 📌 Rule 3: Source ID must exist in Class
    if rules.get("source_id_class_check", True):
        if "Source ID" in df.columns and cross_data:
            class_df = cross_data.get("class")
            if class_df is not None and "Source ID" in class_df.columns:
                valid_ids = set(class_df["Source ID"])
                invalid = ~df["Source ID"].isin(valid_ids)
                add_error(invalid, "Source ID missing in Class file")
            else:
                print("⚠️ Missing Class data or Source ID column")

    # 📌 Rule 4: Student ID must exist in Students
    if rules.get("student_id_check", True):
        if "Student ID" in df.columns and cross_data:
            student_df = cross_data.get("students")
            if student_df is not None and "Student ID" in student_df.columns:

                valid_ids = set(student_df["Student ID"])
                invalid = ~df["Student ID"].isin(valid_ids)
                add_error(invalid, "Student ID missing in Students file")
            else:
                print("⚠️ Missing Students data or Student ID column")

    # 📌 Rule 5: Source ID must exist in Class Teacher
    if rules.get("class_roster_source_id_class_teacher_check", True):
        if "Source ID" in df.columns and cross_data:
            teacher_df = cross_data.get("class_teacher")

            if teacher_df is not None and "Source ID" in teacher_df.columns:
                valid_ids = set(teacher_df["Source ID"])
                invalid = ~df["Source ID"].isin(valid_ids)
                add_error(invalid, "Source ID missing in Class Teacher file")
            else:
                print("⚠️ Missing Class Teacher data or Source ID column")

    return df
