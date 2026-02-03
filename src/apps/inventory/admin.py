from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin # <--- Importamos nossa classe inteligente
from .models import CategoriaPeca, CatalogoPeca, LocalEstoque, EstoqueItem

@admin.register(CategoriaPeca)
class CategoriaAdmin(TenantModelAdmin): 
    list_display = ('nome',)

@admin.register(CatalogoPeca)
class CatalogoAdmin(TenantModelAdmin):
    list_display = ('nome', 'categoria', 'vida_util_horas', 'requer_serial_number')
    list_filter = ('categoria', 'requer_serial_number')
    search_fields = ('nome', 'codigo_fabricante')

@admin.register(LocalEstoque)
class LocalAdmin(TenantModelAdmin):
    list_display = ('nome',)

@admin.register(EstoqueItem)
class EstoqueAdmin(TenantModelAdmin):
    list_display = ('catalogo', 'local', 'quantidade')
    list_filter = ('local',)