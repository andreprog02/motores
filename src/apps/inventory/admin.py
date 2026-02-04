from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin
from .models import CategoriaPeca, CatalogoPeca, EstoqueItem, MovimentoEstoque

@admin.register(CategoriaPeca)
class CategoriaPecaAdmin(TenantModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(CatalogoPeca)
class CatalogoAdmin(TenantModelAdmin):
    list_display = ('nome', 'codigo_fabricante', 'categoria', 'aplicacao_universal')
    list_filter = ('categoria', 'aplicacao_universal')
    search_fields = ('nome', 'codigo_fabricante')
    
    # AQUI ESTÁ A SOLUÇÃO:
    # filter_horizontal cria aquela caixa dupla de seleção (Esquerda -> Direita)
    filter_horizontal = ('modelos_compativeis',)
    
    # Organização visual dos campos
    fieldsets = (
        ('Dados Principais', {
            'fields': ('nome', 'codigo_fabricante', 'categoria')
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
            'classes': ('collapse',), # Esconde essa seção para não poluir a tela
        }),
    )

@admin.register(EstoqueItem)
class EstoqueAdmin(TenantModelAdmin):
    list_display = ('catalogo', 'quantidade', 'local', 'minimo_seguranca')
    list_filter = ('local',)
    # Busca necessária para o Livro de Ocorrências
    search_fields = ('catalogo__nome', 'catalogo__codigo_fabricante')
    autocomplete_fields = ['catalogo']

@admin.register(MovimentoEstoque)
class MovimentoAdmin(TenantModelAdmin):
    list_display = ('data_movimento', 'tipo', 'item', 'quantidade', 'origem')
    list_filter = ('tipo', 'data_movimento')