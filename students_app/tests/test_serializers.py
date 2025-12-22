from django.test import TestCase
from typing import cast

from students_app.models import Student, StudentMetrics, Department, Hobby
from students_app.serializers import StudentWriteSerializer
from students_app.contstants import (
    DailyStudyTime, 
    MediaVideoTime, 
    TravelingTime, 
    StudyPreference, 
    StressLevel, 
    FinancialStatus,
)

class StudentSerializerTests(TestCase):
    def setUp(self):
        # Create dummy department and hobby
        self.department = Department.objects.create(name='CSE')
        self.hobby = Hobby.objects.create(name='Reading')

    def generate_json_payload(self):
        # Just pick enum values
        daily_study = DailyStudyTime.choices[0][0]
        media = MediaVideoTime.choices[0][0]
        travel = TravelingTime.choices[0][0]
        pref = StudyPreference.choices[0][0]
        stress = StressLevel.choices[0][0]
        fin = FinancialStatus.choices[0][0]

        return {
            'gender': 'Male',
            'department': self.department.pk,
            'hobby': self.hobby.pk,
            'height_cm': 170,
            'weight_kg': 69,
            'metrics': {
                'certification_course': True,
                'mark_10th': 80,
                'mark_12th': 85,
                'college_mark': 78,

                'daily_studying_time': daily_study,
                'prefer_to_study_in': pref,

                'salary_expectation': 50000,
                'likes_degree': True,
                'part_time_job': False,
                'financial_status': fin,

                'willingness_percent': 70,

                'social_media_video': media,
                'travelling_time': travel,

                'stress_level': stress,

                # Try to pass some minutes manually, but this shouldnt end up in the resulted row
                'study_minutes': 999,
                'social_minutes': 999,
                'travel_minutes': 999,
            },
        }



    def test_nested_create_creates_student_and_metrics(self):
        data = self.generate_json_payload()
        ser = StudentWriteSerializer(data=data)

        self.assertTrue(ser.is_valid(), ser.errors)

        student =  cast(Student, ser.save())
        
        metrics = StudentMetrics.objects.get(student=student)

        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(StudentMetrics.objects.count(), 1)
        
        self.assertEqual(student.department.pk, self.department.pk)
        self.assertEqual(student.hobby.pk, self.hobby.pk)

        # Ensure metrics created for the student
        self.assertEqual(metrics.college_mark, 78)



    def test_minutes_are_derived_not_accepted(self):
        data = self.generate_json_payload()
        ser = StudentWriteSerializer(data=data)

        self.assertTrue(ser.is_valid(), ser.errors)

        student = ser.save()
        metrics = StudentMetrics.objects.get(student=student)

        # Client sent 999, but it shouldnt be stored
        self.assertNotEqual(metrics.study_minutes, 999)
        self.assertNotEqual(metrics.social_minutes, 999)
        self.assertNotEqual(metrics.travel_minutes, 999)

        # They should be positive ints (derived)
        self.assertIsInstance(metrics.study_minutes, int)
        self.assertGreater(metrics.study_minutes, 0)

    

    def test_nested_update_recomputes_minutes(self):
        data = self.generate_json_payload()
        ser = StudentWriteSerializer(data=data)

        self.assertTrue(ser.is_valid(), ser.errors)

        student = ser.save()
        metrics = StudentMetrics.objects.get(student=student)

        old_minutes = metrics.study_minutes

        # Get a list of egliable options
        choices = [c[0] for c in DailyStudyTime.choices]

        if len(choices) < 2:
            self.skipTest('Not enough DailyStudyTime choices to recompute')

        new_study = choices[1]

        update_data = {
            'department': self.department.pk,
            'hobby': self.hobby.pk,
            'metrics': {
                'daily_studying_time': new_study,
            },
        }

        ser2 = StudentWriteSerializer(instance=student, data=update_data, partial=True)
        self.assertTrue(ser2.is_valid(), ser2.errors)

        student2 = ser2.save()
        metrics2 = StudentMetrics.objects.get(student=student2)

        self.assertNotEqual(metrics2.study_minutes, old_minutes)



    def test_missing_metrics_is_invalid(self):
        data = self.generate_json_payload()
        data.pop('metrics')

        ser = StudentWriteSerializer(data=data)

        self.assertFalse(ser.is_valid())
        self.assertIn('metrics', ser.errors)