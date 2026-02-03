from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from src.apps.core.admin import TenantModelAdmin
from .models import Motor, PosicaoComponente

@admin.register(Motor)
class MotorAdmin(TenantModelAdmin):
    list_display = ('nome', 'modelo', 'horas_totais', 'ver_componentes_link')
    #readonly_fields = ('horas_totais', 'total_arranques')

    def ver_componentes_link(self, obj):
        # Cria um botão que leva para a lista de peças filtrada por esse motor
        url = reverse('admin:assets_posicaocomponente_changelist') + f'?motor__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">🔧 Ver Peças Instaladas</a>', url)
    
    ver_componentes_link.short_description = "Componentes"

@admin.register(PosicaoComponente)
class PosicaoAdmin(TenantModelAdmin):
    # Trocamos 'horas_uso_atual' por 'exibir_horas_uso'
    list_display = ('nome', 'motor', 'peca_instalada', 'exibir_horas_uso')
    list_filter = ('motor', 'peca_instalada')
    search_fields = ('nome', 'serial_number')
    autocomplete_fields = ['peca_instalada']

    def exibir_horas_uso(self, obj):
        """
        Força o Admin a calcular: Horas do Motor - Horas na Instalação.
        """
        valor = obj.horas_uso_atual
        return f"{valor:.1f} h" # Formata com uma casa decimal
    
    exibir_horas_uso.short_description = "Uso Atual"