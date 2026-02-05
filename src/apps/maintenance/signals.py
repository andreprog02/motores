from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RegistroManutencao
from src.apps.components.models import PlanoPreventiva


@receiver(post_save, sender=RegistroManutencao)
def orquestrador_manutencao(sender, instance, created, **kwargs):
    if not created:
        return

    print(f"--- Processando Manutenção ID: {instance.id} ---")

    # ==========================================================
    # 0. ATUALIZAÇÃO DO MOTOR (HORAS E ARRANQUES)
    # ==========================================================
    # Garante que o motor esteja sempre com o horímetro/arranques mais recentes
    motor = instance.motor
    updated_motor = False

    # Atualiza Horas
    if instance.horimetro_na_execucao > motor.horas_totais:
        motor.horas_totais = instance.horimetro_na_execucao
        updated_motor = True
    
    # Atualiza Arranques (CORREÇÃO PARA SUA PERGUNTA)
    if instance.arranques_na_execucao and instance.arranques_na_execucao > motor.total_arranques:
        motor.total_arranques = instance.arranques_na_execucao
        updated_motor = True
        print(f"✅ Motor: Total de arranques atualizado para {motor.total_arranques}")

    if updated_motor:
        motor.save()
# ==========================================================
    # 2. ATUALIZAÇÃO FÍSICA DO COMPONENTE
    # ==========================================================
    posicao = instance.posicao
    atividades_de_troca = ['SUBSTITUICAO', 'INSTALACAO', 'TROCA']

    if instance.tipo_atividade in atividades_de_troca:
        posicao.data_instalacao = instance.data_ocorrencia
        posicao.hora_motor_instalacao = instance.horimetro_na_execucao or 0
        
        # Se foi informado arranques, grava no componente também
        if instance.arranques_na_execucao is not None:
            posicao.arranques_motor_instalacao = instance.arranques_na_execucao
            
        if instance.novo_serial_number:
            posicao.serial_number = instance.novo_serial_number
            
        posicao.save()

    elif instance.tipo_atividade == 'LUBRIFICACAO':
        posicao.ultimo_engraxamento = instance.data_ocorrencia
        posicao.save()

    # ==========================================================
    # 3. AUTOMAÇÃO DE PREVENTIVAS
    # ==========================================================
    planos_afetados = PlanoPreventiva.objects.filter(
        posicao=posicao,
        tipo_servico=instance.tipo_atividade 
    )
    
    count_planos = 0
    for plano in planos_afetados:
        plano.ultima_execucao_data = instance.data_ocorrencia

        if plano.unidade == 'HORAS':
            plano.ultima_execucao_valor = instance.horimetro_na_execucao or 0
        
        elif plano.unidade == 'ARRANQUES':
            # Usa o valor da manutenção. Se não tiver, usa 0 (mas ideal é ser obrigatório na tela)
            plano.ultima_execucao_valor = instance.arranques_na_execucao or 0
        
        plano.save()
        count_planos += 1
        
    if count_planos > 0:
        print(f"✅ Preventivas: {count_planos} planos atualizados.")

    # ==========================================================
    # 1. BAIXA DE ESTOQUE
    # ==========================================================
    if instance.item_estoque and instance.quantidade_utilizada > 0:
        estoque = instance.item_estoque
        if estoque.quantidade >= instance.quantidade_utilizada:
            estoque.quantidade -= instance.quantidade_utilizada
            estoque.save()
            print(f"✅ Estoque: Baixado {instance.quantidade_utilizada} un de '{estoque.catalogo.nome}'")

