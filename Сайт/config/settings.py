import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file():
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value and not os.environ.get(key):
            os.environ[key] = value


load_env_file()

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-local-development-only")
DEBUG = os.getenv("DEBUG", "True").lower() in {"1", "true", "yes", "on"}
APP_HOST = os.getenv("APP_HOST", "islombek77vip.pythonanywhere.com")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", f"{APP_HOST},127.0.0.1,localhost").split(",")
    if host.strip()
]

# Required for PythonAnywhere / HTTPS proxy deployments. Without this, Google OAuth
# callback requests can be rejected during the CSRF/redirect round trip.
csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS", "").strip()
if csrf_origins:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins.split(",") if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        f"https://{APP_HOST}",
        f"https://www.{APP_HOST}",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SITE_ID = 1

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.telegram",
    "store",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "store.context_processors.social_auth",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
# Directory where collectstatic will collect static files for production
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
LOGIN_REDIRECT_URL = "/"
SOCIALACCOUNT_ADAPTER = "store.adapters.StoreSocialAccountAdapter"
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "OAUTH_PKCE_ENABLED": True,
    },
    "telegram": {
        "APP": {
            "client_id": os.getenv("TELEGRAM_BOT_ID", ""),
            "secret": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "key": "",
        },
    },
}

JAZZMIN_SETTINGS = {
    "site_title": "Apple Store Admin",
    "site_header": "Apple Store",
    "site_brand": "Apple Store",
    "welcome_sign": "Mahsulotlar boshqaruv paneli",
    "copyright": "Apple Store",
    "search_model": ["store.Product", "store.Category", "store.Profile"],
    "order_with_respect_to": ["store", "auth"],
    "icons": {
        "store": "fas fa-boxes-stacked",
        "store.category": "fas fa-layer-group",
        "store.product": "fas fa-mobile-screen-button",
        "store.profile": "fas fa-user-check",
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
    },
    "show_ui_builder": True,
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "default_theme_mode": "light",
    "navbar_small_text": False,
    "footer_small_text": False,
    "sidebar_nav_small_text": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "accent": "primary",
}

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND") or (
    "django.core.mail.backends.smtp.EmailBackend"
    if os.getenv("EMAIL_HOST_USER") and os.getenv("EMAIL_HOST_PASSWORD")
    else "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Apple Store <noreply@local.test>")
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in {"1", "true", "yes", "on"}
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
