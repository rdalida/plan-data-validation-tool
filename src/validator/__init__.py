from .base_validator import validate_data
from .students_validator import validate_students
from .schools_validator import validate_schools
from .user_validator import validate_user
from .student_contacts_validator import validate_contacts
from .iep_validator import validate_iep
from .progress_reporting_dates_validator import validate_progress_reporting_dates
from .iep_disability_validator import validate_iep_disability
from .school_year_validator import validate_school_year
from .iep_lre_validator import validate_iep_lre
from ._504_elig_impairments_validator import validate_504_elig_impairments


def dispatch_validation(role, df, config, cross_data=None):
    role = role.lower()

    if role == "students":  # update 3
        return validate_students(df, config, cross_data)
    elif role == "schools": # update 2
        return validate_schools(df, config, cross_data)
    elif role == "user": # update 5
        return validate_user(df, config, cross_data)
    elif role == "student_contact": # update 4
        return validate_contacts(df, config, cross_data)
    elif role == "iep": # update 6
        return validate_iep(df, config, cross_data)
    elif role == "progress_reporting_dates": # update 7
        return validate_progress_reporting_dates(df, config, cross_data)
    elif role == "iep_disability": # update 9
        return validate_iep_disability(df, config, cross_data)
    elif role == "school_year": # update 1
        return validate_school_year(df, config, cross_data)
    elif role == "iep_lre_minutes": # update 8
        return validate_iep_lre(df, config, cross_data)
    elif role == "504_elig_impairments": # update 10
        return validate_504_elig_impairments(df, config, cross_data)
    else:
        return validate_data(df, config)