from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv
from datetime import timedelta



BASE_DIR=Path(__file__).resolve().parent.parent
load_dotenv()
# ------------------------------------------------------
# SECURITY
# ------------------------------------------------------
SECRET_KEY=os.environ.get("SECRET_KEY","dev-secret-key")

DEBUG=os.environ.get("DEBUG","True")=="True"

ALLOWED_HOSTS=os.environ.get(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost"
).split(",")

RENDER_EXTERNAL_HOSTNAME=os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

if not DEBUG:
    CSRF_COOKIE_SECURE=True
    SESSION_COOKIE_SECURE=True
    SECURE_SSL_REDIRECT=True
    SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")
    SECURE_HSTS_SECONDS=2592000
    SECURE_HSTS_INCLUDE_SUBDOMAINS=True
    SECURE_HSTS_PRELOAD=True


# ------------------------------------------------------
# INSTALLED APPS
# ------------------------------------------------------
INSTALLED_APPS=[
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",

    "authapp",
    "contactapp",

    "doctor_personal_details",
    "doctor_certification",
    "doctor_documents",
    "doctor_bank_details",

    "trainers_personal_detials",
    "trainers_certifications",
    "trainers_documents",
    "trainers_bank_details",

    "admin_auth",

    "manager_personal_details",
    "manager_documents",
    "manager_bank_details",
]


# ------------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------------
MIDDLEWARE=[
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF="Atmayantra.urls"


# ------------------------------------------------------
# TEMPLATES
# ------------------------------------------------------
TEMPLATES=[
    {
        "BACKEND":"django.template.backends.django.DjangoTemplates",
        "DIRS":[],
        "APP_DIRS":True,
        "OPTIONS":{
            "context_processors":[
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION="Atmayantra.wsgi.application"


# ------------------------------------------------------
# DATABASE
# ------------------------------------------------------
DATABASES={
    "default":dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# ------------------------------------------------------
# CACHE
# ------------------------------------------------------
if os.environ.get("REDIS_URL"):
    CACHES={
        "default":{
            "BACKEND":"django_redis.cache.RedisCache",
            "LOCATION":os.environ.get("REDIS_URL"),
            "OPTIONS":{"CLIENT_CLASS":"django_redis.client.DefaultClient"},
        }
    }
else:
    CACHES={
        "default":{
            "BACKEND":"django.core.cache.backends.locmem.LocMemCache",
            "LOCATION":"atmayantra-local-cache",
        }
    }


# ------------------------------------------------------
# PASSWORD VALIDATION
# ------------------------------------------------------
AUTH_PASSWORD_VALIDATORS=[
    {"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ------------------------------------------------------
# INTERNATIONAL
# ------------------------------------------------------
LANGUAGE_CODE="en-us"
TIME_ZONE="UTC"
USE_I18N=True
USE_TZ=True


# ------------------------------------------------------
# STATIC + MEDIA
# ------------------------------------------------------
STATIC_URL="/static/"
STATIC_ROOT=BASE_DIR / "staticfiles"
STATICFILES_STORAGE="whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL="/media/"
MEDIA_ROOT=BASE_DIR / "media"


# ------------------------------------------------------
# CUSTOM USER
# ------------------------------------------------------
AUTH_USER_MODEL="authapp.User"


# ------------------------------------------------------
# DRF
# ------------------------------------------------------
REST_FRAMEWORK={
    "DEFAULT_AUTHENTICATION_CLASSES":(
        "admin_auth.authentication.AdminJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PARSER_CLASSES":(
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
}


# ------------------------------------------------------
# SIMPLE JWT (For NORMAL USERS only)
# ------------------------------------------------------
SIMPLE_JWT={
    "ACCESS_TOKEN_LIFETIME":timedelta(
        minutes=int(os.environ.get("SIMPLE_JWT_ACCESS_MINUTES",30))
    ),
    "REFRESH_TOKEN_LIFETIME":timedelta(
        days=int(os.environ.get("SIMPLE_JWT_REFRESH_DAYS",7))
    ),
}


# ------------------------------------------------------
# OTP CONFIG (ADMIN AUTH)
# ------------------------------------------------------
OTP_EXPIRY_MINUTES=int(
    os.environ.get("OTP_EXPIRY_MINUTES",15)
)


# ------------------------------------------------------
# ADMIN MANUAL JWT CONFIG
# ------------------------------------------------------
JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY",SECRET_KEY)

JWT_ALGORITHM=os.environ.get("JWT_ALGORITHM","HS256")

JWT_ACCESS_TOKEN_LIFETIME_MINUTES=int(
    os.environ.get("JWT_ACCESS_TOKEN_LIFETIME_MINUTES",30)
)

JWT_REFRESH_TOKEN_LIFETIME_DAYS=int(
    os.environ.get("JWT_REFRESH_TOKEN_LIFETIME_DAYS",7)
)


# ------------------------------------------------------
# EMAIL (SMTP FOR MANAGER CREDENTIALS)
# ------------------------------------------------------
EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST=os.environ.get("EMAIL_HOST")
EMAIL_PORT=int(os.environ.get("EMAIL_PORT",587))
EMAIL_USE_TLS=os.environ.get("EMAIL_USE_TLS","True")=="True"

EMAIL_HOST_USER=os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD=os.environ.get("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL=os.environ.get("DEFAULT_FROM_EMAIL")


# ------------------------------------------------------
# LOGGING
# ------------------------------------------------------
LOGGING={
    "version":1,
    "disable_existing_loggers":False,
    "handlers":{"console":{"class":"logging.StreamHandler"}},
    "root":{"handlers":["console"],"level":"INFO"},
}


# ------------------------------------------------------
# CORS
# ------------------------------------------------------
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS=True
else:
    allowed_origins=os.environ.get("CORS_ALLOWED_ORIGINS","")
    CORS_ALLOWED_ORIGINS=allowed_origins.split(",") if allowed_origins else []

    CORS_ALLOWED_ORIGINS.extend([
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ])
