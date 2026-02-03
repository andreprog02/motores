from django.contrib import admin
from django.core.exceptions import ValidationError
from src.apps.core.admin import TenantModelAdmin
from .models import RegistroManutencao

@admin.register(RegistroManutencao)
class RegistroManutencaoAdmin(TenantModelAdmin):
    list_display = ('data_ocorrencia', 'tipo_atividade', 'motor', 'posicao', 'responsavel')
    list_filter = ('tipo_atividade', 'motor')
    
    # Busca inteligente
    autocomplete_fields = ['motor', 'posicao', 'item_estoque_utilizado'] 
    
    # Interface simples e direta
    fields = (
        'data_ocorrencia', 
        'motor', 
        'posicao', 
        'horimetro_na_execucao',
        'tipo_atividade', 
        'item_estoque_utilizado', # Fica visível sempre
        'novo_serial_number',
        'responsavel', 
        'observacao'
    )


    class Media:
        # Carrega OS DOIS scripts (o de bloqueio e o de máscara)
        js = ('js/bloqueio_pecas.js', 'js/mascaras.js')

    def save_model(self, request, obj, form, change):
        from src.apps.maintenance.services import registrar_intervencao
        
        if change:
            super().save_model(request, obj, form, change)
            return

        try:
            registrar_intervencao(
                tenant=request.user.tenant, 
                usuario=request.user,
                motor_id=obj.motor.id,
                posicao_id=obj.posicao.id,
                tipo_atividade=obj.tipo_atividade,
                horimetro_atual=obj.horimetro_na_execucao,
                data_ocorrencia=obj.data_ocorrencia,
                estoque_item_id=obj.item_estoque_utilizado.id if obj.item_estoque_utilizado else None,
                novo_serial=obj.novo_serial_number,
                observacao=obj.observacao
            )
        except ValidationError as e:
            from django.contrib import messages
            messages.set_level(request, messages.ERROR)
            messages.error(request, f"ERRO AO SALVAR: {e}")