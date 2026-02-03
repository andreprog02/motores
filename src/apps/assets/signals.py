from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Motor, PosicaoComponente

@receiver(post_save, sender=Motor)
def gerar_slots_do_motor(sender, instance, created, **kwargs):
    if created:
        # transaction.on_commit garante que as peças só sejam criadas 
        # DEPOIS que o motor for salvo com sucesso no banco
        transaction.on_commit(lambda: _gerar_peças_bulk(instance))

def _gerar_peças_bulk(instance):
    slots = []
    itens_cilindro = ["Vela", "Pistão", "Cabeçote", "Camisa", "Biela"] # Reduzi para teste rápido
    
    for i in range(1, instance.qtd_cilindros + 1):
        for item in itens_cilindro:
            slots.append(PosicaoComponente(
                tenant=instance.tenant,
                motor=instance,
                nome=f"Cil. {i:02d} - {item}",
                hora_motor_instalacao=instance.horas_totais
            ))
    
    PosicaoComponente.objects.bulk_create(slots)