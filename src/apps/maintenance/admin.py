from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import RegistroManutencao
from .services import registrar_intervencao

@admin.register(RegistroManutencao)
class RegistroAdmin(admin.ModelAdmin):
    list_display = ('data_ocorrencia', 'tipo_atividade', 'motor', 'posicao', 'responsavel')
    list_filter = ('tipo_atividade', 'motor')
    
    # Melhora a busca de campos chave (senão carrega uma lista gigante)
    # Nota: Você precisa ter configurado search_fields no MotorAdmin e PosicaoAdmin para isso funcionar 100%
    # autocomplete_fields = ['motor', 'posicao', 'item_estoque_utilizado'] 

    def save_model(self, request, obj, form, change):
        """
        Sobrescreve o salvamento padrão do Admin.
        Em vez de apenas salvar no banco, chama o nosso SERVICE que contém a inteligência.
        """
        if change:
            # Não permitimos editar histórico de manutenção pelo Admin para evitar fraudes
            messages.error(request, "Não é permitido editar um registro de manutenção histórico.")
            return

        try:
            # Verifica se o usuário tem um Tenant (Empresa) atribuído
            if not request.user.tenant:
                messages.error(request, "SEU USUÁRIO NÃO TEM EMPRESA (TENANT)! Vá em Core > Usuários e selecione uma empresa para você.")
                return

            # Chama a nossa lógica blindada
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
            
            messages.success(request, f"Sucesso! Manutenção registrada, estoque baixado e horas do componente zeradas.")

        except ValidationError as e:
            # Se o service reclamar (ex: falta de estoque), mostramos o erro na tela
            messages.error(request, f"ERRO DE VALIDAÇÃO: {e.message}")
            
        except Exception as e:
            messages.error(request, f"ERRO CRÍTICO: {str(e)}")

    # Removemos o botão de "Salvar e continuar editando" para evitar confusão
    def response_add(self, request, obj, post_url_continue=None):
        return super().response_add(request, obj, post_url_continue="../")