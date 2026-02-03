import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Adiciona a raiz do projeto ao Python Path (igual fizemos no manage.py)
# Isso garante que ele encontre o módulo 'src'
current_path = Path(__file__).resolve().parent
sys.path.append(str(current_path.parent.parent))

# Aponta para o arquivo de configurações correto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.settings.base')

application = get_wsgi_application()