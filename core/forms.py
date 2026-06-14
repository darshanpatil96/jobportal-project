from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import UserProfile, Job, Application, Interview
from core.hiring.pipeline import PipelineService


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
                defaults={"role": role, "email_verified": True},
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
    required_skills_text = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Python, Django, React (comma-separated)",
            }
        ),
        label="Required skills (optional)",
        help_text="Used by AI matching. Leave blank to auto-detect from description.",
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.required_skills:
            self.fields["required_skills_text"].initial = ", ".join(
                self.instance.required_skills
            )

    def save(self, commit=True):
        job = super().save(commit=False)
        skills_text = self.cleaned_data.get("required_skills_text", "")
        job.required_skills = [
            s.strip() for s in skills_text.split(",") if s.strip()
        ]
        if commit:
            job.save()
        return job


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


class ApplicationStatusForm(forms.Form):
    application_id = forms.IntegerField(widget=forms.HiddenInput)
    status = forms.ChoiceField(choices=Application.STATUS_CHOICES)
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
    )

    def __init__(self, *args, application=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = application
        if application:
            allowed = PipelineService.get_allowed_next_statuses(application.status)
            allowed.add(application.status)
            self.fields["status"].choices = [
                (s, s) for s in Application.STATUS_CHOICES if s[0] in allowed
            ]

    def clean_status(self):
        status = self.cleaned_data["status"]
        if self.application:
            current = Application.normalize_status(self.application.status)
            new = Application.normalize_status(status)
            if current != new and not PipelineService.can_transition(current, new):
                raise ValidationError(
                    f"Cannot move from {current} to {new}."
                )
        return status


class InterviewScheduleForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = [
            "scheduled_time",
            "interview_type",
            "meeting_link",
            "notes",
        ]
        widgets = {
            "scheduled_time": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
            ),
            "interview_type": forms.Select(attrs={"class": "form-control"}),
            "meeting_link": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://meet.google.com/..."}
            ),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_scheduled_time(self):
        scheduled_time = self.cleaned_data["scheduled_time"]
        if scheduled_time <= timezone.now():
            raise ValidationError("Interview must be scheduled in the future.")
        return scheduled_time


class InterviewStatusForm(forms.Form):
    interview_id = forms.IntegerField(widget=forms.HiddenInput)
    status = forms.ChoiceField(choices=Interview.STATUS_CHOICES)
