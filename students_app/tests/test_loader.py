from django.test import TestCase
from django.core.management import call_command
from pathlib import Path
import csv
import tempfile

from students_app.models import Department, Hobby, Student, StudentMetrics
from students_app.contstants import (
    DAILY_STUDY_TIME_MAP,
    MEDIA_VIDEO_TIME_MAP,
    TRAVELING_TIME_MAP,
    GENDER_MAP,
    STUDY_PREFERENCE_MAP,
    STRESS_LEVEL_MAP,
    FINANCIAL_STATUS_MAP,
)

def make_dummy_CSV(dept_name='CSE', hobby_name='Reading'):
    '''
    Create dummy CSV file with one row and return path to it
    '''
    # Pick valid values from the maps
    gender_raw = next(iter(GENDER_MAP.keys()))
    pref_raw = next(iter(STUDY_PREFERENCE_MAP.keys()))
    study_raw = next(iter(DAILY_STUDY_TIME_MAP.keys()))
    media_raw = next(iter(MEDIA_VIDEO_TIME_MAP.keys()))
    travel_raw = next(iter(TRAVELING_TIME_MAP.keys()))
    stress_raw = next(iter(STRESS_LEVEL_MAP.keys()))
    fin_raw = next(iter(FINANCIAL_STATUS_MAP.keys()))

    # Dummy data (header and one row)

    header = [
        'Certification Course', 'Gender', 'Department', 'Height(CM)', 'Weight(KG)',
        '10th Mark', '12th Mark', 'college mark', 'hobbies',
        'daily studing time', 'prefer to study in', 'salary expectation',
        'Do you like your degree?', 'willingness to pursue a career based on their degree  ',
        'social medai & video', 'Travelling Time ', 'Stress Level ', 'Financial Status', 'part-time job'
    ]

    row = [
        'Yes', gender_raw, dept_name, '170', '68.9',
        '80', '85', '78', hobby_name,
        study_raw, pref_raw, '50000',
        'Yes', '70%',
        media_raw, travel_raw, stress_raw, fin_raw, 'No'
    ]

    # Create test CSV file and write our dummy data
    tmp = tempfile.NamedTemporaryFile(mode='w', newline='', suffix='.csv', delete=False)

    with tmp:
        w = csv.writer(tmp)
        w.writerow(header)
        w.writerow(row)

    return tmp.name

class LoaderTests(TestCase):
    def test_loader_creates_students_and_metrics(self):
        '''
        Test that loader works correctly
        '''
        csv = make_dummy_CSV()

        # CSV path
        csv_path = Path(csv)

        # Run loader command
        call_command('load_students', str(csv_path), '--truncate', '--batch-size', '200')

        # Check that student and metrics loadded correctly
        self.assertGreater(Student.objects.count(), 0)
        self.assertEqual(Student.objects.count(), StudentMetrics.objects.count())



class LoaderTruncateTests(TestCase):
    def test_truncate_clears_previous_data(self):
        # First file: department - CSE, hobby - Reading
        csv1 = make_dummy_CSV(dept_name='CSE', hobby_name='Reading')
        # Load into Db
        call_command('load_students', csv1, '--truncate', '--batch-size', '50')

        # Sanity check
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(StudentMetrics.objects.count(), 1)
        self.assertEqual(Department.objects.count(), 1)
        self.assertEqual(Hobby.objects.count(), 1)
        self.assertTrue(Department.objects.filter(name='CSE').exists())

        # Second load: department = EEE, hobby - Gaming, with --truncate argument, command should clear previous data
        csv2 = make_dummy_CSV(dept_name='EEE', hobby_name='Gaming')
        # Second load (with truncation)
        call_command('load_students', csv2, '--truncate', '--batch-size', '50')

        # Sanity check
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(StudentMetrics.objects.count(), 1)

        # Confirm previous data was the one erased
        self.assertFalse(Department.objects.filter(name='CSE').exists())
        self.assertFalse(Hobby.objects.filter(name='Reading').exists())
        self.assertTrue(Department.objects.filter(name='EEE').exists())
        self.assertTrue(Hobby.objects.filter(name='Gaming').exists())