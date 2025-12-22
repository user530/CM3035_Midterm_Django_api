from rest_framework.test import APITestCase
from rest_framework import status

from students_app.models import Student, StudentMetrics, Department, Hobby
from students_app.contstants import (
    DailyStudyTime,
    MediaVideoTime,
    TravelingTime,
    StudyPreference,
    FinancialStatus,
)



class AnalyticsApiTests(APITestCase):
    # Analytic routes
    STUDENTS = '/api/students'
    STUDENTS_SEARCH = '/api/students/search'
    DEPT_SUMMARY = '/api/analytics/departments/summary'
    PARTTIME_IMPACT = '/api/analytics/parttime/impact'
    STUDYTIME_PERF = '/api/analytics/studytime/performance'
    RISK_LIST = '/api/analytics/risk'
    BMI_DIST = '/api/analytics/bmi/distribution'

    # Helper function to create Student using API
    def _create_student_api(
        self,
        *,
        gender: str,
        department_pk: int,
        hobby_pk: int,
        height_cm: int,
        weight_kg: int,
        college_mark: int,
        stress_level: str,
        part_time_job: bool,
        daily_studying_time: str,
    ):
        payload = {
            'gender': gender,
            'department': department_pk,
            'hobby': hobby_pk,
            'height_cm': height_cm,
            'weight_kg': weight_kg,
            'metrics': {
                'certification_course': False,
                'mark_10th': 70,
                'mark_12th': 70,
                'college_mark': college_mark,
                'daily_studying_time': daily_studying_time,
                'prefer_to_study_in': self.pref,
                'salary_expectation': 50000,
                'likes_degree': True,
                'part_time_job': part_time_job,
                'financial_status': self.fin,
                'willingness_percent': 60,
                'social_media_video': self.media,
                'travelling_time': self.travel,
                'stress_level': stress_level,
            },
        }

        # Make POST request and create student entity
        res = self.client.post(self.STUDENTS, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.content.decode('utf-8'))

        return res.json()

    # Setup small dummy dataset with fixed values, ready for testing
    def setUp(self):
        # Test Departments and Hobbies
        self.dep_cse = Department.objects.create(name='CSE')
        self.dep_bca = Department.objects.create(name='BCA')
        self.hob_reading = Hobby.objects.create(name='Reading')
        self.hob_gaming = Hobby.objects.create(name='Gaming')

        # Enum options
        self.daily_study_a = DailyStudyTime.choices[0][0]
        self.daily_study_b = DailyStudyTime.choices[1][0] if len(DailyStudyTime.choices) > 1 else self.daily_study_a
        self.media = MediaVideoTime.choices[0][0]
        self.travel = TravelingTime.choices[0][0]
        self.pref = StudyPreference.choices[0][0]
        self.fin = FinancialStatus.choices[0][0]

        # Create a small dummy dataset
        # Student 1: Part-time job, Bad stress, Low mark ('risky' student)
        self._create_student_api(
            gender='Male',
            department_pk=self.dep_cse.pk,
            hobby_pk=self.hob_reading.pk,
            height_cm=170,
            weight_kg=70,
            college_mark=45,
            stress_level='Bad',
            part_time_job=True,
            daily_studying_time=self.daily_study_a,
        )

        # Student 2: No part-time job, Good stress, High mark
        self._create_student_api(
            gender='Female',
            department_pk=self.dep_cse.pk,
            hobby_pk=self.hob_gaming.pk,
            height_cm=160,
            weight_kg=50,
            college_mark=88,
            stress_level='Good',
            part_time_job=False,
            daily_studying_time=self.daily_study_b,
        )

        # Student 3: Different department, Bad stress, Mark 60 (default threshold value)
        self._create_student_api(
            gender='Male',
            department_pk=self.dep_bca.pk,
            hobby_pk=self.hob_reading.pk,
            height_cm=180,
            weight_kg=90,
            college_mark=50,
            stress_level='Bad',
            part_time_job=False,
            daily_studying_time=self.daily_study_a,
        )



    # === ENDPOINT 1: Students search ===
    def test_students_search_works_and_filters(self):
        # We filter by CSE department and Female gender, it should return student 2
        res = self.client.get(
            self.STUDENTS_SEARCH,
            {'department': self.dep_cse.pk, 'gender': 'Female', 'limit': 50},
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK, res.content.decode('utf-8'))

        payload = res.json()

        self.assertIn('results', payload)
        self.assertEqual(payload['count'], 1)
        self.assertEqual(payload['results'][0]['department'], 'CSE')
        self.assertEqual(payload['results'][0]['gender'], 'Female')
        self.assertTrue('id' in payload['results'][0] or 'pk' in payload['results'][0])



    # === ENDPOINT 2: Department summary ===
    def test_departments_summary_returns_expected_departments(self):
        res = self.client.get(self.DEPT_SUMMARY)

        self.assertEqual(res.status_code, status.HTTP_200_OK, res.content.decode('utf-8'))

        payload = res.json()

        self.assertIn('results', payload)

        names = {r['department_name'] for r in payload['results']}

        # Both departments have summary
        self.assertIn('CSE', names)
        self.assertIn('BCA', names)

        # CSE has 2 students
        cse_row = next(r for r in payload['results'] if r['department_name'] == 'CSE')

        self.assertEqual(cse_row['student_count'], 2)

    

    # === ENDPOINT 3: Impact of the part-time job ===
    def test_parttime_impact_returns_two_groups(self):
        res = self.client.get(self.PARTTIME_IMPACT)

        self.assertEqual(res.status_code, status.HTTP_200_OK, res.content.decode('utf-8'))

        payload = res.json()

        # Both grops + correct split
        self.assertIn('with_part_time_job', payload)
        self.assertIn('without_part_time_job', payload)

        self.assertEqual(payload['with_part_time_job']['student_count'], 1)
        self.assertEqual(payload['without_part_time_job']['student_count'], 2)

        # Correctly rounded
        avg = payload['with_part_time_job']['avg_college_mark']

        if avg is not None:
            self.assertIsInstance(avg, (int, float))
            self.assertLessEqual(len(str(avg).split('.')[-1]), 2)



    # === ENDPOINT 4: Effect of the studytime ===
    def test_studytime_performance_groups(self):
        res = self.client.get(self.STUDYTIME_PERF)

        self.assertEqual(res.status_code, status.HTTP_200_OK, res.content.decode('utf-8'))

        payload = res.json()

        self.assertIn('results', payload)
        self.assertGreaterEqual(payload['count'], 1)

        # Ensure each row has the expected keys
        row = payload['results'][0]

        self.assertIn('daily_studying_time', row)
        self.assertIn('student_count', row)
        self.assertIn('avg_college_mark', row)



    # === ENDPOINT 5: Risk list (high stres and low marks) ===
    def test_risk_list_default_finds_bad_stress_low_marks(self):

        res = self.client.get(self.RISK_LIST)

        self.assertEqual(res.status_code, status.HTTP_200_OK, res.content.decode('utf-8'))

        payload = res.json()

        self.assertIn('results', payload)
        # Should include student with mark 45 and mark 50
        self.assertGreaterEqual(payload['count'], 2)

        marks = [r['college_mark'] for r in payload['results']]

        self.assertIn(45, marks)
        self.assertIn(50, marks)



    # === ENDPOINT 6: BMI distribution ===
    def test_bmi_distribution_works(self):
        res = self.client.get(self.BMI_DIST)

        self.assertEqual(res.status_code, status.HTTP_200_OK, res.content.decode('utf-8'))

        payload = res.json()

        self.assertIn('results', payload)
        self.assertGreaterEqual(payload['count'], 1)

        row = payload['results'][0]

        # Required keys
        self.assertIn('total', row)
        self.assertIn('buckets', row)
        self.assertIn('avg_bmi', row)

    def test_bmi_distribution_group_by_gender(self):
        res = self.client.get(self.BMI_DIST, {'by': 'gender'})

        self.assertEqual(res.status_code, status.HTTP_200_OK, res.content.decode('utf-8'))

        payload = res.json()

        self.assertEqual(payload['group_by'], 'gender')

        genders = {r.get('gender') for r in payload['results']}

        # Group by gender
        self.assertIn('Male', genders)
        self.assertIn('Female', genders)