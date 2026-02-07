from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin
from .models import CategoriaPeca, CatalogoPeca, EstoqueItem, MovimentoEstoque, SerialPeca, Fabricante

@admin.register(Fabricante)
class FabricanteAdmin(TenantModelAdmin):
    list_display = ('nome', 'principal', 'site')
    list_filter = ('principal',)
    search_fields = ('nome',)

@admin.register(CategoriaPeca)
class CategoriaPecaAdmin(TenantModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(CatalogoPeca)
class CatalogoAdmin(TenantModelAdmin):
    list_display = ('nome', 'fabricante', 'codigo_fabricante', 'categoria', 'aplicacao_universal')
    list_filter = ('categoria', 'fabricante', 'aplicacao_universal')
    search_fields = ('nome', 'codigo_fabricante', 'fabricante__nome')
    
    filter_horizontal = ('modelos_compativeis',)
    
    fieldsets = (
        ('Dados Principais', {
            'fields': ('nome', 'fabricante', 'codigo_fabricante', 'categoria')
        }),
        ('Compatibilidade', {
            'fields': ('aplicacao_universal', 'modelos_compativeis'),
            'description': 'Se marcar "Universal", a lista de modelos será ignorada.'
        }),
        ('Configurações Avançadas', {
            'fields': (
                'requer_serial_number', 'quantidade_por_jogo', 
                'vida_util_horas', 'vida_util_arranques', 'vida_util_meses', 
                'alerta_amarelo_pct'
            ),
            'classes': ('collapse',),
        }),
    )

    def get_changeform_initial_data(self, request):
        """
        Pré-seleciona o fabricante marcado como 'Principal' ao abrir o formulário de adição.
        """
        initial = super().get_changeform_initial_data(request)
        
        # Verifica se o usuário tem tenant vinculado
        if hasattr(request.user, 'tenant'):
            fabricante_padrao = Fabricante.objects.filter(
                tenant=request.user.tenant, 
                principal=True
            ).first()
            
            if fabricante_padrao:
                initial['fabricante'] = fabricante_padrao.pk
        
        return initial

# --- CONFIGURAÇÃO DOS SERIAIS ---
class SerialInline(admin.TabularInline):
    model = SerialPeca
    extra = 1
    fields = ('serial_number', 'data_entrada')
    readonly_fields = ('data_entrada',)
    verbose_name = "Serial Disponível"
    verbose_name_plural = "Seriais Vinculados a este Estoque"

@admin.register(EstoqueItem)
class EstoqueAdmin(TenantModelAdmin):
    list_display = ('catalogo', 'quantidade', 'contar_seriais', 'local', 'minimo_seguranca')
    list_filter = ('local',)
    search_fields = ('catalogo__nome', 'catalogo__codigo_fabricante')
    autocomplete_fields = ['catalogo']
    inlines = [SerialInline]

    @admin.display(description="Qtd. Seriais")
    def contar_seriais(self, obj):
        return f"{obj.seriais.count()}"

    # --- A CORREÇÃO ESTÁ AQUI ---
    # Esse método garante que os itens da tabela (Inlines) recebam o Tenant do usuário
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            # Se o item (Serial) não tiver tenant, preenche com o do usuário logado
            if hasattr(instance, 'tenant_id') and not instance.tenant_id:
                instance.tenant = request.user.tenant
            instance.save()
        formset.save_m2m()

@admin.register(MovimentoEstoque)
class MovimentoAdmin(TenantModelAdmin):
    list_display = ('data_movimento', 'tipo', 'item', 'quantidade', 'origem')
    list_filter = ('tipo', 'data_movimento')