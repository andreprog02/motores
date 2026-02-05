from django.apps import AppConfig

class MaintenanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.maintenance'
    verbose_name = "Manutenção e Ocorrências"

    def ready(self):
        # Esta linha é OBRIGATÓRIA para o sinal funcionar
        import src.apps.maintenance.signals