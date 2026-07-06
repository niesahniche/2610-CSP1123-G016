# CampusCook

CampusCook is a Django web application for managing recipes, groceries, and cooking features.  
It includes custom user management, recipe uploads, grocery list functionality, and feedback forms.

---

## 📂 Project Structure

2610-CSP1123-G016-MAIN/
│
├── 2610-CSP1123-G016-campuscook/
│   ├── campuscook/        # Django project core (settings, urls, wsgi, asgi)
│   ├── pages/             # Django app with views, urls, templates
│   ├── media/             # Uploaded files (recipe_images)
│   ├── templates/pages/   # HTML templates (home, grocery, recipes, etc.)
│   ├── manage.py          # Django management script
│   ├── db.sqlite3         # Default SQLite database
│   ├── requirements.txt   # Python dependencies
│   └── .env               # Environment variables (email, API keys)


---

## ⚙️ Setup Instructions

### 1. Install Python
- Recommended: **Python 3.12** (stable for Django + Pillow).  
- Download from [python.org/downloads](https://www.python.org/downloads/).  
- During installation:  
  ✅ Check **“Add Python to PATH”**  
  ✅ Ensure `pip` is installed.

> ⚠️ Python 3.14 may cause Pillow errors on Windows. Use 3.12 for smooth setup.

---

### 2. Create a Virtual Environment
```powershell
cd 2610-CSP1123-G016-main
py -m venv .venv
.\.venv\Scripts\activate

---

### 3. Install Dependencies

```powershell
py -m pip install -r requirements.txt

If requirements.txt is incomplete, install manually:
```powershell
py -m pip install django python-dotenv requests pillow

---

### 4. Apply Migrations

```powershell
py manage.py makemigrations
py manage.py migrate

---

### 5. Apply Migrations

```powershell
py manage.py runserver

Open your browser at:
👉 http://127.0.0.1:8000/

