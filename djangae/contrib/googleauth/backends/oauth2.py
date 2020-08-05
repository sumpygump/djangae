from .base import BaseBackend
from ..models import (
    Group,
    OAuthUserSession,
    User,
    UserPermission,
)


class OAuthBackend(BaseBackend):
    def authenticate(self, request, **kwargs):
        username = kwargs['email']
        email = kwargs['email']
        token = kwargs['token']

        user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                }
        )

        # something is wronk with update_or_create, need to fallback to manually doing it
        # oauth_user = OAuthUserSession.objects.update_or_create(user=user)
        defaults = {
            'access_token': token.get('access_token'),
            'expires_at': token.get('expires_at'),
            'expires_in': token.get('expires_in'),
            'id_token': token.get('id_token'),
            'refresh_token': token.get('refresh_token'),
            'scopes': token.get('scope'),
            'token_type': token.get('token_type'),
        }

        try:
            obj = OAuthUserSession.objects.get(user=user)
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.save()
        except OAuthUserSession.DoesNotExist:
            new_values = {'user': user}
            new_values.update(defaults)
            obj = OAuthUserSession(**new_values)
            obj.save()

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
