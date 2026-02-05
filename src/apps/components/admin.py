from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin 
from .models import (
    GrupoComponente, PosicaoComponente, 
    MenuOleo, MenuFiltros, MenuPerifericos, MenuIgnicao, 
    MenuCilindros, MenuCabecotes, MenuOutros, PlanoPreventiva
)

# --- 1. O INLINE (CORRIGIDO) ---
class PlanoPreventivaInline(admin.TabularInline):
    model = PlanoPreventiva
    extra = 1
    # CORREÇÃO CRÍTICA:
    # Removemos 'intervalo_horas' e 'intervalo_meses' (que não existem mais)
    # Adicionamos 'unidade' e 'intervalo_valor'
    fields = ('tarefa', 'tipo_servico', 'unidade', 'intervalo_valor')

# --- 2. BASE COMPARTILHADA ---
class ComponenteBaseAdmin(TenantModelAdmin): 
    # Colunas da tabela
    list_display = ('motor', 'nome', 'data_instalacao', 'horas_uso_atual', 'exibir_alertas')
    
    # Filtros e Busca
    list_filter = ('motor',)
    search_fields = ('nome', 'serial_number', 'motor__nome')
    autocomplete_fields = ['peca_instalada']
    
    inlines = [PlanoPreventivaInline] 
    
    def get_queryset(self, request):
        # Otimização para trazer as preventivas junto
        return super().get_queryset(request).prefetch_related('planos_preventiva')

    def exibir_alertas(self, obj):
        alertas = obj.status_preventivas
        if not alertas:
            return "✅ Em dia"
        return " ⚠️ ".join(alertas)
    exibir_alertas.short_description = "Status de Manutenção"

# --- 3. MENUS ESPECÍFICOS ---
@admin.register(MenuOleo)
class OleoAdmin(ComponenteBaseAdmin):
    def get_queryset(self, request): return super().get_queryset(request).filter(grupo__slug='oleo')

@admin.register(MenuFiltros)
class FiltrosAdmin(ComponenteBaseAdmin):
    def get_queryset(self, request): return super().get_queryset(request).filter(grupo__slug='filtros')

@admin.register(MenuPerifericos)
class PerifericosAdmin(ComponenteBaseAdmin):
    def get_queryset(self, request): return super().get_queryset(request).filter(grupo__slug='perifericos')

@admin.register(MenuIgnicao)
class IgnicaoAdmin(ComponenteBaseAdmin):
    def get_queryset(self, request): return super().get_queryset(request).filter(grupo__slug='ignicao')

@admin.register(MenuCilindros)
class CilindrosAdmin(ComponenteBaseAdmin):
    def get_queryset(self, request): return super().get_queryset(request).filter(grupo__slug='cilindros')

@admin.register(MenuCabecotes)
class CabecotesAdmin(ComponenteBaseAdmin):
    def get_queryset(self, request): return super().get_queryset(request).filter(grupo__slug='cabecotes')

@admin.register(MenuOutros)
class OutrosAdmin(ComponenteBaseAdmin):
    def get_queryset(self, request):
        slugs_padrao = ['oleo', 'filtros', 'perifericos', 'ignicao', 'cilindros', 'cabecotes']
        return super().get_queryset(request).exclude(grupo__slug__in=slugs_padrao)

# --- 4. GERENCIADOR DE CATEGORIAS ---
@admin.register(GrupoComponente)
class GrupoComponenteAdmin(TenantModelAdmin): 
    list_display = ('id', 'nome', 'motor', 'slug', 'ordem')
    list_display_links = ('id',) 
    list_filter = ('motor',)
    list_editable = ('nome', 'ordem')
    readonly_fields = ('slug',)

# --- 5. BUSCA TÉCNICA ---
@admin.register(PosicaoComponente)
class PosicaoComponenteBuscaAdmin(ComponenteBaseAdmin): 
    search_fields = ('nome', 'serial_number')
    def has_module_permission(self, request): return False