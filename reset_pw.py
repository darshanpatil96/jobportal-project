import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobportal.settings')
django.setup()

from django.contrib.auth.models import User

user = User.objects.get(username='darshan')
user.set_password('admin123')
user.save()
print("Password reset successfully!")
print("Username: darshan")
print("Password: admin123")
