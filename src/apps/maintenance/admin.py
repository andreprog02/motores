from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin
from .models import RegistroManutencao

# --- COMENTE TUDO AQUI TEMPORARIAMENTE ---
# @admin.register(RegistroManutencao)
# class RegistroManutencaoAdmin(TenantModelAdmin):
#     list_display = ('data_ocorrencia', 'motor', 'posicao', 'tipo_atividade')
#     list_filter = ('motor', 'tipo_atividade', 'data_ocorrencia')
#     search_fields = ('motor__nome', 'posicao__nome') 
#     fieldsets = (
#         ('Dados Principais', {
#             'fields': ('motor', 'posicao', 'data_ocorrencia', 'tipo_atividade')
#         }),
#     )