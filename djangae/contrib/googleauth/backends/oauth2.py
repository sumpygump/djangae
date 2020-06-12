from django.contrib.auth import get_user_model
from .base import BaseBackend


UserModel = get_user_model()


class OAuthBackend(BaseBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

    def authenticate(self, request, **kwargs):
        username = kwargs['email']
        email = kwargs['email']
        user, created = UserModel._default_manager.get_or_create(
                username=username, defaults={
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
            user = UserModel._default_manager.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
