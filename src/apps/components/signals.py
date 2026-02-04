from django.db.models.signals import post_save
from django.dispatch import receiver
# Importa Motor de Assets e PosicaoComponente daqui de Components
from src.apps.assets.models import Motor
from src.apps.components.models import PosicaoComponente

@receiver(post_save, sender=Motor)
def criar_componentes_automaticos(sender, instance, created, **kwargs):
    
    def garantir_slots(nome_base, quantidade):
        if not quantidade: return
        for i in range(1, quantidade + 1):
            suffix = f" #{i:02d}" if quantidade > 1 else ""
            PosicaoComponente.objects.get_or_create(
                motor=instance,
                nome=f"{nome_base}{suffix}",
                defaults={'tenant': instance.tenant}
            )

    # Lógica de criação (igual ao anterior)
    garantir_slots("Óleo do Motor (Cárter)", 1)
    garantir_slots("Filtro de Óleo", instance.qtd_filtros_oleo)
    garantir_slots("Trocador de Óleo", instance.qtd_trocadores_oleo)
    
    garantir_slots("Turbo", instance.qtd_turbos)
    garantir_slots("Blowby", instance.qtd_blowby)
    garantir_slots("Motor de Arranque", instance.qtd_motores_partida)
    garantir_slots("Intercooler", instance.qtd_intercoolers)
    garantir_slots("Alternador", instance.qtd_alternadores)
    garantir_slots("Damper", instance.qtd_dampers)
    garantir_slots("Compensador de Escape", instance.qtd_compensadores)
    garantir_slots("Resistência de Aquecimento", instance.qtd_resistencias)
    garantir_slots("Filtro de Ar", instance.qtd_filtros_ar)
    garantir_slots("Filtro de Gás", instance.qtd_filtros_gas)
    garantir_slots("Pré-Filtro de Ar", instance.qtd_pre_filtros_ar)
    garantir_slots("Bypass", instance.qtd_bypass)

    if instance.qtd_cilindros:
        for i in range(1, instance.qtd_cilindros + 1):
            PosicaoComponente.objects.get_or_create(motor=instance, nome=f"Cilindro {i:02d} - Vela", defaults={'tenant': instance.tenant})
            PosicaoComponente.objects.get_or_create(motor=instance, nome=f"Cilindro {i:02d} - Injetor", defaults={'tenant': instance.tenant})

    garantir_slots("Bateria", instance.qtd_baterias)
    garantir_slots("Bobina de Ignição", instance.qtd_bobinas)
    garantir_slots("Cabo de Vela", instance.qtd_cabos_vela)
    garantir_slots("Líquido Refrigerante", 1)