from pathlib import Path
import environ
import os

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')

ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
ANTHROPIC_DEFAULT_MODEL = 'claude-sonnet-4-6'

GOOGLE_MAPS_API_KEY = env('GOOGLE_MAPS_API_KEY', default='')

DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'content',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'content.context_processors.inbox_pending_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database — use DATABASE_URL (Neon) only in production; always use local DB_* vars in dev
if env('DATABASE_URL', default=None) and not DEBUG:
    DATABASES = {'default': env.db('DATABASE_URL')}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('DB_NAME'),
            'USER': env('DB_USER'),
            'PASSWORD': env('DB_PASSWORD'),
            'HOST': env('DB_HOST'),
            'PORT': env('DB_PORT'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files — use Cloudflare R2 when configured, local filesystem for dev
_r2_bucket = env('CLOUDFLARE_R2_BUCKET_NAME', default='')
if _r2_bucket and not DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = _r2_bucket
    AWS_S3_ENDPOINT_URL = env('CLOUDFLARE_R2_ENDPOINT_URL', default='')
    AWS_ACCESS_KEY_ID = env('CLOUDFLARE_R2_ACCESS_KEY_ID', default='')
    AWS_SECRET_ACCESS_KEY = env('CLOUDFLARE_R2_SECRET_ACCESS_KEY', default='')
    AWS_S3_CUSTOM_DOMAIN = env('CLOUDFLARE_R2_CUSTOM_DOMAIN', default='')
    AWS_QUERYSTRING_AUTH = False  # Use public URLs, not presigned URLs
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/' if AWS_S3_CUSTOM_DOMAIN else f'{AWS_S3_ENDPOINT_URL}/{_r2_bucket}/'
else:
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Allow larger request bodies to accommodate base64-encoded dish images in review submission
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20 MB

# HTTPS security settings — enable in production via USE_HTTPS=true env var
if env.bool('USE_HTTPS', default=False):
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year

# Confluence API settings
CONFLUENCE_EMAIL = env('CONFLUENCE_EMAIL', default=None)
CONFLUENCE_API_TOKEN = env('CONFLUENCE_API_TOKEN', default=None)
CONFLUENCE_SITE_URL = env('CONFLUENCE_SITE_URL', default='https://gavinlu.atlassian.net')
