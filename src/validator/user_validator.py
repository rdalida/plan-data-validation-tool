
from src.acceptable_values_loader import load_acceptable_values

ACCEPTABLE_VALUES = load_acceptable_values()
user_type_values = ACCEPTABLE_VALUES.get("USER", {}).get("USER_TYPE", [])
plan_role_values = ACCEPTABLE_VALUES.get("USER", {}).get("PLAN_ROLE", [])
provider_type_values = ACCEPTABLE_VALUES.get("USER", {}).get("PROVIDER_TYPE", [])

def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())

def validate_user(df, config, cross_data=None):
    print("🔍 Running validate_faculty()")
    df["Validation_Errors"] = ""

    def add_error(mask, message):
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

 
    # 📌 Rule #3: Acceptable Values
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("User Type", user_type_values, True),
            ("Plan Role Name", plan_role_values, True),
            ("Provider Type", provider_type_values, False)
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


    # 📌 Rule #4: Email if not null must be a valid email address
    if rules.get("email_format_check", True):
        col = "Email"

        if col in df.columns:
            # Only validate non-empty values
            non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")

            # Simple email regex pattern
            email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            email_series = df[col].astype(str).str.strip()

            valid_format = email_series.str.match(email_pattern)

            # Flag invalid formats only for rows with data
            invalid_mask = non_empty_mask & ~valid_format

            add_error(invalid_mask, f"{col} must be a valid email address")


    # 📌 Rule #5: Combination of Employee ID, Plan Role Name, and Provider Type must be unique
    if rules.get("employee_planrole_provider_unique_check", True):
        cols = ["Employee ID", "Plan Role Name", "Provider Type"]

        if all(col in df.columns for col in cols):
            # Build a mask to include only rows where all values are non-empty
            non_empty_mask = (
                df["Employee ID"].notna() & (df["Employee ID"].astype(str).str.strip() != "") &
                df["Plan Role Name"].notna() & (df["Plan Role Name"].astype(str).str.strip() != "") &
                df["Provider Type"].notna() & (df["Provider Type"].astype(str).str.strip() != "")
            )

            # Build composite key only for non-empty rows
            combo_keys = df[cols].astype(str).apply(lambda row: "|".join(row.str.strip()), axis=1)

            # Mark duplicates only among rows with complete data
            duplicate_mask = non_empty_mask & combo_keys.duplicated(keep=False)

            add_error(duplicate_mask, "Combination of Employee ID, Plan Role Name, and Provider Type must be unique")


    # 📌 Rule #6: School ID if not null must exist in School file (supports comma-separated values)
    if rules.get("multi_school_id_check", True):
        col = "School ID"

        if col in df.columns and cross_data:
            schools_df = cross_data.get("schools")

            if schools_df is not None and "School ID" in schools_df.columns:
                valid_ids = set(schools_df["School ID"].astype(str).str.strip())

                # Only validate non-empty values
                non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")
                values = df[col].astype(str).str.strip()

                def any_invalid_ids(cell):
                    # Split by comma, strip each ID, and check if all are valid
                    ids = [id.strip() for id in cell.split(",")]
                    return any(id not in valid_ids for id in ids)

                # Apply the check only to non-empty rows
                invalid_mask = non_empty_mask & values.apply(any_invalid_ids)

                add_error(invalid_mask, f"{col} contains ID(s) not found in School file")
            else:
                print("⚠️ Could not validate School ID: missing schools file or School ID column")


    # 📌 Rule #7: Phone fields if not null must contain exactly 10 digits
    if rules.get("phone_number_format_check", True):
        phone_fields = ["Phone Number", "Mobile Phone", "Work Phone"]

        for col in phone_fields:
            if col in df.columns:
                non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")

                digits_only = df[col].astype(str).str.replace(r"\D", "", regex=True)
                valid_format = digits_only.str.len() == 10

                invalid_mask = non_empty_mask & ~valid_format

                add_error(invalid_mask, f"{col} must contain exactly 10 digits")


    # 📌 Rule #8: If User Type is "Provider", then Provider Type is required
    if rules.get("provider_type_required_check", True):
        user_col = "User Type"
        required_col = "Provider Type"

        if user_col in df.columns and required_col in df.columns:
            # Normalize and trim values for comparison
            user_type_series = df[user_col].astype(str).str.strip().str.lower()
            provider_type_series = df[required_col].astype(str).str.strip()

            # Condition: User Type == 'provider' AND Provider Type is missing
            invalid_mask = (user_type_series == "provider") & (provider_type_series == "")

            add_error(invalid_mask, f"{required_col} is required when {user_col} is 'Provider'")




    return df
