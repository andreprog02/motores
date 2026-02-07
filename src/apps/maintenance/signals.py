from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RegistroManutencao
from src.apps.components.models import PlanoPreventiva

@receiver(post_save, sender=RegistroManutencao)
def orquestrador_manutencao(sender, instance, created, **kwargs):
    """
    Função Mestre que roda toda vez que uma manutenção é salva.
    """
    if not created:
        return

    print(f"--- Processando Manutenção ID: {instance.id} ---")

    # ==========================================================
    # 1. BAIXA DE ESTOQUE (Mantido igual)
    # ==========================================================
    if instance.item_estoque and instance.quantidade_utilizada > 0:
        estoque = instance.item_estoque
        if estoque.quantidade >= instance.quantidade_utilizada:
            estoque.quantidade -= instance.quantidade_utilizada
            estoque.save()
            print(f"✅ Estoque: Baixado {instance.quantidade_utilizada} un de '{estoque.catalogo.nome}'")
        else:
            print(f"⚠️ Estoque: Saldo insuficiente para baixa automática no item '{estoque.catalogo.nome}'")

    # ==========================================================
    # 2. ATUALIZAÇÃO FÍSICA DO COMPONENTE (Mantido igual)
    # ==========================================================
    posicao = instance.posicao
    
    # Lista de atividades que significam "Peça Nova"
    atividades_de_troca = ['SUBSTITUICAO', 'INSTALACAO', 'TROCA']

    if instance.tipo_atividade in atividades_de_troca:
        posicao.data_instalacao = instance.data_ocorrencia
        posicao.hora_motor_instalacao = instance.horimetro_na_execucao or 0
        
        if instance.arranques_na_execucao is not None:
            posicao.arranques_motor_instalacao = instance.arranques_na_execucao
            
        if instance.novo_serial_number:
            posicao.serial_number = instance.novo_serial_number
            
        posicao.save()
        print(f"✅ Componente: Slot '{posicao.nome}' atualizado com novos dados de instalação.")

    elif instance.tipo_atividade == 'LUBRIFICACAO':
        posicao.ultimo_engraxamento = instance.data_ocorrencia
        posicao.save()
        print(f"✅ Componente: Data de engraxamento atualizada.")

    # ==========================================================
    # 3. AUTOMAÇÃO DE PREVENTIVAS (MODIFICADO)
    # ==========================================================
    
    # LÓGICA NOVA: Se for troca de peça, zera TODOS os contadores (Limpeza, Regulagem, etc.)
    # Se for apenas um serviço (ex: Limpeza), zera apenas o contador da Limpeza.
    
    if instance.tipo_atividade in atividades_de_troca:
        # Busca TODOS os planos vinculados a esta posição
        planos_afetados = PlanoPreventiva.objects.filter(posicao=posicao)
        print("🔄 Substituição de peça detectada: Zerando TODOS os planos preventivos.")
    else:
        # Busca apenas os planos que tem este tipo de serviço como gatilho
        planos_afetados = PlanoPreventiva.objects.filter(
            posicao=posicao,
            tipo_servico=instance.tipo_atividade 
        )
    
    count_planos = 0
    for plano in planos_afetados:
        
        # A. Atualiza a DATA da última execução
        plano.ultima_execucao_data = instance.data_ocorrencia

        # B. Atualiza o CONTADOR (define o novo "zero")
        if plano.unidade == 'HORAS':
            plano.ultima_execucao_valor = instance.horimetro_na_execucao or 0
        
        elif plano.unidade == 'ARRANQUES':
            # Se não foi informado o nº de arranques, tenta pegar do motor para não zerar erradamente
            valor_arranques = instance.arranques_na_execucao
            if valor_arranques is None:
                valor_arranques = instance.motor.total_arranques
            
            plano.ultima_execucao_valor = valor_arranques or 0
            
        plano.save()
        count_planos += 1
        
    if count_planos > 0:
        print(f"✅ Preventivas: {count_planos} planos foram resetados/atualizados.")