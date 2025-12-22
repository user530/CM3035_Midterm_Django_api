from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings

from typing import cast

def require_setting(name: str) -> str:
    value = cast(str | None, getattr(settings, name, None))

    if value is None or not value.strip():
        raise CommandError(f'{name} is required and cannot be empty!')

    return value



class Command(BaseCommand):
    help = 'Create a superuser from env vars if it doesn`t exist yet.'

    def handle(self, *args, **options):
        User = get_user_model()

        # Load and assert credentials
        username = require_setting('ADMIN_USERNAME')
        password = require_setting('ADMIN_PASSWORD')
        email = require_setting('ADMIN_EMAIL')

        # Guard clause
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f'Superuser `{username}` already exists.'))
            return

        # Create super user, if needed, and log
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Created superuser `{username}` from env/settings.'))