from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    ROLE_CHOICES = UserProfile.ROLE_CHOICES  # ('jobseeker', 'Job Seeker'), ('employer', 'Employer')

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial="jobseeker",
        label="I am a",
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def save(self, commit=True):
        user = super().save(commit=commit)
        role = self.cleaned_data.get("role", "jobseeker")

        if commit:
            # create or update profile with chosen role
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"role": role},
            )

        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'role',
            'full_name',
            'phone',
            'location',
            'resume',
            'company_name',
            'company_website',
            'company_logo',
            'company_description',
        ]
        widgets = {
            'resume': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx'}),
            'company_logo': forms.FileInput(attrs={'accept': 'image/*'}),
        }
