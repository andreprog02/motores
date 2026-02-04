from django.apps import AppConfig

class MaintenanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.maintenance'

    def ready(self):
        import src.apps.maintenance.signals