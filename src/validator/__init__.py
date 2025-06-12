from .base_validator import validate_data
from .students_validator import validate_students
from .schools_validator import validate_schools
from .faculty_validator import validate_faculty
from .contacts_validator import validate_contacts
from .class_validator import validate_class
from .class_roster_validator import validate_class_roster
from .class_teacher_validator import validate_class_teacher
from .student_immunization_validator import validate_student_immunization


def dispatch_validation(role, df, config, cross_data=None):
    role = role.lower()

    if role == "students":
        return validate_students(df, config, cross_data)
    elif role == "schools":
        return validate_schools(df, config, cross_data)
    elif role == "faculty":
        return validate_faculty(df, config, cross_data)
    elif role == "contacts":
        return validate_contacts(df, config, cross_data)
    elif role == "class":
        return validate_class(df, config, cross_data)
    elif role == "class_roster":
        return validate_class_roster(df, config, cross_data)
    elif role == "class_teacher":
        return validate_class_teacher(df, config, cross_data)
    elif role == "student_immunization":
        return validate_student_immunization(df, config, cross_data)
    else:
        return validate_data(df, config)