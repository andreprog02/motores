from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin
from .models import (
    CategoriaPeca, CatalogoPeca, EstoqueItem, 
    MovimentoEstoque, SerialPeca, Fabricante, LocalEstoque
)

@admin.register(Fabricante)
class FabricanteAdmin(TenantModelAdmin):
    list_display = ('nome', 'principal', 'site')
    list_filter = ('principal',)
    search_fields = ('nome',)

@admin.register(CategoriaPeca)
class CategoriaPecaAdmin(TenantModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(LocalEstoque)
class LocalEstoqueAdmin(TenantModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(CatalogoPeca)
class CatalogoAdmin(TenantModelAdmin):
    list_display = ('nome', 'fabricante', 'codigo_fabricante', 'categoria', 'exibir_modelos')
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

    @admin.display(description="Modelos Compatíveis")
    def exibir_modelos(self, obj):
        """Exibe lista de modelos ou 'UNIVERSAL' na listagem"""
        if obj.aplicacao_universal:
            return "UNIVERSAL (Todos)"
        
        # Pega os primeiros 5 modelos para não poluir a tela
        modelos = [str(m) for m in obj.modelos_compativeis.all()[:5]]
        count = obj.modelos_compativeis.count()
        
        if not modelos:
            return "-"
        
        texto = ", ".join(modelos)
        if count > 5:
            texto += f" ... (+{count - 5})"
        return texto

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
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

@admin.register(SerialPeca)
class SerialPecaAdmin(TenantModelAdmin):
    list_display = ('serial_number', 'item_estoque', 'data_entrada')
    search_fields = ('serial_number', 'item_estoque__catalogo__nome')
    list_filter = ('data_entrada',)

@admin.register(EstoqueItem)
class EstoqueAdmin(TenantModelAdmin):
    # ADICIONADO: 'get_categoria' e 'get_modelos' na lista
    list_display = (
        'catalogo', 
        'get_categoria', 
        'quantidade', 
        'local', 
        'get_modelos',  
        'contar_seriais'
    )
    list_filter = ('local', 'catalogo__categoria') # Adicionei filtro por categoria também
    search_fields = ('catalogo__nome', 'catalogo__codigo_fabricante')
    autocomplete_fields = ['catalogo']
    inlines = [SerialInline]

    @admin.display(description="Categoria", ordering='catalogo__categoria')
    def get_categoria(self, obj):
        return obj.catalogo.categoria

    @admin.display(description="Modelos Compatíveis")
    def get_modelos(self, obj):
        # Acessa o catálogo vinculado a este item de estoque
        catalogo = obj.catalogo
        
        if catalogo.aplicacao_universal:
            return "UNIVERSAL"
        
        # Reutiliza a lógica de limitar a exibição para não quebrar o layout
        modelos = [str(m) for m in catalogo.modelos_compativeis.all()[:3]]
        if not modelos:
            return "-"
            
        texto = ", ".join(modelos)
        if catalogo.modelos_compativeis.count() > 3:
            texto += "..."
        return texto

    @admin.display(description="Qtd. Seriais")
    def contar_seriais(self, obj):
        return f"{obj.seriais.count()}"

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if hasattr(instance, 'tenant_id') and not instance.tenant_id:
                instance.tenant = request.user.tenant
            instance.save()
        formset.save_m2m()

@admin.register(MovimentoEstoque)
class MovimentoAdmin(TenantModelAdmin):
    list_display = ('data_movimento', 'tipo', 'item', 'quantidade', 'origem')
    list_filter = ('tipo', 'data_movimento')
    search_fields = ('item__catalogo__nome', 'origem')