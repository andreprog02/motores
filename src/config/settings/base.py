from pathlib import Path
import environ
import os

# 1. Configuração de Caminhos (Paths)
# Como estamos em src/config/settings/base.py, precisamos voltar 3 níveis para chegar na raiz
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# 2. Leitura do .env
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# 3. Aplicações Instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Nossos Apps (Domínio)
    'src.apps.core',
    'src.apps.inventory',
    'src.apps.assets',
    'src.apps.maintenance',
    'src.apps.dashboard',
    'src.apps.components',
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

ROOT_URLCONF = 'src.config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'src/apps/dashboard/templates'], # Aponta para nossa pasta de templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'src.config.wsgi.application'

# 4. Banco de Dados (Supabase)
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# 5. Configuração de Autenticação (CRUCIAL)
# Aponta para o model que criaremos no próximo passo
AUTH_USER_MODEL = 'core.User' 

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

USE_THOUSAND_SEPARATOR = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'src/apps/dashboard/static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'