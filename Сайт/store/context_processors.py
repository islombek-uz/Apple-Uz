from django.conf import settings


def social_auth(request):
    providers = settings.SOCIALACCOUNT_PROVIDERS
    google = providers["google"]["APP"]
    telegram = providers["telegram"]["APP"]
    return {
        "social_auth": {
            "google": bool(google["client_id"] and google["secret"]),
            "telegram": bool(telegram["client_id"] and telegram["secret"]),
        }
    }