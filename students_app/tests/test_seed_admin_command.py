from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.management import call_command



class SeedAdminCommandTests(TestCase):
    @override_settings(
        ADMIN_USERNAME='admin_test',
        ADMIN_PASSWORD='admin123_test',
        ADMIN_EMAIL='admin_test@example.com',
    )
    def test_seed_admin_creates_superuser_if_missing(self):
        User = get_user_model()

        self.assertFalse(User.objects.filter(username='admin_test').exists())

        # Create a super user with admin pre-requisites
        call_command('seed_admin')

        user = User.objects.get(username='admin_test')

        # Check that it is correct super user with correct password
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password('admin123_test'))



    @override_settings(
        ADMIN_USERNAME='admin_test2',
        ADMIN_PASSWORD='admin123_test2',
        ADMIN_EMAIL='admin_test2@example.com',
    )
    def test_seed_admin_is_idempotent(self):
        User = get_user_model()

        # Create different super user
        call_command('seed_admin')

        self.assertEqual(User.objects.filter(username='admin_test2').count(), 1)

        # Check that command doesnt duplicate users
        call_command('seed_admin')

        self.assertEqual(User.objects.filter(username='admin_test2').count(), 1)