import csv
from pathlib import Path
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from students_app.models import Department, Hobby, Student, StudentMetrics
from students_app.contstants import (
    normalize_str,
    GENDER_MAP,
    STUDY_PREFERENCE_MAP,
    STRESS_LEVEL_MAP,
    FINANCIAL_STATUS_MAP,
    DAILY_STUDY_TIME_MAP,
    MEDIA_VIDEO_TIME_MAP,
    TRAVELING_TIME_MAP,
)

# === Helper parser functions ===
def parse_bool(value: str) -> bool:
    v = str(value).strip().casefold()

    if v in {'yes', 'y', 'true', '1'}:
        return True
    if v in {'no', 'n', 'false', '0'}:
        return False

    raise ValueError(f'Invalid boolean value: {value!r}')

def parse_int(value: str) -> int:
    return int(str(value).strip())

def parse_float(value: str) -> float:
    return float(str(value).strip())

def parse_percent(value: str) -> int:
    '''
    Kaggle field looks like '70%'. We normalize it to int value 70.
    '''
    s = str(value).strip()
    s = s.replace('%', '').strip()

    return int(float(s))

def parse_height_cm(value: str) -> int:
    '''
    Validate height and round it to int
    '''
    h = int(round(float(str(value).strip())))
    if not (50 <= h <= 250):
        raise ValueError(f'Unrealistic height_cm: {value!r} -> {h}')

    return h

def parse_weight_kg(value: str) -> int:
    '''
    Validate weigh and round it to int
    '''
    w = int(round(float(str(value).strip())))
    if not (20 <= w <= 300):
        raise ValueError(f'Unrealistic weight_kg: {value!r} -> {w}')

    return w

def normalize_header(h: str) -> str:
    '''
    Normalize CSV headers:
    '''
    h = str(h).strip()
    h = re.sub(r'\s+', ' ', h)

    return h.casefold()

def normalize_cell(v: str) -> str:
    '''Normalize cell strings similarly'''
    v = '' if v is None else str(v)
    v = v.strip()
    v = re.sub(r'\s+', ' ', v)

    return v

# === CSV column names (with typos and all) ===
COL_CERT = normalize_header("Certification Course")
COL_GENDER = normalize_header("Gender")
COL_DEPT = normalize_header("Department")
COL_HEIGHT = normalize_header("Height(CM)")
COL_WEIGHT = normalize_header("Weight(KG)")
COL_MARK10 = normalize_header("10th Mark")
COL_MARK12 = normalize_header("12th Mark")
COL_COLLEGE = normalize_header("college mark")
COL_HOBBY = normalize_header("hobbies")
COL_STUDY_TIME = normalize_header("daily studing time")
COL_PREF = normalize_header("prefer to study in")
COL_SALARY = normalize_header("salary expectation")
COL_LIKE_DEGREE = normalize_header("Do you like your degree?")
COL_WILL = normalize_header("willingness to pursue a career based on their degree")
COL_MEDIA = normalize_header("social medai & video")
COL_TRAVEL = normalize_header("Travelling Time")
COL_STRESS = normalize_header("Stress Level")
COL_FIN = normalize_header("Financial Status")
COL_PARTTIME = normalize_header("part-time job")



