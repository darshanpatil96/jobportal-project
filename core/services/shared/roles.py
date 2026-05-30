"""
Role identification helpers.

Used across both candidate and employer views to determine user type.
These are intentionally simple — no DB queries beyond the cached userprofile.
"""


def is_employer(user):
    """Check if user has an employer profile."""
    return hasattr(user, "userprofile") and user.userprofile.role == "employer"


def is_jobseeker(user):
    """Check if user has a jobseeker profile."""
    return hasattr(user, "userprofile") and user.userprofile.role == "jobseeker"
