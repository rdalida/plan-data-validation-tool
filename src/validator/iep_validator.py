from datetime import datetime
import pandas as pd


def validate_iep(df, config, cross_data=None):
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


    # TODO: Figure out how to handle this for Excel files. Rows in MM/DD/YYYY format fail this rule.
    # 📌 Rule #10: Date fields must be formatted as MM/DD/YYYY
    if rules.get("date_format_check", True):
        date_fields = [
            "Start Date of Plan",
            "End Date of Plan",
            "Next Plan Due Date",
            "Date of Last Evaluation"
        ]

        for col in date_fields:
            if col in df.columns:
                # Skip empty cells (leave them for required field rule)
                non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")

                parsed_dates = pd.to_datetime(df[col], errors="coerce")
                formatted_dates = parsed_dates.dt.strftime("%m/%d/%Y")
                original_series = df[col].astype(str).str.strip()

                valid_format = original_series == formatted_dates

                # Only flag invalid values that are not empty
                invalid_mask = non_empty_mask & (parsed_dates.isna() | ~valid_format)

                add_error(invalid_mask, f"{col} must be formatted as MM/DD/YYYY")


    # 📌 Rule: If not null, End Date of Plan and Next Plan Due Date must be after Start Date of Plan
    if rules.get("plan_date_order_check", True):
        base_col = "Start Date of Plan"
        date_checks = [
            ("End Date of Plan", "End Date must be after Start Date"),
            ("Next Plan Due Date", "Next Plan Due Date must be after Start Date")
        ]

        if base_col in df.columns:
            parsed_start = pd.to_datetime(df[base_col], errors="coerce")

            for col, message in date_checks:
                if col in df.columns:
                    parsed_target = pd.to_datetime(df[col], errors="coerce")

                    # Only validate where both values exist and are non-empty
                    non_empty_mask = (
                        df[base_col].notna() & (df[base_col].astype(str).str.strip() != "") &
                        df[col].notna() & (df[col].astype(str).str.strip() != "")
                    )

                    invalid_mask = non_empty_mask & (
                        parsed_start.isna() |
                        parsed_target.isna() |
                        (parsed_target <= parsed_start)
                    )

                    add_error(invalid_mask, f"{col} must be after {base_col}")



  


    return df
