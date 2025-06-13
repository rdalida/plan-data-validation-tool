from src.acceptable_values_loader import load_acceptable_values

ACCEPTABLE_VALUES = load_acceptable_values()
school_type_values = ACCEPTABLE_VALUES.get("SCHOOLS", {}).get("SCHOOL_TYPE", [])

def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())

def validate_schools(df, config, cross_data=None):
    print("🔍 Running validate_schools()")
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


    # 📌 Rule #2. Unique fields (optional, if defined in config)
    if rules.get("unique_fields", True):
        for field in config.get("unique_fields", []):
            if field in df.columns:
                dupes = df.duplicated(field, keep=False)
                add_error(dupes, f"{field} must be unique")


    # 📌 Rule #3. Acceptable Values
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("Schools", school_type_values, False),
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


    # 📌 Rule #4: Zip Code must be 5 digits or ZIP+4 format
    if rules.get("zip_code_format_check", True):
        col = "Zip Code"

        if col in df.columns:
            # Only validate non-empty values
            non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")

            postal_codes = df[col].astype(str).str.strip()
            pattern = r"^\d{5}(-\d{4})?$"

            # Flag if format does not match the pattern
            invalid_mask = non_empty_mask & ~postal_codes.str.match(pattern)

            add_error(invalid_mask, f"{col} must be 5 digits or ZIP+4 format")


    # 📌 Rule #5 Phone Number if not null must contain exactly 10 digits
    if rules.get("phone_number_format_check", True):
        col = "Phone Number"

        if col in df.columns:
            # Only validate non-empty values
            non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")

            # Normalize and extract only digits
            digits_only = df[col].astype(str).str.replace(r"\D", "", regex=True)

            # Check for exactly 10 digits
            valid_format = digits_only.str.len() == 10

            # Flag invalid formats only for rows with data
            invalid_mask = non_empty_mask & ~valid_format

            add_error(invalid_mask, f"{col} must contain exactly 10 digits")



    return df
