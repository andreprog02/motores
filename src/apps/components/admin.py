from django.contrib import admin
from .models import (
    GrupoComponente, PosicaoComponente, 
    MenuOleo, MenuFiltros, MenuPerifericos, MenuIgnicao, 
    MenuCilindros, MenuCabecotes, MenuOutros
)

# --- BASE ---
class ComponenteBaseAdmin(admin.ModelAdmin):
    list_display = ('nome', 'peca_instalada', 'motor', 'horas_uso_atual')
    list_filter = ('motor',)
    search_fields = ('nome', 'serial_number')
    autocomplete_fields = ['peca_instalada']
    
    def get_queryset(self, request):
        return super().get_queryset(request)

# --- MENUS ESPECÍFICOS ---
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

# --- GERENCIADOR DE CATEGORIAS ---
@admin.register(GrupoComponente)
class GrupoComponenteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'motor', 'slug', 'ordem')
    list_display_links = ('id',) # Link no ID para permitir edição do nome na lista
    list_filter = ('motor',)
    list_editable = ('nome', 'ordem')
    readonly_fields = ('slug',)