# CampusCook

CampusCook is a Django web application for managing recipes, groceries, and cooking features. It allows users to upload recipes, save favorite recipes, manage grocery lists, and submit feedback.

## Project Structure

```
2610-CSP1123-G016-MAIN/
│
├── 2610-CSP1123-G016-campuscook/
│   ├── campuscook/          # Django project core files
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── pages/               # Main Django app
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── models.py
│   │   └── templates/
│   │
│   ├── media/               # Uploaded recipe images
│   ├── templates/pages/     # HTML templates
│   ├── manage.py            # Django management script
│   ├── db.sqlite3           # Default SQLite database
│   └── requirements.txt     # Python dependencies
```

## Setup Instructions

### 1. Install Python

Install Python 3.12 from the official Python website.

Python 3.12 is recommended because it is stable for Django and Pillow.

During installation, make sure to:

Tick `Add Python to PATH`
Ensure `pip` is installed

Avoid using Python 3.14 because it may cause Pillow installation errors on Windows.

## 2. Open the Project Folder

Open Command Prompt or VS Code terminal, then go to the project folder:

```powershell
cd 2610-CSP1123-G016-main
cd 2610-CSP1123-G016-campuscook
```

## 3. Create a Virtual Environment

Create a virtual environment:

```powershell
py -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\activate
```

## 4. Install Dependencies

Install all required packages:

```powershell
py -m pip install -r requirements.txt
```

If the `requirements.txt` file is incomplete, install the packages manually:

```powershell
py -m pip install django django-environ python-dotenv requests pillow
```

## 5. Apply Database Migrations

Run the following commands:

```powershell
py manage.py makemigrations
py manage.py migrate
```

## 6. Run the Development Server

Start the Django development server:

```powershell
py manage.py runserver
```

Then open the website in your browser:

```text
http://127.0.0.1:8000/
```

## Features

CampusCook includes the following features:

Custom user registration and login
Recipe upload and management
Recipe image upload
Save favorite recipes
Grocery list management
Prevention of duplicate grocery items
Feedback form
User session handling

## Troubleshooting

### `pip` is not recognized

Use this command instead:

```powershell
py -m pip install package_name
```

Example:

```powershell
py -m pip install django
```

### `ModuleNotFoundError: dotenv`

Install `python-dotenv`:

```powershell
py -m pip install python-dotenv
```

### `ModuleNotFoundError: requests`

Install `requests`:

```powershell
py -m pip install requests
```

### Pillow installation error

If Pillow fails to install, check your Python version.

Python 3.12 is recommended. Python 3.14 may cause compatibility issues on Windows.

## Notes for Team Members

Do not delete `db.sqlite3` unless the team agrees to reset the database.
Run migrations after pulling new model changes from GitHub.
Always activate the virtual environment before running the project.
Do not upload sensitive files or personal credentials to GitHub.
Use `py manage.py runserver` to test the website locally.
