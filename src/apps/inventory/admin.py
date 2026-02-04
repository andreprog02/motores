from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin
from .models import CategoriaPeca, CatalogoPeca, EstoqueItem, MovimentoEstoque

@admin.register(CategoriaPeca)
class CategoriaPecaAdmin(TenantModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(CatalogoPeca)
class CatalogoAdmin(TenantModelAdmin):
    # Ajustado para os campos reais do seu model
    list_display = ('nome', 'codigo_fabricante', 'categoria')
    list_filter = ('categoria',)
    search_fields = ('nome', 'codigo_fabricante')

@admin.register(EstoqueItem)
class EstoqueAdmin(TenantModelAdmin):
    # Ajustado: 'catalogo' em vez de 'peca', 'local' em vez de 'localizacao'
    list_display = ('catalogo', 'quantidade', 'local', 'minimo_seguranca')
    list_filter = ('local',)
    search_fields = ('catalogo__nome', 'catalogo__codigo_fabricante')

@admin.register(MovimentoEstoque)
class MovimentoAdmin(TenantModelAdmin):
    list_display = ('data_movimento', 'tipo', 'item', 'quantidade', 'origem')
    list_filter = ('tipo', 'data_movimento')