@receiver(post_save, sender=RegistroManutencao)
def orquestrador_manutencao(sender, instance, created, **kwargs):
    """
    Função Mestre que roda toda vez que uma manutenção é salva.
    Realiza 3 tarefas críticas:
    1. Baixa de Estoque (Se houver peça vinculada)
    2. Atualização Física do Componente (Se for Troca/Instalação)
    3. Automação de Preventivas (Reset inteligente de Horas, Arranques ou Tempo)
    """
    
    # Executa apenas na criação do registro para evitar duplicidade de baixa ou loops
    if not created:
        return

    print(f"--- Processando Manutenção ID: {instance.id} ---")

    # ==========================================================
    # 1. BAIXA DE ESTOQUE
    # ==========================================================
    if instance.item_estoque and instance.quantidade_utilizada > 0:
        estoque = instance.item_estoque
        
        # Opcional: Validar saldo antes de baixar
        if estoque.quantidade >= instance.quantidade_utilizada:
            estoque.quantidade -= instance.quantidade_utilizada
            estoque.save()
            print(f"✅ Estoque: Baixado {instance.quantidade_utilizada} un de '{estoque.catalogo.nome}'")
        else:
            print(f"⚠️ Estoque: Saldo insuficiente para baixa automática no item '{estoque.catalogo.nome}'")

    # ==========================================================
    # 2. ATUALIZAÇÃO FÍSICA DO COMPONENTE
    # ==========================================================
    # Atualiza os dados do 'Componente Instalado' na árvore de ativos
    posicao = instance.posicao
    
    # Lista de atividades que significam "Peça Nova"
    atividades_de_troca = ['SUBSTITUICAO', 'INSTALACAO', 'TROCA']

    if instance.tipo_atividade in atividades_de_troca:
        # Atualiza a data de instalação
        posicao.data_instalacao = instance.data_ocorrencia
        
        # Atualiza o horímetro de instalação (Base para cálculo de horas de uso)
        posicao.hora_motor_instalacao = instance.horimetro_na_execucao or 0
        
        # Se foi informado arranques, atualiza também
        if instance.arranques_na_execucao is not None:
            posicao.arranques_motor_instalacao = instance.arranques_na_execucao
            
        # Se foi informado novo serial, substitui o antigo
        if instance.novo_serial_number:
            posicao.serial_number = instance.novo_serial_number
            
        posicao.save()
        print(f"✅ Componente: Slot '{posicao.nome}' atualizado com novos dados de instalação.")

    # Lógica específica para Lubrificação
    elif instance.tipo_atividade == 'LUBRIFICACAO':
        posicao.ultimo_engraxamento = instance.data_ocorrencia
        posicao.save()
        print(f"✅ Componente: Data de engraxamento atualizada.")

    # ==========================================================
    # 3. AUTOMAÇÃO DE PREVENTIVAS (RESET INTELIGENTE)
    # ==========================================================
    # Busca planos vinculados a este componente que tenham o MESMO gatilho (tipo_servico)
    # Ex: Se lancei "REGULAGEM", busca preventivas de "Regulagem"
    
    planos_afetados = PlanoPreventiva.objects.filter(
        posicao=posicao,
        tipo_servico=instance.tipo_atividade 
    )
    
    count_planos = 0
    for plano in planos_afetados:
        
        # A. Atualiza a DATA da última execução (Serve para todos os tipos)
        plano.ultima_execucao_data = instance.data_ocorrencia

        # B. Atualiza o CONTADOR dependendo da unidade do plano
        if plano.unidade == 'HORAS':
            # Se o plano é por hora, grava o horímetro atual como o novo "Zero"
            plano.ultima_execucao_valor = instance.horimetro_na_execucao or 0
        
        elif plano.unidade == 'ARRANQUES':
            # Se o plano é por partidas, grava os arranques atuais
            # Se o usuário não preencheu arranques na manutenção, assume 0 ou mantém o anterior (aqui assumimos 0 por segurança)
            plano.ultima_execucao_valor = instance.arranques_na_execucao or 0
            
        # Se for DIAS ou MESES, o item (A) já resolveu.

        plano.save()
        count_planos += 1
        
    if count_planos > 0:
        print(f"✅ Preventivas: {count_planos} planos foram resetados/atualizados.")