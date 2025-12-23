# CM3035 – Midterm Project  
Student Attitude & Behaviour API

CM3035 Midterm project — Django RESTful API
Advanced Web Design module midterm assesment

The application provides CRUD endpoints for managing students and related entities
There are also several analytical endpoints for exploring trends and statistics derived from the dataset, using advanced querries and filters

---

## Features

- CRUD API for:
  - Students
  - Departments
  - Hobbies

- Analytical endpoints:
  - Student search with multiple filters
  - Department-level summaries
  - Part-time job impact analysis
  - Study-time vs performance analysis
  - Risk list (high stress + low marks)
  - BMI distribution (with grouping option)

- CSV data loader command
- Adimn user creation to emulate production version
- Unit tests for CRUD, analytics, and commands
- Simple HTML homepage with hyperlinks to all endpoints

---

## Requirements

- Python 3.14
- Django 6.0
- Django REST Framework 3.16.1

All required Python packages are listed in `requirements.txt`.

---

## Setup (Local)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py load_students students_app/data/students_behaviour.csv --truncate
python manage.py seed_admin
python manage.py test
python manage.py runserver