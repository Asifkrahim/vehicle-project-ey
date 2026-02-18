from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-x195(*%@m7f%t9k^c%_lxmobnjn6+c)=*y4z!sk%#5%g8jn^$2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['.vercel.app', '127.0.0.1', 'localhost']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'vehiclecareapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'vehiclecareproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Add this so Django looks for templates in app folders
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'vehiclecareproject.wsgi.application'

# Database
# Default to SQLite (for your local computer)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# If running on Vercel, overwrite with the online database
database_url = os.environ.get("DATABASE_URL")
if database_url:
    DATABASES["default"] = dj_database_url.parse(database_url)

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # optional if you have project-level static folder
]
STATIC_ROOT = BASE_DIR / 'staticfiles'  # for collectstatic in production

# Media files (optional, if you later upload PDFs, images, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==========================================
# 📧 EMAIL CONFIGURATION (GMAIL SMTP)
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# 👇 REPLACE THESE WITH YOUR REAL DETAILS 👇
EMAIL_HOST_USER = 'asifkr664@gmail.com'   # <--- Put your REAL Gmail here
EMAIL_HOST_PASSWORD = 'gprv ogxh dodt qupr'     # <--- Put your 16-char APP PASSWORD here (NOT your login password)