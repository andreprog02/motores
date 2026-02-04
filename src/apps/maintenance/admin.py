from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin
from .models import RegistroManutencao

@admin.register(RegistroManutencao)
class RegistroManutencaoAdmin(TenantModelAdmin):
    list_display = ('data_ocorrencia', 'motor', 'exibir_componentes', 'tipo_atividade', 'horimetro_na_execucao')
    list_filter = ('tipo_atividade', 'motor')
    search_fields = ('motor__nome', 'observacao', 'componentes__nome') # Busca pelo nome dos componentes internos
    
    # Busca inteligente (Suporta seleção múltipla!)
    autocomplete_fields = ['motor', 'componentes', 'item_estoque']

    fieldsets = (
        ('1. Contexto', {
            'fields': ('data_ocorrencia', 'motor', 'horimetro_na_execucao', 'arranques_na_execucao')
        }),
        ('2. Serviço e Componentes', {
            'fields': ('tipo_atividade', 'componentes', 'novo_serial_number'),
            'description': 'Você pode selecionar VÁRIOS componentes aqui (ex: todos os 16 pistões).'
        }),
        ('3. Estoque', {
            'fields': ('item_estoque', 'quantidade_utilizada'),
            'description': 'Coloque a quantidade TOTAL gasta (ex: se trocou 16 pistões, coloque 16).'
        }),
        ('4. Detalhes', {
            'fields': ('responsavel', 'observacao')
        }),
    )

    def exibir_componentes(self, obj):
        # Exibe os primeiros 3 itens na lista para não poluir
        comps = obj.componentes.all()
        if comps.count() > 3:
            return f"{', '.join([c.nome for c in comps[:3]])} e mais {comps.count()-3}..."
        return ", ".join([c.nome for c in comps])
    exibir_componentes.short_description = "Componentes Afetados"