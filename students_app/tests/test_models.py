from django.test import TestCase
from django.db.models.deletion import ProtectedError
from students_app.models import Department, Hobby, Student, StudentMetrics
from students_app.contstants import (
    Gender, 
    DailyStudyTime, 
    MediaVideoTime, 
    TravelingTime, 
    StressLevel, 
    FinancialStatus, 
    StudyPreference,
)

class ModelProtectTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name='CSE')
        self.hobby = Hobby.objects.create(name='Reading')

        self.student = Student.objects.create(
            gender=Gender.MALE,
            department=self.dept,
            height_cm=170,
            weight_kg=70,
            hobby=self.hobby,
        )

    def test_department_delete_is_protected(self):
        # Department is protected while Student references it
        with self.assertRaises(ProtectedError):
            self.dept.delete()

    def test_hobby_delete_is_protected(self):
        # Hobby is protected while Student references it
        with self.assertRaises(ProtectedError):
            self.hobby.delete()

    def test_department_can_delete_after_student_removed(self):
        self.student.delete()
        # Now it should elete
        self.dept.delete()
        self.assertEqual(Department.objects.count(), 0)

    def test_hobby_can_delete_after_student_removed(self):
        self.student.delete()
        self.hobby.delete()
        self.assertEqual(Hobby.objects.count(), 0)



class ModelRelationshipTests(TestCase):
    def test_cascade_delete_student_deletes_metrics(self):
        dept = Department.objects.create(name='CSE')
        hobby = Hobby.objects.create(name='Reading')

        student = Student.objects.create(
            gender=Gender.MALE,
            department=dept,
            height_cm=170,
            weight_kg=70,
            hobby=hobby,
        )

        StudentMetrics.objects.create(
            student=student,
            certification_course=True,
            mark_10th=80,
            mark_12th=85,
            college_mark=75,
            daily_studying_time=DailyStudyTime.H1_2,
            prefer_to_study_in=StudyPreference.MORNING,
            salary_expectation=50000,
            likes_degree=True,
            willingness_percent=80,
            social_media_video=MediaVideoTime.M30_60,
            travelling_time=TravelingTime.M30_60,
            stress_level=StressLevel.GOOD,
            financial_status=FinancialStatus.GOOD,
            part_time_job=False,
            study_minutes=90,
            social_minutes=45,
            travel_minutes=45,
        )

        # Ensure it automatically deletes linked entity
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(StudentMetrics.objects.count(), 1)

        student.delete()

        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(StudentMetrics.objects.count(), 0)