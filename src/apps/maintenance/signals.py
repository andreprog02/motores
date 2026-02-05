from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import RegistroManutencao

# --- Mantendo sua função auxiliar EXATAMENTE como você pediu ---
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
    2. Atualização de Componentes (Criação e Edição)
    
    Nota: Como mudamos para ForeignKey, não precisamos mais do m2m_changed.
    O campo 'posicao' já está disponível aqui mesmo.
    """
    print(f"SINAL POST_SAVE DISPARADO. Criado: {created}")

    # --- LÓGICA DE ESTOQUE (Só na criação) ---
    if created and instance.item_estoque and instance.quantidade_utilizada > 0:
        print(f"   > Baixando {instance.quantidade_utilizada} do estoque...")
        estoque = instance.item_estoque
        estoque.quantidade -= instance.quantidade_utilizada
        estoque.save()

    # --- LÓGICA DE COMPONENTES ---
    # Aqui unificamos o que antes ficava dividido entre post_save (edição) e m2m_changed (criação).
    # Agora roda sempre, garantindo que o componente seja atualizado.
    
    if instance.tipo_atividade in ['SUBSTITUICAO', 'INSTALACAO']:
        # Pegamos o componente diretamente (antes era via lista)
        comp = instance.posicao
        _atualizar_dados_componente(instance, comp)
        
    elif instance.tipo_atividade == 'LUBRIFICACAO':
        # Mantendo lógica extra se houver
        comp = instance.posicao
        comp.ultimo_engraxamento = instance.data_ocorrencia
        comp.save()
        print(f"   > Lubrificação registrada em: {instance.data_ocorrencia}")