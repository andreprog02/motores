from django.db import transaction
from django.core.exceptions import ValidationError
from src.apps.maintenance.models import RegistroManutencao
from src.apps.assets.models import PosicaoComponente, Motor, Equipamento
from src.apps.inventory.models import EstoqueItem

def registrar_intervencao(
    *,
    tenant,
    usuario,
    posicao_id: int,
    tipo_atividade: str,
    horimetro_atual: int, 
    data_ocorrencia,
    motor_id: int = None,       # Agora opcional
    equipamento_id: int = None, # Novo parametro opcional
    estoque_item_id: int = None,
    novo_serial: str = None,
    observacao: str = ""
) -> RegistroManutencao:
    
    with transaction.atomic():
        # --- 1. Identificar o Ativo (Motor ou Equipamento) ---
        motor = None
        equipamento = None
        ativo = None

        if motor_id:
            motor = Motor.objects.get(id=motor_id, tenant=tenant)
            ativo = motor
        elif equipamento_id:
            equipamento = Equipamento.objects.get(id=equipamento_id, tenant=tenant)
            ativo = equipamento
        else:
            raise ValidationError("É necessário informar o ID do Motor ou do Equipamento para registrar a intervenção.")

        # Busca a posição e trava o registro
        posicao = PosicaoComponente.objects.select_for_update().get(id=posicao_id, tenant=tenant)
        
        # (Opcional) Validação de Integridade: A peça pertence mesmo a este ativo?
        if posicao.ativo_pai != ativo:
             raise ValidationError(f"O componente '{posicao.nome}' não pertence ao ativo informado ({ativo}).")

        # --- 2. Validação de Hierarquia (Horas) ---
        # Compara com o horímetro do ativo correto
        if horimetro_atual > ativo.horas_totais:
            raise ValidationError(
                f"Erro: O ativo {ativo} tem {ativo.horas_totais}h. "
                f"Não é possível registrar intervenção futura com {horimetro_atual}h."
            )

        item_estoque = None
        
        # --- 3. Lógica de Troca de Peças ---
        if tipo_atividade in ['TROCA', 'SUBSTITUICAO']:
            if not estoque_item_id:
                raise ValidationError("Para substituição, informe o Item de Estoque.")
            
            item_estoque = EstoqueItem.objects.select_for_update().get(id=estoque_item_id, tenant=tenant)
            catalogo = item_estoque.catalogo

            # 4. Validação de Compatibilidade (Motor x Peça)
            # Se for MOTOR, validamos rigorosamente o modelo.
            # Se for EQUIPAMENTO, validamos apenas se for universal (ou pulamos a validação de modelo de motor).
            if motor and not catalogo.aplicacao_universal:
                if not catalogo.modelos_compativeis.filter(id=motor.modelo.id).exists():
                    raise ValidationError(f"Peça incompatível com o motor {motor.modelo}.")
            
            # 5. Baixa no Estoque
            if item_estoque.quantidade < catalogo.quantidade_por_jogo:
                raise ValidationError(f"Estoque insuficiente. Disponível: {item_estoque.quantidade}")
            
            item_estoque.quantidade -= catalogo.quantidade_por_jogo
            item_estoque.save()

            # 6. Atualiza a Posição no Ativo
            posicao.peca_instalada = catalogo
            posicao.hora_motor_instalacao = horimetro_atual
            posicao.data_instalacao = data_ocorrencia
            posicao.serial_number = novo_serial
            posicao.save()

        elif tipo_atividade == 'LUBRIFICACAO':
            posicao.ultimo_engraxamento = data_ocorrencia
            posicao.save()

        # --- 7. Cria o Registro Histórico ---
        return RegistroManutencao.objects.create(
            tenant=tenant,
            responsavel=usuario,
            motor=motor,              # Salva Motor (se houver)
            equipamento=equipamento,  # Salva Equipamento (se houver)
            posicao=posicao,
            tipo_atividade=tipo_atividade,
            horimetro_na_execucao=horimetro_atual,
            item_estoque=item_estoque, # Corrigido para corresponder ao models.py
            novo_serial_number=novo_serial,
            data_ocorrencia=data_ocorrencia,
            observacao=observacao
        )