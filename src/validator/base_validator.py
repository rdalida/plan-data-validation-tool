import re
from datetime import datetime

def validate_data(df, rules):
    df["Validation_Errors"] = ""

    # 📌 Required fields
    for field in rules.get("required_fields", []):
        if field in df.columns:
            df.loc[df[field].isna(), 'Validation_Errors'] += f"{field} is required; "

    # 📌 Unique fields
    for field in rules.get("unique_fields", []):
        if field in df.columns:
            dupes = df.duplicated(field, keep=False)
            df.loc[dupes, 'Validation_Errors'] += f"{field} must be unique; "

    # 📌 Regex / Type rules
    for field, rule in rules.get("field_rules", {}).items():
        if field in df.columns:
            if rule.get("regex"):
                pattern = re.compile(rule["regex"])
                mask = ~df[field].astype(str).str.match(pattern)
                df.loc[mask, 'Validation_Errors'] += rule["error"] + "; "
            if rule.get("type") == "date":
                fmt = rule.get("format", "%Y-%m-%d")
                invalid = ~df[field].astype(str).apply(lambda x: is_valid_date(x, fmt))
                df.loc[invalid, 'Validation_Errors'] += rule["error"] + "; "

    return df

def is_valid_date(value, fmt="%m/%d/%Y"):
    try:
        datetime.strptime(str(value), fmt)
        return True
    except:
        return False
