from django.apps import AppConfig

class ComponentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.components'

    def ready(self):
        # Isso é crucial! Sem isso, o código de automação não roda.
        import src.apps.components.signals