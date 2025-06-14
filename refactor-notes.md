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
1. Install Git
    https://git-scm.com/downloads
    Confirm installation
      git --version (may need to restart vscode)
2. Create Github Account
    Create SSH Key 
      ssh-keygen -t ed25519 -C "your.email@example.com" (press ENTER twice)
    Copy public key
      cat ~/.ssh/id_ed25519.pub
    In Github, go to Settings >>> SSH and GPG Keys and add new SSH key
    In terminal, test connection
      ssh -T git@github.com
3. Create a folder in Desktop to house Github repo
    mkdir ~/Desktop/github && cd ~/Desktop/github
4. Clone repo
    git clone git@github.com:rdalida/REPO-NAME.git
4. Confirm remote
    git remove -v
    If repair needed
      git remote add origin git@github.com:rdalida/REPO-NAME.git
      git push -u origin branch-name
5. Create new branch
    git checkout -b branch/name
1. Update User Config JSON
2. Update validation logic 
3. Update validator __init__ 
4. Update rules enabled in User Config JSON
5. Update readable rules in Config Manager
6. Update Expected Roles and Priority Order in main Validator App


GIT WORKFLOW:
1. stage changes
    git add . (stages all changes)
    git status (to verify what's being staged)
2. commit changes
    git commit -m "Short, descriptive message"
      Good format: "feat: updated validation logic for students file"
3. push changes to Github
    git push -u origin branch-name 
4. open Pull Request (PR)
    Go to Github >>> Pulls
    Click "Compare & pull request"
    Add title and description of changes
    Select reviewer

GIT NOTES:
check what's staged
  git status
  git diff --cached
check branch
  git branch
delete branch
  git branch -d branch-name
create new branch
  git checkout -b branch-name
  switch branch
  git checkout branch-name
remove all changes
  git restore .