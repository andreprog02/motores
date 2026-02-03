from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from src.apps.core.admin import TenantModelAdmin
from .models import Motor, PosicaoComponente, MarcaMotor, ModeloMotor

@admin.register(MarcaMotor)
class MarcaMotorAdmin(TenantModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(ModeloMotor)
class ModeloMotorAdmin(TenantModelAdmin):
    list_display = ('nome', 'marca')
    list_filter = ('marca',)
    search_fields = ('nome', 'marca__nome')
    # Cria o combobox pesquisável para selecionar a marca
    autocomplete_fields = ['marca']

@admin.register(Motor)
class MotorAdmin(TenantModelAdmin):
    # Adicionamos 'modelo' ao autocomplete para funcionar a busca inteligente
    autocomplete_fields = ['modelo']
    
    # Mantive suas customizações originais
    list_display = ('nome', 'get_marca_modelo', 'horas_totais', 'ver_componentes_link')
    list_filter = ('modelo__marca', 'em_operacao')
    search_fields = ('nome', 'modelo__nome', 'numero_serie')
    
    #readonly_fields = ('horas_totais', 'total_arranques')

    def get_marca_modelo(self, obj):
        return f"{obj.modelo.marca.nome} - {obj.modelo.nome}"
    get_marca_modelo.short_description = "Marca / Modelo"

    def ver_componentes_link(self, obj):
        # Cria um botão que leva para a lista de peças filtrada por esse motor
        url = reverse('admin:assets_posicaocomponente_changelist') + f'?motor__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">🔧 Ver Peças Instaladas</a>', url)
    
    ver_componentes_link.short_description = "Componentes"

    class Media:
        js = ('js/mascaras.js',)

@admin.register(PosicaoComponente)
class PosicaoAdmin(TenantModelAdmin):
    # Mantive exatamente como estava, pois sua lógica está correta
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

    class Media:
        js = ('js/mascaras.js',)
