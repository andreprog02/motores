from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from src.apps.core.admin import TenantModelAdmin
from .models import Motor, MarcaMotor, ModeloMotor

@admin.register(MarcaMotor)
class MarcaMotorAdmin(TenantModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(ModeloMotor)
class ModeloMotorAdmin(TenantModelAdmin):
    # IMPORTANTE: search_fields é obrigatório aqui para o autocomplete_fields do Motor funcionar
    list_display = ('nome', 'marca')
    search_fields = ('nome', 'marca__nome') 
    autocomplete_fields = ['marca']

@admin.register(Motor)
class MotorAdmin(TenantModelAdmin):
    autocomplete_fields = ['modelo']
    list_display = ('nome', 'modelo', 'horas_totais', 'ver_componentes_link', 'em_operacao')
    list_filter = ('modelo__marca', 'em_operacao')
    search_fields = ('nome', 'modelo__nome')
    
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'modelo', 'numero_serie', 'localizacao', 'em_operacao')
        }),
        ('Sistema de Óleo', {
            'fields': ('qtd_filtros_oleo', 'qtd_trocadores_oleo'),
            'description': 'O item "Óleo Lubrificante" será criado automaticamente.'
        }),
        ('Periféricos', {
            'fields': (
                'qtd_turbos', 'qtd_intercoolers', 'qtd_alternadores', 
                'qtd_dampers', 'qtd_compensadores', 'qtd_resistencias', 'qtd_bypass'
            )
        }),
        ('Filtros', {
            'fields': ('qtd_filtros_ar', 'qtd_pre_filtros_ar', 'qtd_filtros_gas')
        }),
        ('Cilindros e Componentes Internos', {
            'fields': (
                'qtd_cilindros', 
                'qtd_pistoes', 'qtd_camisas', 'qtd_bronzinas', 'qtd_bielas', 'qtd_velas'
            ),
            'description': 'Se deixar 0, o sistema usará a quantidade de cilindros como padrão.'
        }),
        ('Ignição e Partida', {
            'fields': ('qtd_bobinas', 'qtd_cabos_vela', 'qtd_baterias', 'qtd_motores_partida')
        }),
        ('Horímetros Iniciais', {
            'fields': ('horas_totais', 'total_arranques')
        }),
    )

    def ver_componentes_link(self, obj):
        # Gera o link para a tela de Categorias filtrada por este motor
        url = reverse('admin:components_grupocomponente_changelist') + f'?motor__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">📂 Categorias</a>', url)
    ver_componentes_link.short_description = "Gestão"