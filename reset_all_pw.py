import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobportal.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile

resets = {
    "darshan":  "Admin@123",
    "darshan1": "Admin@123",
    "admin":    "Admin@123",
    "Dars":     "Employer@123",
    "ads":      "Seeker@123",
}

print("=== PASSWORD RESET ===\n")
for username, new_password in resets.items():
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        try:
            role = user.userprofile.role
        except:
            role = "admin/superuser"
        print(f"  {username:20s} | password: {new_password:15s} | role: {role}")
    except User.DoesNotExist:
        print(f"  {username:20s} | NOT FOUND")

print("\nDone.")
