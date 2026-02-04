from django.db.models.signals import post_save
from django.dispatch import receiver
from src.apps.assets.models import Motor
from src.apps.components.models import PosicaoComponente, GrupoComponente

@receiver(post_save, sender=Motor)
def criar_estrutura_inicial_motor(sender, instance, created, **kwargs):
    if not created: return

    # --- Helpers ---
    def get_grupo(nome, slug, ordem):
        g, _ = GrupoComponente.objects.get_or_create(
            tenant=instance.tenant, motor=instance, slug=slug,
            defaults={'nome': nome, 'ordem': ordem}
        )
        return g

    def criar_itens(grupo_obj, nome_base, quantidade):
        if not quantidade or quantidade <= 0: return
        itens = []
        for i in range(1, quantidade + 1):
            nome_final = f"{nome_base} #{i}" if quantidade > 1 else nome_base
            itens.append(PosicaoComponente(
                tenant=instance.tenant, motor=instance, grupo=grupo_obj,
                nome=nome_final, hora_motor_instalacao=instance.horas_totais
            ))
        PosicaoComponente.objects.bulk_create(itens)

    # 1. SISTEMA DE ÓLEO
    gp_oleo = get_grupo("Sistema de Óleo", "oleo", 10)
    criar_itens(gp_oleo, "Óleo Lubrificante", 1) # <--- FIXO (Default 1)
    criar_itens(gp_oleo, "Filtro de Óleo", instance.qtd_filtros_oleo)
    criar_itens(gp_oleo, "Trocador de Calor", instance.qtd_trocadores_oleo)

    # 2. PERIFÉRICOS
    gp_perif = get_grupo("Periféricos", "perifericos", 30)
    criar_itens(gp_perif, "Turbo", instance.qtd_turbos)
    criar_itens(gp_perif, "Intercooler", instance.qtd_intercoolers)
    criar_itens(gp_perif, "Alternador", instance.qtd_alternadores)
    criar_itens(gp_perif, "Damper", instance.qtd_dampers)
    criar_itens(gp_perif, "Compensador de Escape", instance.qtd_compensadores)
    criar_itens(gp_perif, "Resistência de Aquec.", instance.qtd_resistencias)
    criar_itens(gp_perif, "Válvula Bypass", instance.qtd_bypass)

    # 3. FILTROS
    gp_filtros = get_grupo("Filtros", "filtros", 20)
    criar_itens(gp_filtros, "Filtro de Ar", instance.qtd_filtros_ar)
    criar_itens(gp_filtros, "Pré-Filtro de Ar", instance.qtd_pre_filtros_ar)
    criar_itens(gp_filtros, "Filtro de Gás", instance.qtd_filtros_gas)

    # 4. CILINDROS (Agora detalhado e incluindo VELAS)
    gp_cilindros = get_grupo("Cilindros", "cilindros", 40)
    criar_itens(gp_cilindros, "Pistão", instance.qtd_pistoes)
    criar_itens(gp_cilindros, "Camisa", instance.qtd_camisas)
    criar_itens(gp_cilindros, "Bronzina", instance.qtd_bronzinas)
    criar_itens(gp_cilindros, "Biela", instance.qtd_bielas)
    criar_itens(gp_cilindros, "Vela de Ignição", instance.qtd_velas)

    # 5. IGNIÇÃO (Sem velas)
    gp_ignicao = get_grupo("Ignição", "ignicao", 50)
    criar_itens(gp_ignicao, "Bobina", instance.qtd_bobinas)
    criar_itens(gp_ignicao, "Cabo de Vela", instance.qtd_cabos_vela)
    criar_itens(gp_ignicao, "Bateria", instance.qtd_baterias)
    criar_itens(gp_ignicao, "Motor de Arranque", instance.qtd_motores_partida)

    # Extras (Cabeçotes, se quiser manter a lógica de 1 por cilindro)
    gp_cabecotes = get_grupo("Cabeçotes", "cabecotes", 60)
    criar_itens(gp_cabecotes, "Cabeçote", instance.qtd_cilindros)