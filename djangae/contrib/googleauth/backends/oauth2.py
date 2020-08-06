from .base import BaseBackend

from ..models import (
    Group,
    User,
    UserPermission,
    UserManager
)


class OAuthBackend(BaseBackend):
    def authenticate(self, request, **kwargs):
        oauth_session = kwargs.get("oauth_session")

        if (not oauth_session) or (not oauth_session.is_valid):
            return

        # FIXME: Refresh the token if it's close to expiry?

        profile = oauth_session.profile

        # We use the oauth_session ID as the username
        username = oauth_session.pk

        email = UserManager.normalize_email(profile["email"])
        assert email

        user, created = User.objects.update_or_create(
            username=username,
            defaults={
                'email': email,
            }
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
