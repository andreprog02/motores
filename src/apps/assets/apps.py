from django.apps import AppConfig

class AssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.assets'  # Caminho completo
    label = 'assets'

    def ready(self):
        # Isso ativa a automação (Signals) quando o app inicia
        import src.apps.assets.signals