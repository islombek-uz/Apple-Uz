from django.conf import settings


def social_auth(request):
    providers = settings.SOCIALACCOUNT_PROVIDERS
    google = providers.get("google", {}).get("APP", {})
    telegram = providers.get("telegram", {}).get("APP", {})
    return {
        "social_auth": {
            "google": bool(google["client_id"] and google["secret"]),
            "telegram": bool(telegram.get("client_id") and telegram.get("secret")),
        }
    }