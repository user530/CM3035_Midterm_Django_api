from django.test import TestCase
from django.urls import reverse



class HomeRouteTests(TestCase):
    def test_home_returns_required_metadata_and_endpoints(self):
        res = self.client.get(reverse('home'))

        self.assertEqual(res.status_code, 200)

        data = res.json()

        # Required metadata fields
        self.assertIn('title', data)
        self.assertIn('api_version', data)
        self.assertIn('python_version', data)
        self.assertIn('django_version', data)

        # Links block
        self.assertIn('endpoints', data)
        self.assertIsInstance(data['endpoints'], dict)

        # Confirm that it includes key routes as hyperlinks
        endpoints = data['endpoints']

        self.assertIn('health', endpoints)
        self.assertIn('students', endpoints)
        self.assertIn('departments', endpoints)
        self.assertIn('hobbies', endpoints)

        # Admin block present
        self.assertIn('admin', data)
        self.assertIsInstance(data['admin'], dict)
        self.assertIn('url', data['admin'])

    def test_home_includes_analytics_links(self):
        res = self.client.get(reverse('home'))

        self.assertEqual(res.status_code, 200)

        endpoints = res.json()['endpoints']

        self.assertIn('students_search', endpoints)
        self.assertIn('departments_summary', endpoints)
        self.assertIn('parttime_impact', endpoints)
        self.assertIn('studytime_performance', endpoints)
        self.assertIn('risk_list', endpoints)
        self.assertIn('bmi_distribution', endpoints)



class HealthEndpointTests(TestCase):
    def test_health_ok(self):
        res = self.client.get(reverse('health'))

        self.assertEqual(res.status_code, 200)

        data = res.json()

        self.assertEqual(data.get('status'), 'ok')
        self.assertIn('service', data)
        self.assertIn('api_version', data)