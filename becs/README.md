# BECS – Blood Bank Management (Part 3)

PyQt6 + SQLite project for managing a blood bank, including full support for **PART 11** and **HIPAA**.

---

## Installation & Run

### 1) Create virtual environment
```powershell
cd <repo-root>
python -m venv src/.venv
src/.venv/Scripts/Activate.ps1
pip install -r requirements.txt

cd src
py -m becs.migrate_sqlite --db ..\becs.db --set-admin admin admin123 "Admin" "User"
py -m becs.create_user --db ..\becs.db --username med1 --password med123 --first Med --last User --role medical
py -m becs.create_user --db ..\becs.db --username student1 --password stud123 --first Stu --last Dent --role student

py -m becs.app --db ..\becs.db
