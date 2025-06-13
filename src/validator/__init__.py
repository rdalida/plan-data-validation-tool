from .base_validator import validate_data
from .students_validator import validate_students
from .schools_validator import validate_schools
from .user_validator import validate_user
from .student_contacts_validator import validate_contacts
from .iep_validator import validate_iep
from .class_roster_validator import validate_class_roster
from .class_teacher_validator import validate_class_teacher
from .school_year_validator import validate_school_year


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
    elif role == "class_roster":
        return validate_class_roster(df, config, cross_data)
    elif role == "class_teacher":
        return validate_class_teacher(df, config, cross_data)
    elif role == "school_year": # update 1
        return validate_school_year(df, config, cross_data)
    else:
        return validate_data(df, config)