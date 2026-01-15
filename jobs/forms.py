from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        # employer & posted_at are set automatically, so we exclude them
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
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
        }