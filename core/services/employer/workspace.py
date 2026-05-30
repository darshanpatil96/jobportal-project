"""
Workspace management services.

Handles workspace creation, member management, and isolation logic.
"""

import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from core.models import CompanyWorkspace, UserProfile, WorkspaceInvitation, WorkspaceMember


class WorkspaceService:
    """Create and manage company workspaces."""

    @classmethod
    @transaction.atomic
    def create_workspace(cls, owner, name, **kwargs):
        """
        Create a new workspace and add the owner as the first member.

        Called during employer registration or when an existing employer
        sets up their company workspace for the first time.
        """
        workspace = CompanyWorkspace.objects.create(
            owner=owner,
            name=name,
            description=kwargs.get("description", ""),
            website=kwargs.get("website", ""),
            headquarters=kwargs.get("headquarters", ""),
            industry=kwargs.get("industry", ""),
            company_size=kwargs.get("company_size", ""),
        )

        # Add owner as first member
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=owner,
            role="owner",
        )

        return workspace

    @classmethod
    def get_user_workspace(cls, user):
        """
        Get the primary workspace for a user.

        Returns the first active workspace membership, or None.
        For single-workspace users (most cases), this is their company.
        """
        membership = (
            WorkspaceMember.objects.filter(user=user, is_active=True)
            .select_related("workspace")
            .first()
        )
        return membership.workspace if membership else None

    @classmethod
    def get_user_workspaces(cls, user):
        """Get all workspaces a user belongs to."""
        return CompanyWorkspace.objects.filter(
            members__user=user, members__is_active=True
        ).distinct()

    @classmethod
    def get_workspace_member(cls, workspace, user):
        """Get the membership record for a user in a workspace."""
        try:
            return WorkspaceMember.objects.get(
                workspace=workspace, user=user, is_active=True
            )
        except WorkspaceMember.DoesNotExist:
            return None

    @classmethod
    @transaction.atomic
    def invite_member(cls, workspace, email, role, invited_by):
        """
        Create an invitation to join the workspace.

        Returns the invitation with a unique token for the invite link.
        """
        if workspace.members.filter(is_active=True).count() >= workspace.max_members:
            raise ValueError(
                f"Workspace has reached the maximum of {workspace.max_members} members. "
                f"Upgrade your plan to add more."
            )

        token = secrets.token_urlsafe(48)
        invitation = WorkspaceInvitation.objects.create(
            workspace=workspace,
            email=email,
            role=role,
            invited_by=invited_by,
            token=token,
            expires_at=timezone.now() + timedelta(days=7),
        )
        return invitation

    @classmethod
    @transaction.atomic
    def accept_invitation(cls, token, user):
        """Accept a workspace invitation and create membership."""
        try:
            invitation = WorkspaceInvitation.objects.get(
                token=token, status="pending"
            )
        except WorkspaceInvitation.DoesNotExist:
            raise ValueError("Invalid or expired invitation.")

        if invitation.is_expired:
            invitation.status = "expired"
            invitation.save(update_fields=["status"])
            raise ValueError("This invitation has expired.")

        # Create membership
        member, created = WorkspaceMember.objects.get_or_create(
            workspace=invitation.workspace,
            user=user,
            defaults={"role": invitation.role, "invited_by": invitation.invited_by},
        )

        if not created:
            member.is_active = True
            member.role = invitation.role
            member.save(update_fields=["is_active", "role"])

        invitation.status = "accepted"
        invitation.save(update_fields=["status"])

        # Ensure user has employer profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if profile.role != "employer":
            profile.role = "employer"
            profile.save(update_fields=["role"])

        return member

    @classmethod
    def auto_create_from_profile(cls, user_profile):
        """
        Auto-create a workspace from an existing employer UserProfile.

        Used during migration to give existing employers a workspace
        without requiring them to re-register.
        """
        if not user_profile.company_name:
            return None

        # Check if workspace already exists for this user
        existing = cls.get_user_workspace(user_profile.user)
        if existing:
            return existing

        workspace = cls.create_workspace(
            owner=user_profile.user,
            name=user_profile.company_name,
            website=user_profile.company_website or "",
            description=user_profile.company_description or "",
        )

        # Copy logo if exists
        if user_profile.company_logo:
            workspace.logo = user_profile.company_logo
            workspace.save(update_fields=["logo"])

        return workspace
