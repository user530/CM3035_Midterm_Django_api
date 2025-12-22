from rest_framework.test import APITestCase
from rest_framework import status
from typing import Any
from django.http import HttpResponse

from students_app.models import Student, StudentMetrics, Department, Hobby
from students_app.contstants import (
    DailyStudyTime,
    MediaVideoTime,
    TravelingTime,
    StudyPreference,
    StressLevel,
    FinancialStatus,
)

def json_or_text(res: HttpResponse) -> Any:
    '''
    Helper function to safely access response payload and fix type errors
    '''
    try:
        return res.json()
    except Exception:
        try:
            return res.content.decode('utf-8')
        except Exception:
            return str(res)



class CrudApiTests(APITestCase):
    BASE_STUDENTS = '/api/students'
    BASE_DEPARTMENTS = '/api/departments'
    BASE_HOBBIES = '/api/hobbies'

    def setUp(self):
        # Create dummy department and hobby
        self.department = Department.objects.create(name='CSE')
        self.hobby = Hobby.objects.create(name='Reading')

    def _student_payload(self):
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
            },
        }

    def _create_student_via_api(self):
        res = self.client.post(self.BASE_STUDENTS, self._student_payload(), format='json')
        payload = json_or_text(res)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, payload)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(StudentMetrics.objects.count(), 1)

        return payload

    # === STUDENTS CRUD ===
    def test_students_list_returns_200(self):
        self._create_student_via_api()
        res = self.client.get(self.BASE_STUDENTS)
        payload = json_or_text(res)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Should be a list-like response (list or paginated dict)
        if isinstance(payload, dict) and 'results' in payload:
            self.assertGreaterEqual(len(payload['results']), 1)
        else:
            self.assertGreaterEqual(len(payload), 1)

    def test_students_create_creates_student_and_metrics(self):
        res = self.client.post(self.BASE_STUDENTS, self._student_payload(), format='json')
        payload = json_or_text(res)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, payload)

        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(StudentMetrics.objects.count(), 1)

        student_id = payload.get('id') or payload.get('pk')

        self.assertIsNotNone(student_id, f'Expected created student id in response, got: {payload}')

        # Verify nested metrics exist in DB and link is correct
        student = Student.objects.get(id=student_id)
        metrics = StudentMetrics.objects.get(student=student)

        self.assertEqual(metrics.college_mark, 78)

    def test_students_retrieve_returns_200(self):
        created = self._create_student_via_api()
        student_id = created.get('id') or created.get('pk')

        res = self.client.get(f'{self.BASE_STUDENTS}/{student_id}')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_students_patch_updates_metrics(self):
        created = self._create_student_via_api()
        student_id = created.get('id') or created.get('pk')

        student = Student.objects.get(id=student_id)
        old_minutes = StudentMetrics.objects.get(student=student).study_minutes

        # Select different study time option
        choices = [c[0] for c in DailyStudyTime.choices]
        if len(choices) < 2:
            self.skipTest('Not enough DailyStudyTime choices to verify recompute')
        new_study = choices[1]
        patch_payload = {'metrics': {'daily_studying_time': new_study}}

        res = self.client.patch(f'{self.BASE_STUDENTS}/{student_id}', patch_payload, format='json')
        payload = json_or_text(res)

        self.assertIn(res.status_code, (status.HTTP_200_OK, status.HTTP_202_ACCEPTED), payload)

        new_minutes = StudentMetrics.objects.get(student=student).study_minutes

        self.assertNotEqual(new_minutes, old_minutes)

    def test_students_delete_returns_204(self):
        created = self._create_student_via_api()
        student_id = created.get('id') or created.get('pk')

        res = self.client.delete(f'{self.BASE_STUDENTS}/{student_id}')
        # Delete response might not contain any data
        self.assertIn(res.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK), getattr(res, 'data', None))

        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(StudentMetrics.objects.count(), 0)

    # === DEPARTMENTS CRUD ===
    def test_departments_crud_create_list_retrieve_update_delete(self):
        # Create department
        res = self.client.post(self.BASE_DEPARTMENTS, {'name': 'BCA'}, format='json')
        payload = json_or_text(res)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, payload)

        dept_id = payload.get('id') or payload.get('pk')

        self.assertIsNotNone(dept_id)

        # Departments list GET
        res = self.client.get(self.BASE_DEPARTMENTS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Single department GET
        res = self.client.get(f'{self.BASE_DEPARTMENTS}/{dept_id}')

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Single department PATCH
        res = self.client.patch(f'{self.BASE_DEPARTMENTS}/{dept_id}', {'name': 'BCA-UPDATED'}, format='json')

        self.assertIn(res.status_code, (status.HTTP_200_OK, status.HTTP_202_ACCEPTED), payload)
        self.assertTrue(Department.objects.filter(id=dept_id, name='BCA-UPDATED').exists())

        # Single department DELETE
        res = self.client.delete(f'{self.BASE_DEPARTMENTS}/{dept_id}')

        self.assertIn(res.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK), getattr(res, 'data', None))
        self.assertFalse(Department.objects.filter(id=dept_id).exists())

    def test_departments_delete_blocked_if_referenced(self):
        # Create student record
        self._create_student_via_api()

        # Try to delete Department referenced by this student
        res = self.client.delete(f'{self.BASE_DEPARTMENTS}/{self.department.pk}')

        # Allow Err 409 or 400
        self.assertIn(res.status_code, (status.HTTP_409_CONFLICT, status.HTTP_400_BAD_REQUEST), getattr(res, 'data', None))
        self.assertTrue(Department.objects.filter(id=self.department.pk).exists())

    # === HOBBY CRUD ===
    def test_hobbies_crud_create_list_retrieve_update_delete(self):
        # Create hobby
        res = self.client.post(self.BASE_HOBBIES, {'name': 'Gaming'}, format='json')
        payload = json_or_text(res)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, payload)

        hobby_id = payload.get('id') or payload.get('pk')

        self.assertIsNotNone(hobby_id)

        # Hobbies list GET
        res = self.client.get(self.BASE_HOBBIES)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Single hobby GET
        res = self.client.get(f'{self.BASE_HOBBIES}/{hobby_id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Single hobby PATCH
        res = self.client.patch(f'{self.BASE_HOBBIES}/{hobby_id}', {'name': 'Gaming-UPDATED'}, format='json')

        self.assertIn(res.status_code, (status.HTTP_200_OK, status.HTTP_202_ACCEPTED), payload)
        self.assertTrue(Hobby.objects.filter(id=hobby_id, name='Gaming-UPDATED').exists())

        # Single hobby DELETE
        res = self.client.delete(f'{self.BASE_HOBBIES}/{hobby_id}')

        self.assertIn(res.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK), getattr(res, 'data', None))
        self.assertFalse(Hobby.objects.filter(id=hobby_id).exists())

    def test_hobbies_delete_blocked_if_referenced(self):
        # Create student
        self._create_student_via_api()

        # Try to delete Hobby referenced by this student
        res = self.client.delete(f'{self.BASE_HOBBIES}/{self.hobby.pk}')

        # Allow Err 409 or 400
        self.assertIn(res.status_code, (status.HTTP_409_CONFLICT, status.HTTP_400_BAD_REQUEST), getattr(res, 'data', None))
        self.assertTrue(Hobby.objects.filter(id=self.hobby.pk).exists())