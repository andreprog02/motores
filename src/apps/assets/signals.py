from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Motor, PosicaoComponente

@receiver(post_save, sender=Motor)
def criar_componentes_automaticos(sender, instance, created, **kwargs):
    """
    Sempre que um Motor for salvo, verifica se os componentes (slots)
    existem na quantidade correta. Se não, cria-os.
    """
    
    # Função auxiliar para criar slots em loop
    def garantir_slots(nome_base, quantidade):
        if not quantidade:
            return
            
        for i in range(1, quantidade + 1):
            nome_slot = f"{nome_base} #{i:02d}"  # Ex: Filtro de Ar #01
            
            # get_or_create evita duplicidade: só cria se não existir
            PosicaoComponente.objects.get_or_create(
                motor=instance,
                nome=nome_slot,
                defaults={'tenant': instance.tenant} # Garante que pertence ao mesmo cliente
            )

    # 1. Cria Slots de Cilindros (Kits)
    if instance.qtd_cilindros:
        for i in range(1, instance.qtd_cilindros + 1):
            # Cria slot para a Vela do cilindro
            PosicaoComponente.objects.get_or_create(
                motor=instance,
                nome=f"Cilindro {i:02d} - Vela",
                defaults={'tenant': instance.tenant}
            )
            # Cria slot para o Bico/Válvula do cilindro (opcional, ajustável conforme necessidade)
            PosicaoComponente.objects.get_or_create(
                motor=instance,
                nome=f"Cilindro {i:02d} - Injetor/Válvula",
                defaults={'tenant': instance.tenant}
            )

    # 2. Cria Slots de Filtros
    garantir_slots("Filtro de Ar", instance.qtd_filtros_ar)
    garantir_slots("Filtro de Combustível", instance.qtd_filtros_gas)
    garantir_slots("Filtro de Óleo", instance.qtd_filtros_oleo)

    # 3. Cria Slots de Ignição (Bobinas e Cabos)
    garantir_slots("Bobina de Ignição", instance.qtd_bobinas)
    garantir_slots("Cabo de Vela", instance.qtd_cabos_vela)

    # 4. Cria Slots de Turbinas
    garantir_slots("Turbina", instance.qtd_turbos)
    
    # 5. Cria Slots de Baterias e Arranque
    garantir_slots("Bateria", instance.qtd_baterias)
    garantir_slots("Motor de Partida", instance.qtd_motores_partida)

    # 6. Blowby (Geralmente é 1 sistema, mas tratamos como slot único)
    if instance.blowby:
        PosicaoComponente.objects.get_or_create(
            motor=instance,
            nome="Sistema de Blowby (Respiro)",
            defaults={'tenant': instance.tenant}
        )