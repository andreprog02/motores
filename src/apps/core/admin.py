from django.contrib import admin
from .models import Tenant, User

# 1. Registra os modelos básicos
admin.site.register(Tenant)
admin.site.register(User)

# 2. A Classe Mágica (O erro acontece porque esta classe está faltando)
class TenantModelAdmin(admin.ModelAdmin):
    """
    Classe base para todos os Admins do sistema.
    Esconde o tenant e preenche automaticamente.
    """
    exclude = ['tenant'] # Esconde o campo da tela

    def save_model(self, request, obj, form, change):
        # Se não tem tenant, usa o do usuário logado
        if not obj.tenant_id:
            obj.tenant = request.user.tenant
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        # Filtra para ver apenas coisas da sua empresa
        qs = super().get_queryset(request)
        if request.user.is_superuser and not request.user.tenant:
            return qs
        return qs.filter(tenant=request.user.tenant)