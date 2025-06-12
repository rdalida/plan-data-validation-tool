
## Project Structure

```
SHM Data Validation Tool/                           # Main project folder
├── assets/                                         # Images, icons, Excel Dashboard      
├── config/                                         # Columns mappings, required fields, unique fields, based on SHM data templates    
│   ├── class.json
│   ├── class_roster.json
│   ├── class_teacher.json
│   ├── contacts.json
│   ├── faculty.json
│   ├── medical_alerts.json
│   ├── schools.json
│   ├── student_immunization.json
│   ├── students.json
│   └── validation_rules.json
├── output/                                         # Validated files are placed here       
├── scripts/                                        # Utility scripts (e.g., helpers, test runners)        
├── src/                            
│   ├── gui/                                        # CustomTkinter GUI modules        
│   ├── validator/                                  # Logic rules     
│   │   ├── base_validator.py
│   │   ├── class_roster_validator.py
│   │   ├── class_teacher_validator.py
│   │   ├── class_validator.py
│   │   ├── contacts_validator.py
│   │   ├── faculty_validator.py
│   │   ├── schools_validator.py
│   │   ├── student_immunization_validator.py
│   │   └── students_validator.py
│   └── main.py                                     # Entry point
│   └── file_handler.py                             # Loads, normalizes, and preprocesses input CSV files   
│   └── rules_constants.py                          # List of Acceptable Values    
├── README.md                                       # Project overview    
├── requirements.txt                                # Python dependencies   
├── SHMValidator.spec                               # PyInstaller build spec

```

### Prerequisites
- Python 3.9+

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Packaging to an EXE
```bash
pyinstaller SHMValidator.spec
```
