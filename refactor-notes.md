### ✅ Summary of Completed Steps

#### 📁 Repo Setup & Environment

* Cloned the original **SHM validation tool repo** into a new repo for the **Plan data validation tool**
* Initialized the virtual environment and Git setup
  *✅ (`2025-06-12 12:54 PM`)*

#### 🛠️ Configuration Refactoring

* Modified all **JSON files** in `User Configs` based on Plan's implementation data templates
  *✅ (`12:55 PM – 2:05 PM`)*

#### 🔄 Validator Refactor

* Began refactoring validator modules:

  * Started with `school_year_validator.py`
  * Completed refactor of `school_year_validator.py`
  * Updated `__init__.py` to reflect the new role structure and import/dispatch logic
    *✅ (`2:05 PM – 3:13 PM`)*

#### ⚙️ Rule Control Config

* Updated school_year.json config to include `rules_enabled` for each rule
* Updated Readable Rules in manager_gui.py for school_year.json
  *✅ (`3:25 PM`)*

#### 🖥️ GUI Adjustments

* In `manager_gui.py`, updated:

  * `Expected Roles`
  * `Priority Order`
* Ensured names in GUI match those in the JSON config
  *✅ (`4:56 PM`)*

### STEPS
1. Update User Config JSON
2. Update validation logic 
3. Update validator __init__ 
4. Update rules enabled in User Config JSON
5. Update readable rules in Config Manager
6. Update Expected Roles and Priority Order in main Validator App