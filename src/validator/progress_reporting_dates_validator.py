from datetime import datetime
import pandas as pd

from src.acceptable_values_loader import load_acceptable_values

ACCEPTABLE_VALUES = load_acceptable_values()
program_type_values = ACCEPTABLE_VALUES.get("PROGRESS_REPORTING_DATES", {}).get("PROGRAM_TYPE", [])
grading_period_values = ACCEPTABLE_VALUES.get("PROGRESS_REPORTING_DATES", {}).get("GRADING_PERIOD", [])
printout_values = ACCEPTABLE_VALUES.get("PROGRESS_REPORTING_DATES", {}).get("PRINTOUT", [])


def normalize(value: str) -> str:
    return ''.join(value.strip().lower().split())

def validate_progress_reporting_dates(df, config, cross_data=None):
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


    # 📌 Rule #2: School Year must be in 'YYYY-YYYY' format
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


    # 📌 Rule #3: Validate expected row count per School Year for specific Grading Period Types
    if rules.get("grading_period_count_check", True):
        col_year = "School Year"
        col_type = "Grading Period Type"

        if col_year in df.columns and col_type in df.columns:
            expected_counts = {
                "every 9 weeks": 4,
                "every 6 weeks": 6
            }

            # Normalize grading type without modifying the original df
            normalized_grading_type = df[col_type].astype(str).str.strip().str.lower()

            grouped = (
                df.assign(_key=normalized_grading_type)
                .groupby([col_year, "_key"])
                .size()
                .reset_index(name="actual_count")
            )

            grouped["expected_count"] = grouped["_key"].map(expected_counts)

            error_keys = grouped[
                grouped["expected_count"].notna() &
                (grouped["actual_count"] != grouped["expected_count"])
            ][[col_year, "_key"]]

            # Flag rows that match invalid (year, grading_type) pairs
            error_pairs = set((g["_key"], g[col_year]) for _, g in error_keys.iterrows())
            invalid_mask = df.apply(
                lambda row: (str(row[col_type]).strip().lower(), row[col_year]) in error_pairs,
                axis=1
            )

            add_error(invalid_mask, "Incorrect number of rows for Grading Period Type")



    # TODO: Figure out how to handle this for Excel files. Rows in MM/DD/YYYY format fail this rule.
    # 📌 Rule #4: Date fields must be formatted as MM/DD/YYYY
    if rules.get("date_format_check", True):
        date_fields = [
            "Start Date",
            "End Date",
            "Due Date"
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


    # 📌 Rule #5: End Date must be after Start Date
    if rules.get("end_after_start_check", True):
        start_col = "Start Date"
        end_col = "End Date"

        if start_col in df.columns and end_col in df.columns:
            parsed_start = pd.to_datetime(df[start_col], errors="coerce")
            parsed_end = pd.to_datetime(df[end_col], errors="coerce")

            non_empty_mask = (
                df[start_col].notna() & (df[start_col].astype(str).str.strip() != "") &
                df[end_col].notna() & (df[end_col].astype(str).str.strip() != "")
            )

            invalid_mask = non_empty_mask & (
                parsed_start.isna() | parsed_end.isna() | (parsed_end <= parsed_start)
            )

            add_error(invalid_mask, f"{end_col} must be after {start_col}")


    # 📌 Rule #6: Due Date must be on or after End Date
    if rules.get("due_after_end_check", True):
        due_col = "Due Date"
        end_col = "End Date"

        if due_col in df.columns and end_col in df.columns:
            parsed_due = pd.to_datetime(df[due_col], errors="coerce")
            parsed_end = pd.to_datetime(df[end_col], errors="coerce")

            non_empty_mask = (
                df[due_col].notna() & (df[due_col].astype(str).str.strip() != "") &
                df[end_col].notna() & (df[end_col].astype(str).str.strip() != "")
            )

            invalid_mask = non_empty_mask & (
                parsed_due.isna() | parsed_end.isna() | (parsed_due < parsed_end)
            )

            add_error(invalid_mask, f"{due_col} must be on or after {end_col}")


    # 📌 Rule #7: (acceptable values)
    if rules.get("acceptable_values_check", True):
        enum_checks = [
            ("Program Type", program_type_values, True),
            ("Grading Period Type", grading_period_values, True),
            ("Printout Type", printout_values, True)
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