class Command(BaseCommand):
    help = 'Load Student Attitude & Behavior CSV into the database.'

    # We dfeine command arguments 
    def add_arguments(self, parser):
        parser.add_argument(
            'csv_path',
            type=str,
            help='Path to CSV file (e.g. `data/Student Attitude and Behavior.csv`)',
        )

        parser.add_argument(
            '--truncate',
            action='store_true',
            help='Clear existing StudentMetrics/Student/Department/Hobby data before loading from file',
        )

        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Batch size for bulk_create operations (default: 500)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = Path(options['csv_path']).expanduser().resolve()
        truncate = bool(options['truncate'])
        batch_size = int(options['batch_size'])

        if not csv_path.exists() or not csv_path.is_file():
            raise CommandError(f'CSV file not found: {csv_path}!')

        # If truncate option present: clear tables for deterministic re-runs
        if truncate:
            # Delete in dependency order
            StudentMetrics.objects.all().delete()
            Student.objects.all().delete()
            Department.objects.all().delete()
            Hobby.objects.all().delete()
            # Log it
            self.stdout.write(self.style.WARNING('Cleared existing data.'))

        with csv_path.open('r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            # Normalize headers
            normalized_fnames = {normalize_header(header) for header in fieldnames}
            # All fields required
            required = [
                COL_CERT, COL_GENDER, COL_DEPT, COL_HEIGHT, COL_WEIGHT,
                COL_MARK10, COL_MARK12, COL_COLLEGE, COL_HOBBY,
                COL_STUDY_TIME, COL_PREF, COL_SALARY, COL_LIKE_DEGREE,
                COL_WILL, COL_MEDIA, COL_TRAVEL, COL_STRESS, COL_FIN, COL_PARTTIME
            ]
            # Check missing columns
            missing = [col for col in required if col not in normalized_fnames]

            if missing:
                raise CommandError(f'CSV missing required columns: {missing}')

            rows = [
                {normalize_header(k): v for k, v in raw.items()}
                for raw in reader
            ]

        # Guard clause for empty
        if not rows:
            self.stdout.write(self.style.WARNING('CSV is empty. Nothing to load.'))
            return

        # Ensure Departments & Hobbies exist
        dept_names = sorted({normalize_str(row[COL_DEPT]) for row in rows})
        hobby_names = sorted({normalize_str(row[COL_HOBBY]) for row in rows})

        # Bulk create departments and Hobbies
        Department.objects.bulk_create(
            [Department(name=name) for name in dept_names],
            ignore_conflicts=True,
            batch_size=batch_size,
        )

        Hobby.objects.bulk_create(
            [Hobby(name=name) for name in hobby_names],
            ignore_conflicts=True,
            batch_size=batch_size,
        )


        # Create a dict "cache"
        dept_by_name = {department.name: department for department in Department.objects.filter(name__in=dept_names)}
        hobby_by_name = {hobby.name: hobby for hobby in Hobby.objects.filter(name__in=hobby_names)}

        # Build Students + keep parsed metric payloads aligned by index
        students: list[Student] = []
        metrics_payloads: list[dict] = []
        errors: list[str] = []

        # Iterate and create students (populating list) and collecting metrics (row 1 is header, so we start from 2)
        for ind, row in enumerate(rows, start=2):
            try:
                dept_name = normalize_str(row[COL_DEPT])
                hobby_name = normalize_str(row[COL_HOBBY])
                dept = dept_by_name[dept_name]
                hobby = hobby_by_name[hobby_name]

                gender = GENDER_MAP[normalize_str(row[COL_GENDER])]

                # Create student
                student = Student(
                    gender=gender,
                    department=dept,
                    height_cm=parse_height_cm(row[COL_HEIGHT]),
                    weight_kg=parse_weight_kg(row[COL_WEIGHT]),
                    hobby=hobby,
                )
                students.append(student)

                # Parse & store everything needed for creating of student survey metrics
                study_enum, study_min = DAILY_STUDY_TIME_MAP[normalize_str(row[COL_STUDY_TIME])]
                media_enum, media_min = MEDIA_VIDEO_TIME_MAP[normalize_str(row[COL_MEDIA])]
                travel_enum, travel_min = TRAVELING_TIME_MAP[normalize_str(row[COL_TRAVEL])]

                surv_metrics = {
                    'certification_course': parse_bool(row[COL_CERT]),
                    'mark_10th': parse_float(row[COL_MARK10]),
                    'mark_12th': parse_float(row[COL_MARK12]),
                    'college_mark': parse_float(row[COL_COLLEGE]),
                    'daily_studying_time': study_enum,
                    'study_minutes': study_min,
                    'prefer_to_study_in': STUDY_PREFERENCE_MAP[normalize_str(row[COL_PREF])],
                    'salary_expectation': parse_int(row[COL_SALARY]),
                    'likes_degree': parse_bool(row[COL_LIKE_DEGREE]),
                    'part_time_job': parse_bool(row[COL_PARTTIME]),
                    'financial_status': FINANCIAL_STATUS_MAP[normalize_str(row[COL_FIN])],
                    'willingness_percent': parse_percent(row[COL_WILL]),
                    'social_media_video': media_enum,
                    'social_minutes': media_min,
                    'travelling_time': travel_enum,
                    'travel_minutes': travel_min,
                    'stress_level': STRESS_LEVEL_MAP[normalize_str(row[COL_STRESS])],
                }
                metrics_payloads.append(surv_metrics)

            except Exception as exc:
                errors.append(f'Line {ind}: {exc}')
                continue

        # Guard clause
        if not students:
            raise CommandError(f'All rows failed to parse. First errors: {errors[:5]}')

        # DB Bulk create students
        created_students = Student.objects.bulk_create(students, batch_size=batch_size)

        # Guard clause - failed student creatin
        if any(student.pk is None for student in created_students):
            raise CommandError(
                'bulk_create did not populate Student table (no PKs), can`t proceed with metrics creation!'
            )

        # Student metrics creation
        metrics: list[StudentMetrics] = []
        # We use zip trick to iterate over 2 iterables at the same time (pair iteration)
        for student, payload in zip(created_students, metrics_payloads):
            metrics.append(StudentMetrics(student=student, **payload))

        # Bulk create metrics
        StudentMetrics.objects.bulk_create(metrics, batch_size=batch_size)

        # Log to console
        self.stdout.write(self.style.SUCCESS('Bulk CSV load finished.'))
        self.stdout.write(f'File: {csv_path}')
        self.stdout.write(f'Rows read: {len(rows)}')
        self.stdout.write(f'Students created: {len(created_students)}')
        self.stdout.write(f'Metrics created: {len(metrics)}')
        self.stdout.write(f'Rows skipped (parse errors): {len(errors)}')

        # Log errors
        if errors:
            self.stdout.write(self.style.WARNING('First 10 parse errors:'))
            for msg in errors[:10]:
                self.stdout.write(f'  - {msg}')
            if len(errors) > 10:
                self.stdout.write(f'  ... and {len(errors) - 10} more.')