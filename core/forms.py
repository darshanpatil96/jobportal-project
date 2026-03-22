from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Job, Application


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial="jobseeker",
        label="I am a",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "role"]

    def save(self, commit=True):
        user = super().save(commit=commit)
        role = self.cleaned_data.get("role", "jobseeker")
        if commit:
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"role": role},
            )
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "role",
            "full_name",
            "phone",
            "location",
            "resume",
            "company_name",
            "company_website",
            "company_logo",
            "company_description",
        ]
        widgets = {
            "resume": forms.FileInput(attrs={"accept": ".pdf,.doc,.docx"}),
            "company_logo": forms.FileInput(attrs={"accept": "image/*"}),
        }


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            "title",
            "company",
            "location",
            "salary",
            "category",
            "job_type",
            "description",
            "status",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "company": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "salary": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "job_type": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["qualification", "phone", "experience", "resume", "cover_letter"]
        widgets = {
            "qualification": forms.TextInput(
                attrs={
                    "class": "rounded-lg border border-slate-200 px-3 py-2 w-full",
                    "placeholder": "e.g. B.Tech in Computer Science",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "rounded-lg border border-slate-200 px-3 py-2 w-full",
                    "placeholder": "+1 555 123 4567",
                    "inputmode": "tel",
                }
            ),
            "experience": forms.TextInput(
                attrs={
                    "class": "rounded-lg border border-slate-200 px-3 py-2 w-full",
                    "placeholder": "e.g. 3 years in React",
                }
            ),
            "cover_letter": forms.Textarea(
                attrs={
                    "class": "rounded-lg border border-slate-200 px-3 py-2 w-full",
                    "rows": 6,
                    "placeholder": "Write a short note to the employer",
                }
            ),
            "resume": forms.ClearableFileInput(
                attrs={
                    "class": "block w-full text-sm text-slate-700",
                    "accept": ".pdf,.doc,.docx",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["qualification"].required = True
        self.fields["phone"].required = True
