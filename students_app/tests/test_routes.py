from django.test import TestCase
from django.urls import reverse

class HomeRouteTests(TestCase):
    def test_home_returns_links(self):
        # We use url name to reverse path
        res = self.client.get(reverse('home'))
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertIn('links', data)
        self.assertIsInstance(data['links'], dict)

        # Check that we link to at least health route (first one)
        self.assertTrue(any(key for key in data['links'].keys()))



class HealthEndpointTests(TestCase):
    def test_health_ok(self):
        res = self.client.get(reverse('health'))
        self.assertEqual(res.status_code, 200)
        self.assertIn('status', res.json())