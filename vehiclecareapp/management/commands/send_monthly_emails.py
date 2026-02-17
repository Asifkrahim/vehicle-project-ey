from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Sends monthly maintenance reminders to all users'

    def handle(self, *args, **kwargs):
        users = User.objects.filter(email__isnull=False).exclude(email='')
        
        self.stdout.write(f"Found {users.count()} users with emails...")

        for user in users:
            try:
                subject = "VehicleCare+: Monthly Check-in"
                message = (
                    f"Hello {user.username},\n\n"
                    f"It is the end of the month! \n"
                    f"It has been roughly one month since your last maintenance check.\n\n"
                    f"Please log in to your dashboard to check if any service is due or update your odometer readings.\n\n"
                    f"http://127.0.0.1:8000/login\n\n"
                    f"Drive Safe,\nVehicleCare+ Team"
                )
                
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f'Sent email to {user.email}'))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to send to {user.email}: {e}'))