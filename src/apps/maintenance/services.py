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
    horimetro_atual: float, # Horímetro lido no painel no momento da troca
    data_ocorrencia,
    estoque_item_id: int = None,
    novo_serial: str = None,
    observacao: str = ""
) -> RegistroManutencao:
    
    with transaction.atomic():
        # 1. Busca os objetos (Motor agora é apenas para consulta)
        motor = Motor.objects.get(id=motor_id, tenant=tenant)
        posicao = PosicaoComponente.objects.select_for_update().get(id=posicao_id, tenant=tenant)
        
        # 2. VALIDAÇÃO DE HIERARQUIA
        # Não faz sentido trocar uma peça com 3000h se o motor só tem 2500h
        if horimetro_atual > motor.horas_totais:
            raise ValidationError(
                f"Erro de Hierarquia: O motor tem {motor.horas_totais}h. "
                f"Você não pode registrar uma intervenção com {horimetro_atual}h. "
                "Atualize primeiro o horímetro no cadastro do Motor."
            )

        # 3. Lógica de Peça
        item_estoque = None
        if tipo_atividade == 'TROCA':
            if not estoque_item_id:
                raise ValidationError("Para substituição, informe o Item de Estoque.")
            
            item_estoque = EstoqueItem.objects.select_for_update().get(id=estoque_item_id, tenant=tenant)
            
            # Baixa estoque
            qtd_a_baixar = item_estoque.catalogo.quantidade_por_jogo
            if item_estoque.quantidade < qtd_a_baixar:
                raise ValidationError(f"Estoque insuficiente. Disponível: {item_estoque.quantidade}")
            
            item_estoque.quantidade -= qtd_a_baixar
            item_estoque.save()

            # ZERA O USO DA PEÇA (Marca o ponto de instalação no histórico do motor)
            posicao.peca_instalada = item_estoque.catalogo
            posicao.hora_motor_instalacao = horimetro_atual # A peça "nasce" nesta hora do motor
            posicao.data_instalacao = data_ocorrencia
            posicao.serial_number = novo_serial
            posicao.save()

        elif tipo_atividade == 'LUBRIFICACAO':
            posicao.ultimo_engraxamento = data_ocorrencia
            posicao.save()

        # 4. Cria o log histórico (O Motor NÃO é alterado aqui)
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