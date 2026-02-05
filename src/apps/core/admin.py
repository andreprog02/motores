from django.contrib import admin
from .models import Tenant, User

# 1. Registra os modelos básicos
admin.site.register(Tenant)
admin.site.register(User)

# 2. A Classe Mágica (TenantModelAdmin) - VERSÃO CORRIGIDA
class TenantModelAdmin(admin.ModelAdmin):
    """
    Classe base para todos os Admins do sistema.
    Esconde o tenant e preenche automaticamente (Pai e Filhos).
    """
    exclude = ['tenant'] # Esconde o campo da tela

    # Salva o Pai (ex: Motor, Componente)
    def save_model(self, request, obj, form, change):
        # Se o objeto não tem empresa, tenta pegar do usuário
        if not obj.tenant_id:
            if request.user.tenant_id:
                obj.tenant_id = request.user.tenant_id
        super().save_model(request, obj, form, change)

    # Salva os Filhos (ex: Preventivas, Itens Inline)
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        
        # Pega o objeto pai que está sendo editado (O Componente)
        parent_obj = form.instance
        
        for instance in instances:
            # Se o registro filho (preventiva) não tem tenant_id...
            if hasattr(instance, 'tenant_id') and not instance.tenant_id:
                
                # ESTRATÉGIA BLINDADA:
                # 1. Copia o ID direto do Pai (É garantido que o componente tem dono)
                if hasattr(parent_obj, 'tenant_id') and parent_obj.tenant_id:
                    instance.tenant_id = parent_obj.tenant_id
                
                # 2. Se falhar (ex: criando pai e filho juntos), tenta do Usuário
                elif request.user.tenant_id:
                    instance.tenant_id = request.user.tenant_id
            
            instance.save()
        formset.save_m2m()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Se for superusuário sem tenant, vê tudo
        if request.user.is_superuser and not request.user.tenant_id:
            return qs
        # Senão, vê apenas da sua empresa
        return qs.filter(tenant_id=request.user.tenant_id)