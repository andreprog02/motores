#!/usr/bin/env python
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.settings.base')

    # --- A CORREÇÃO SÊNIOR ---
    # Isso diz ao Python: "Adicione a pasta raiz do projeto (motores) ao seu caminho de busca".
    # Assim, ele consegue encontrar o módulo 'src' sem dar erro.
    current_path = Path(__file__).resolve().parent
    sys.path.append(str(current_path.parent))
    # -------------------------

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()

if __name__ == '__main__':
    main()