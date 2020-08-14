import logging

from django.contrib.auth import get_user_model
from django.db.models import Q

from djangae.contrib.googleauth.models import UserManager
from gcloudc.db import transaction

from .base import BaseBackend

User = get_user_model()


class IAPBackend(BaseBackend):

    @classmethod
    def can_authenticate(cls, request):
        return "HTTP_X_GOOG_AUTHENTICATED_USER_ID" in request.META and \
            "HTTP_X_GOOG_AUTHENTICATED_USER_EMAIL" in request.META

    def authenticate(self, request, **kwargs):
        user_id = request.META.get("HTTP_X_GOOG_AUTHENTICATED_USER_ID")
        email = request.META.get("HTTP_X_GOOG_AUTHENTICATED_USER_EMAIL")

        # User not logged in to IAP
        if not user_id or not email:
            return

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            logging.warning("Invalid IAP user id: %s", user_id)
            return

        email = UserManager.normalize_email(email)
        assert email

        with transaction.atomic():
            # Look for a user, either by ID, or email
            user = User.objects.filter(
                Q(google_iap_id=user_id) | Q(email=email)
            ).first()

            if user:
                # So we previously had a user sign in by email, but not
                # via IAP, so we should set that ID
                if not user.google_iap_id:
                    user.google_iap_id = user_id
                else:
                    assert(user.google_iap_id == user_id)
                    # We got the user by google_iap_id, but their email
                    # might have changed (maybe), so update that just in case
                    user.email = email
                user.save()
            else:
                # First time we've seen this user
                user = User.objects.create(
                    google_iap_id=user_id,
                    email=email
                )

        return user
