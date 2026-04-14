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
AWS_APP_RUNNER_HOSTNAME=os.environ.get("AWS_APP_RUNNER_HOSTNAME")
EC2_PUBLIC_IP=os.environ.get("EC2_PUBLIC_IP")

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

if AWS_APP_RUNNER_HOSTNAME:
    ALLOWED_HOSTS.append(AWS_APP_RUNNER_HOSTNAME)

if EC2_PUBLIC_IP:
    ALLOWED_HOSTS.append(EC2_PUBLIC_IP)

# ------------------------------------------------------
# CSRF + SECURITY
# ------------------------------------------------------
CSRF_TRUSTED_ORIGINS=[]
trusted_origins_env=os.environ.get("CSRF_TRUSTED_ORIGINS","")
if trusted_origins_env:
    CSRF_TRUSTED_ORIGINS.extend(trusted_origins_env.split(","))

if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

if AWS_APP_RUNNER_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{AWS_APP_RUNNER_HOSTNAME}")

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
db_url=os.environ.get("DATABASE_URL")
if db_url and "amazonaws.com" in db_url:
    # RDS specific configuration with SSL
    DATABASES={
        "default":dj_database_url.config(
            default=db_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
elif db_url:
    # Local PostgreSQL or any other database URL
    DATABASES={
        "default":dj_database_url.config(
            default=db_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Fallback to SQLite (only when DATABASE_URL is not set)
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
elif os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    # Render fallback: Persistent Database Cache (FileBasedCache is unstable on Render)
    CACHES={
        "default":{
            "BACKEND":"django.core.cache.backends.db.DatabaseCache",
            "LOCATION":"atmayantra_cache_table",
        }
    }
else:
    # Local fallback
    CACHES={
        "default":{
            "BACKEND":"django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION":os.path.join(BASE_DIR, "django_cache"),
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
# AWS S3 STORAGE (PRODUCTION)
# ------------------------------------------------------
AWS_ACCESS_KEY_ID=os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME=os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME=os.environ.get("AWS_S3_REGION_NAME","us-east-1")

if all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_STORAGE_BUCKET_NAME]):
    DEFAULT_FILE_STORAGE="storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_FILE_OVERWRITE=False
    AWS_DEFAULT_ACL=None
    AWS_S3_VERIFY=True
    # Custom URL for S3 if using CloudFront or specific domain
    AWS_S3_CUSTOM_DOMAIN=os.environ.get("AWS_S3_CUSTOM_DOMAIN")
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL=f"https://{AWS_S3_CUSTOM_DOMAIN}/"


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

SIGNUP_TOKEN_LIFETIME_MINUTES=int(
    os.environ.get("SIGNUP_TOKEN_LIFETIME_MINUTES",30)
)


# ------------------------------------------------------
# EMAIL (SMTP FOR MANAGER CREDENTIALS)
# ------------------------------------------------------
AWS_SES_ACCESS_KEY_ID=os.environ.get("AWS_SES_ACCESS_KEY_ID")
AWS_SES_SECRET_ACCESS_KEY=os.environ.get("AWS_SES_SECRET_ACCESS_KEY")
AWS_SES_REGION_NAME=os.environ.get("AWS_SES_REGION_NAME","us-east-1")

if all([AWS_SES_ACCESS_KEY_ID, AWS_SES_SECRET_ACCESS_KEY]):
    # Use AWS SES
    EMAIL_BACKEND="django_ses.SESBackend"
    AWS_SES_ACCESS_KEY_ID=AWS_SES_ACCESS_KEY_ID
    AWS_SES_SECRET_ACCESS_KEY=AWS_SES_SECRET_ACCESS_KEY
    AWS_SES_REGION_NAME=AWS_SES_REGION_NAME
else:
    # Fallback to standard SMTP (Local/Gmail)
    EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST=os.environ.get("EMAIL_HOST","smtp.gmail.com")
EMAIL_PORT=int(os.environ.get("EMAIL_PORT",587))
EMAIL_USE_TLS=os.environ.get("EMAIL_USE_TLS","True")=="True"
EMAIL_USE_SSL=os.environ.get("EMAIL_USE_SSL","False")=="True"

# Safety: TLS and SSL are mutually exclusive
if EMAIL_USE_SSL:
    EMAIL_USE_TLS=False

EMAIL_HOST_USER=os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD=os.environ.get("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL=os.environ.get("DEFAULT_FROM_EMAIL")

EMAIL_TIMEOUT=int(os.environ.get("EMAIL_TIMEOUT",30))


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
