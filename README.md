# ExcelMerge Pro

A modern Django web application for merging Excel and CSV files with intelligent duplicate detection.

## Features
- Upload two spreadsheet files (.xlsx, .xls, .csv)
- Automatic column analysis and preview
- Smart merge key suggestions scored by uniqueness
- Four join types: Inner, Outer, Left, Right
- Duplicate handling: keep first, last, or all
- Styled Excel output with all source sheets included

## Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Apply migrations (for sessions)

```bash
python manage.py migrate
```

### 3. Start the server

```bash
python manage.py runserver
```

### 4. Open in browser

Visit: **http://127.0.0.1:8000**

---

## Project Structure

```
excel_merger/
├── manage.py
├── requirements.txt
├── excel_merger/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── merger/                # Main app
│   ├── views.py           # All logic (upload, analyse, merge, download)
│   ├── urls.py
│   ├── templatetags/
│   │   └── dict_extras.py
│   └── templates/merger/
│       ├── base.html
│       ├── index.html     # Upload page
│       └── analyse.html   # Analysis + merge config + download
└── media/
    ├── uploads/           # Temporary uploaded files
    └── outputs/           # Generated merged files
```

## Notes
- Uploaded and output files are stored in the `media/` folder
- Sessions use file-based storage (no database needed for core features)
- Run `python manage.py migrate` only once to set up session tables if you switch to DB sessions
# Excel_Merger
