from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import get_profile_for_user


class StoreSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        get_profile_for_user(user)
        return user