from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin
from .models import RegistroManutencao

@admin.register(RegistroManutencao)
class RegistroManutencaoAdmin(TenantModelAdmin):
    list_display = ('data_ocorrencia', 'motor', 'posicao', 'tipo_atividade', 'horimetro_na_execucao', 'responsavel')
    list_filter = ('motor', 'tipo_atividade', 'data_ocorrencia')
    search_fields = ('motor__nome', 'posicao__nome', 'responsavel', 'observacao')
    autocomplete_fields = ['motor', 'posicao']
    
    fieldsets = (
        ('Dados Principais', {
            'fields': ('motor', 'posicao', 'data_ocorrencia', 'tipo_atividade')
        }),
        ('Detalhes da Execução', {
            'fields': ('horimetro_na_execucao', 'responsavel', 'observacao')
        }),
        ('Troca de Peças', {
            # 'item_estoque_utilizado' removido temporariamente
            'fields': ('novo_serial_number',) 
        }),
    )