from django.db.models import Q

from gcloudc.db import transaction

from ..models import (
    Group,
    User,
    UserManager,
    UserPermission,
)
from .base import BaseBackend


class OAuthBackend(BaseBackend):
    def authenticate(self, request, **kwargs):
        oauth_session = kwargs.get("oauth_session")

        if (not oauth_session) or (not oauth_session.is_valid):
            return

        # FIXME: Refresh the token if it's close to expiry?

        profile = oauth_session.profile

        email = UserManager.normalize_email(profile["email"])
        assert email

        with transaction.atomic():
            # Look for a user, either by oauth ID, or email
            user = User.objects.filter(
                Q(google_oauth_id=oauth_session.pk) | Q(email=email)
            )

            # So we previously had a user sign in by email, but not
            # via OAuth, so let's update their user with their oauth
            # session ID
            if user:
                if not user.google_oauth_id:
                    user.google_oauth_id = oauth_session.pk
                else:
                    assert(user.google_oauth_id == oauth_session.pk)
                    # We got the user by google_oauth_id, but their email
                    # might have changed (maybe), so update that just in case
                    user.email = email
                user.save()
            else:
                # First time we've seen this user
                user = User.objects.create(
                    google_oauth_id=oauth_session.pk,
                    email=email
                )

        return user

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        is_active = getattr(user, 'is_active', None)
        return is_active or is_active is None

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None

    def get_user_permissions(self, user_obj, obj=None):
        qs = UserPermission.objects.filter(
            user_id=user_obj.pk
        ).values_list("permission", flat=True)

        if obj:
            qs = qs.filter(obj_id=obj.pk)

        return list(qs)

    def get_group_permissions(self, user_obj, obj=None):
        perms = set()
        qs = Group.objects.filter(users__contains=user_obj)
        for group in qs:
            perms.update(group.permissions)

        return list(perms)
