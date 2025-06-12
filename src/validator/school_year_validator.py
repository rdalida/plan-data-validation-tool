from datetime import datetime
import pandas as pd

def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())

def extract_school_year_parts(school_year_series):
    """
    Extracts the starting and ending years from a School Year column,
    strictly in the format 'YYYY-YYYY' (e.g., '2023-2024').

    Returns:
        start_years (pd.Series of Int64)
        end_years (pd.Series of Int64)

    Any rows not matching the format will return NaN and should be caught in validations.
    """
    extracted = (
        school_year_series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.extract(r"^(\d{4})\s*-\s*(\d{4})$")  # Must be exactly 4 digits on both sides
    )

    start_years = extracted[0].astype("Int64")
    end_years = extracted[1].astype("Int64")

    return start_years, end_years


def validate_school_year(df, config, cross_data=None):
    print("🔍 Running validate_student_immunization()")
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


    # 📌 Rule #2 Unique fields (optional, if defined in config)
    if rules.get("unique_fields", True):
        for field in config.get("unique_fields", []):
            if field in df.columns:
                dupes = df.duplicated(field, keep=False)
                add_error(dupes, f"{field} must be unique") 


    # 📌 Rule #3: State Reporting Start Date must always have the month and day of 07/01
    if rules.get("state_reporting_start_check", True):
        col = "State Reporting Start Date"
        if col in df.columns:
            # Create a mask to skip null or empty values
            non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")

            # Parse to datetime
            parsed_dates = pd.to_datetime(df[col], errors="coerce")

            # Apply validation only to rows with non-empty values
            invalid_mask = non_empty_mask & ~parsed_dates.dt.strftime("%m-%d").eq("07-01")

        add_error(invalid_mask, f"{col} must start on 07-01")


    # 📌 Rule #4: State Reporting Start Date year must match the starting year in School Year
    if rules.get("start_year_match_check", True):
        date_col = "State Reporting Start Date"
        year_col = "School Year"

        if date_col in df.columns and year_col in df.columns:
            # Only validate non-empty values
            non_empty_mask = df[date_col].notna() & (df[date_col].astype(str).str.strip() != "")

            parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
            date_years = parsed_dates.dt.year

            school_year_starts, _ = extract_school_year_parts(df[year_col])

            # Apply condition only to non-empty rows
            invalid_mask = non_empty_mask & (
                parsed_dates.isna() |
                school_year_starts.isna() |
                (date_years != school_year_starts)
            )

            add_error(invalid_mask, f"{date_col} year must match starting year of {year_col}")


    # 📌 Rule #5: Last Day of School must always have the month and day of 06/30
    if rules.get("last_day_check", True):
        col = "Last Day of School"
        if col in df.columns:
            # Only validate rows that are not empty or blank
            non_empty_mask = df[col].notna() & (df[col].astype(str).str.strip() != "")

            # Parse to datetime
            parsed_dates = pd.to_datetime(df[col], errors="coerce")

            # Apply check only to valid (non-empty) rows
            invalid_mask = non_empty_mask & ~parsed_dates.dt.strftime("%m-%d").eq("06-30")

            add_error(invalid_mask, f"{col} must start on 06-30")


    # 📌 Rule #6: State Reporting End Date year must match the ending year in School Year
    if rules.get("end_year_match_check", True):
        date_col = "State Reporting End Date"
        year_col = "School Year"

        if date_col in df.columns and year_col in df.columns:
            # Only validate non-empty rows
            non_empty_mask = df[date_col].notna() & (df[date_col].astype(str).str.strip() != "")

            parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
            date_years = parsed_dates.dt.year

            # Use helper to get the ENDING year
            _, school_year_ends = extract_school_year_parts(df[year_col])

            # Validate only where value exists
            invalid_mask = non_empty_mask & (
                parsed_dates.isna() |
                school_year_ends.isna() |
                (date_years != school_year_ends)
            )

            add_error(invalid_mask, f"{date_col} year must match ending year of {year_col}")


    # 📌 Rule #7: First Day of School year must match the starting year in School Year
    if rules.get("first_day_match_check", True):
        date_col = "First Day of School"
        year_col = "School Year"

        if date_col in df.columns and year_col in df.columns:
            # Only validate rows with actual values
            non_empty_mask = df[date_col].notna() & (df[date_col].astype(str).str.strip() != "")

            parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
            date_years = parsed_dates.dt.year

            # Use helper to extract the STARTING year
            school_year_starts, _ = extract_school_year_parts(df[year_col])

            # Only apply validation to non-empty rows
            invalid_mask = non_empty_mask & (
                parsed_dates.isna() |
                school_year_starts.isna() |
                (date_years != school_year_starts)
            )

            add_error(invalid_mask, f"{date_col} year must match starting year of {year_col}")


    # 📌 Rule #8: Last Day of School year must match the ending year in School Year
    if rules.get("last_day_year_match_check", True):
        date_col = "Last Day of School"
        year_col = "School Year"

        if date_col in df.columns and year_col in df.columns:
            # Only validate non-empty rows
            non_empty_mask = df[date_col].notna() & (df[date_col].astype(str).str.strip() != "")

            parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
            date_years = parsed_dates.dt.year

            # Use helper to extract the ENDING year
            _, school_year_ends = extract_school_year_parts(df[year_col])

            # Apply validation only to rows with data
            invalid_mask = non_empty_mask & (
                parsed_dates.isna() |
                school_year_ends.isna() |
                (date_years != school_year_ends)
            )

            add_error(invalid_mask, f"{date_col} year must match ending year of {year_col}")


    # 📌 Rule #9: School Year must be in 'YYYY-YYYY' format
    if rules.get("school_year_format_check", True):
        year_col = "School Year"

        if year_col in df.columns:
            # Skip empty values — leave those for the required field rule
            non_empty_mask = df[year_col].notna() & (df[year_col].astype(str).str.strip() != "")

            # Match format 'YYYY-YYYY'
            valid_format_mask = df[year_col].astype(str).str.match(r"^\d{4}\s*-\s*\d{4}$")

            # Flag rows where value exists but is incorrectly formatted
            invalid_mask = non_empty_mask & ~valid_format_mask

            add_error(invalid_mask, f"{year_col} must be in 'YYYY-YYYY' format")


    # TODO: Figure out how to handle this for Excel files. Rows in MM/DD/YYYY format fail this rule.
    # 📌 Rule #10: Date fields must be formatted as MM/DD/YYYY
    if rules.get("date_format_check", True):
        date_fields = [
            "First Day of School",
            "Last Day of School",
            "State Reporting Start Date",
            "State Reporting End Date"
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


    # 📌 Rule #11: School Year must span exactly 1 year (e.g., 2023-2024)
    if rules.get("school_year_difference_check", True):
        year_col = "School Year"

        if year_col in df.columns:
            # Skip empty values — let required field rule handle those
            non_empty_mask = df[year_col].notna() & (df[year_col].astype(str).str.strip() != "")

            start_years, end_years = extract_school_year_parts(df[year_col])
            year_diff = end_years - start_years

            # Only apply check where values exist
            invalid_mask = non_empty_mask & (
                start_years.isna() |
                end_years.isna() |
                (year_diff != 1)
            )

            add_error(invalid_mask, f"{year_col} must span exactly 1 year (e.g., 2023-2024)")


    # 📌 Rule #12: Year suffixes in date pairs must be 1 year apart
    if rules.get("school_year_suffix_check", True):
        date_pairs = [
            ("First Day of School", "Last Day of School", "First/Last Day of School"),
            ("State Reporting Start Date", "State Reporting End Date", "State Reporting Dates")
        ]

        for start_col, end_col, label in date_pairs:
            if start_col in df.columns and end_col in df.columns:
                parsed_start = pd.to_datetime(df[start_col], errors="coerce")
                parsed_end = pd.to_datetime(df[end_col], errors="coerce")

                # Only validate rows with both dates present
                non_empty_mask = (
                    df[start_col].notna() & (df[start_col].astype(str).str.strip() != "") &
                    df[end_col].notna() & (df[end_col].astype(str).str.strip() != "")
                )

                start_suffix = parsed_start.dt.year % 100
                end_suffix = parsed_end.dt.year % 100

                invalid_mask = non_empty_mask & (
                    parsed_start.isna() |
                    parsed_end.isna() |
                    (end_suffix - start_suffix != 1)
                )

                add_error(invalid_mask, f"Last 2 digits of {label} years must be 1 year apart")


    # 📌 Rule #13: Start date must come before end date
    if rules.get("date_order_check", True):
        date_pairs = [
            ("First Day of School", "Last Day of School", "First/Last Day of School"),
            ("State Reporting Start Date", "State Reporting End Date", "State Reporting Dates")
        ]

        for start_col, end_col, label in date_pairs:
            if start_col in df.columns and end_col in df.columns:
                parsed_start = pd.to_datetime(df[start_col], errors="coerce")
                parsed_end = pd.to_datetime(df[end_col], errors="coerce")

                # Only validate rows with both values present
                non_empty_mask = (
                    df[start_col].notna() & (df[start_col].astype(str).str.strip() != "") &
                    df[end_col].notna() & (df[end_col].astype(str).str.strip() != "")
                )

                invalid_mask = non_empty_mask & (
                    parsed_start.isna() |
                    parsed_end.isna() |
                    (parsed_start >= parsed_end)
                )

                add_error(invalid_mask, f"{start_col} must come before {end_col} in {label}")








    return df
