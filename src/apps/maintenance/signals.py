from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import RegistroManutencao

def _atualizar_dados_componente(registro, componente):
    """
    Função auxiliar que aplica os dados da manutenção ao componente.
    """
    print(f"--- Processando Componente: {componente.nome} ---")
    
    # 1. Atualiza Data
    componente.data_instalacao = registro.data_ocorrencia
    
    # 2. Atualiza Horímetro (se informado)
    if registro.horimetro_na_execucao is not None:
        componente.hora_motor_instalacao = registro.horimetro_na_execucao
        print(f"   > Horímetro atualizado para: {registro.horimetro_na_execucao}")
    
    # 3. Atualiza Arranques (se informado)
    if registro.arranques_na_execucao is not None:
        componente.arranques_motor_instalacao = registro.arranques_na_execucao
        print(f"   > Arranques atualizados para: {registro.arranques_na_execucao}")
        
    # 4. Atualiza Serial (se informado)
    if registro.novo_serial_number:
        componente.serial_number = registro.novo_serial_number
        print(f"   > Novo Serial: {registro.novo_serial_number}")

    componente.save()
    print("   > Salvo com sucesso!")


@receiver(post_save, sender=RegistroManutencao)
def manutencao_post_save(sender, instance, created, **kwargs):
    """
    1. Baixa de Estoque (Apenas na Criação)
    2. Atualização de Componentes (Apenas na Edição - quando created=False)
    """
    print(f"SINAL POST_SAVE DISPARADO. Criado: {created}")

    # --- LÓGICA DE ESTOQUE (Só na criação) ---
    if created and instance.item_estoque and instance.quantidade_utilizada > 0:
        print(f"   > Baixando {instance.quantidade_utilizada} do estoque...")
        estoque = instance.item_estoque
        estoque.quantidade -= instance.quantidade_utilizada
        estoque.save()

    # --- LÓGICA DE COMPONENTES (Só na edição) ---
    # Se estamos EDITANDO, a relação M2M já existe, então podemos iterar.
    # Se estamos CRIANDO, a lista instance.componentes.all() estaria vazia aqui.
    if not created and instance.tipo_atividade in ['SUBSTITUICAO', 'INSTALACAO']:
        for comp in instance.componentes.all():
            _atualizar_dados_componente(instance, comp)


@receiver(m2m_changed, sender=RegistroManutencao.componentes.through)
def manutencao_componentes_changed(sender, instance, action, pk_set, **kwargs):
    """
    Captura o momento exato em que os componentes são adicionados ao registro.
    Crucial para a tela de CRIAÇÃO do Admin.
    """
    # Só roda se estiver ADICIONANDO itens e for troca/instalação
    if action == 'post_add' and instance.tipo_atividade in ['SUBSTITUICAO', 'INSTALACAO']:
        print(f"SINAL M2M DISPARADO (Ação: {action})")
        
        # Importação local para evitar ciclo
        from src.apps.components.models import PosicaoComponente
        
        # Pega os objetos reais baseados nos IDs selecionados (pk_set)
        componentes_afetados = PosicaoComponente.objects.filter(pk__in=pk_set)
        
        for comp in componentes_afetados:
            _atualizar_dados_componente(instance, comp)