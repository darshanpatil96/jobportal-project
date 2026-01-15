from django import forms
from .models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = [
            "qualification",
            "phone",
            "experience",
            "resume",
            "cover_letter",
        ]
        widgets = {
            "qualification": forms.TextInput(attrs={"class": "rounded-lg border border-slate-200 px-3 py-2 w-full", "placeholder": "e.g. B.Tech in Computer Science"}),
            "phone": forms.TextInput(attrs={"class": "rounded-lg border border-slate-200 px-3 py-2 w-full", "placeholder": "+1 555 123 4567", "inputmode": "tel"}),
            "experience": forms.TextInput(attrs={"class": "rounded-lg border border-slate-200 px-3 py-2 w-full", "placeholder": "e.g. 3 years in React"}),
            "cover_letter": forms.Textarea(attrs={"class": "rounded-lg border border-slate-200 px-3 py-2 w-full", "rows": 6, "placeholder": "Write a short note to the employer"}),
            "resume": forms.ClearableFileInput(attrs={"class": "block w-full text-sm text-slate-700", "accept": ".pdf,.doc,.docx"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make key fields mandatory at the form level
        self.fields["qualification"].required = True
        self.fields["phone"].required = True
        # If you also want the resume to be mandatory, uncomment the next line:
        # self.fields["resume"].required = True
