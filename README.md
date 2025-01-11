# HEXA Operation Tracking System (OTS)

A web-based system for tracking operations and activities, replacing the previous Google Sheets system.

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## Features
- User authentication and authorization
- Project management
- Operation tracking
- Activity logging
- Interactive data tables with filtering and sorting
- RESTful API endpoints
