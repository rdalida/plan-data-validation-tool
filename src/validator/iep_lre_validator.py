

def validate_iep_lre(df, config, cross_data=None):
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


    # 📌 Rule #2: School ID must exist in School Data
    if rules.get("school_id_check", True):
        if "School ID" in df.columns and cross_data:
            school_df = cross_data.get("schools")
            if school_df is not None and "School ID" in school_df.columns:
                valid_school_ids = school_df["School ID"].fillna("").astype(str).str.strip()
                student_school_ids = df["School ID"].fillna("").astype(str).str.strip()
                missing = ~student_school_ids.isin(valid_school_ids)
                add_error(missing, "School ID missing in School file")



  


    return df
