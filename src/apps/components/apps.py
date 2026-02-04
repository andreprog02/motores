from django.apps import AppConfig

class ComponentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.components'
    verbose_name = '2. Gestão de Componentes' # Nome da Nova Raiz no Menu

    def ready(self):
        # Importa os sinais para criar peças automaticamente
        import src.apps.components.signals