from django.conf import settings


def social_auth(request):
    providers = settings.SOCIALACCOUNT_PROVIDERS
    google = providers["google"]["APP"]
    return {
        "social_auth": {
            "google": bool(google["client_id"] and google["secret"]),
            "telegram": False,
        }
    }