from django.db import transaction
from django.core.exceptions import ValidationError
from src.apps.maintenance.models import RegistroManutencao
from src.apps.assets.models import PosicaoComponente, Motor
from src.apps.inventory.models import EstoqueItem

def registrar_intervencao(
    *,
    tenant,
    usuario,
    motor_id: int,
    posicao_id: int,
    tipo_atividade: str,
    horimetro_atual: int, # Garante que recebemos um inteiro
    data_ocorrencia,
    estoque_item_id: int = None,
    novo_serial: str = None,
    observacao: str = ""
) -> RegistroManutencao:
    
    with transaction.atomic():
        motor = Motor.objects.get(id=motor_id, tenant=tenant)
        posicao = PosicaoComponente.objects.select_for_update().get(id=posicao_id, tenant=tenant)
        
        # 1. Validação de Hierarquia (Horas)
        # Como agora tudo é inteiro, a comparação é direta e segura
        if horimetro_atual > motor.horas_totais:
            raise ValidationError(
                f"Erro: O motor tem {motor.horas_totais}h. "
                f"Não é possível registrar intervenção futura com {horimetro_atual}h."
            )

        item_estoque = None
        
        # 2. Lógica de Troca de Peças
        if tipo_atividade in ['TROCA', 'SUBSTITUICAO']:
            if not estoque_item_id:
                raise ValidationError("Para substituição, informe o Item de Estoque.")
            
            item_estoque = EstoqueItem.objects.select_for_update().get(id=estoque_item_id, tenant=tenant)
            catalogo = item_estoque.catalogo

            # 3. Validação de Compatibilidade (Motor x Peça)
            if not catalogo.aplicacao_universal:
                if not catalogo.modelos_compativeis.filter(id=motor.modelo.id).exists():
                    raise ValidationError(f"Peça incompatível com o motor {motor.modelo}.")
            
            # 4. Baixa no Estoque
            # Verifica se tem quantidade suficiente (agora comparando inteiros)
            if item_estoque.quantidade < catalogo.quantidade_por_jogo:
                raise ValidationError(f"Estoque insuficiente. Disponível: {item_estoque.quantidade}")
            
            item_estoque.quantidade -= catalogo.quantidade_por_jogo
            item_estoque.save()

            # 5. Atualiza a Posição no Motor
            posicao.peca_instalada = catalogo
            posicao.hora_motor_instalacao = horimetro_atual
            posicao.data_instalacao = data_ocorrencia
            posicao.serial_number = novo_serial
            posicao.save()

        elif tipo_atividade == 'LUBRIFICACAO':
            posicao.ultimo_engraxamento = data_ocorrencia
            posicao.save()

        # 6. Cria o Registro Histórico
        return RegistroManutencao.objects.create(
            tenant=tenant,
            responsavel=usuario,
            motor=motor,
            posicao=posicao,
            tipo_atividade=tipo_atividade,
            horimetro_na_execucao=horimetro_atual,
            item_estoque_utilizado=item_estoque,
            novo_serial_number=novo_serial,
            data_ocorrencia=data_ocorrencia,
            observacao=observacao
        )