from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from src.apps.core.admin import TenantModelAdmin
from .models import Motor, MarcaMotor, ModeloMotor

@admin.register(MarcaMotor)
class MarcaMotorAdmin(TenantModelAdmin):
    list_display = ('nome',); search_fields = ('nome',)

@admin.register(ModeloMotor)
class ModeloMotorAdmin(TenantModelAdmin):
    list_display = ('nome', 'marca'); search_fields = ('nome', 'marca__nome'); autocomplete_fields = ['marca']

@admin.register(Motor)
class MotorAdmin(TenantModelAdmin):
    autocomplete_fields = ['modelo']
    list_display = ('nome', 'get_marca_modelo', 'horas_totais', 'ver_componentes_link', 'em_operacao')
    list_filter = ('modelo__marca', 'em_operacao')
    search_fields = ('nome', 'modelo__nome', 'numero_serie')
    fieldsets = (
        ('Identificação', {'fields': ('nome', 'modelo', 'numero_serie', 'localizacao')}),
        ('Horímetros', {'fields': ('horas_totais', 'total_arranques', 'em_operacao')}),
        ('Configurações', {'fields': ('qtd_filtros_oleo', 'qtd_trocadores_oleo', 'qtd_turbos', 'qtd_intercoolers', 'qtd_alternadores', 'qtd_dampers', 'qtd_compensadores', 'qtd_resistencias', 'qtd_bypass', 'qtd_filtros_ar', 'qtd_pre_filtros_ar', 'qtd_filtros_gas')}),
    )
    def get_marca_modelo(self, obj): return f"{obj.modelo.marca.nome} - {obj.modelo.nome}"
    def ver_componentes_link(self, obj):
        # Aponta para a nova app 'components'
        url = reverse('admin:components_posicaocomponente_changelist') + f'?motor__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">🔧 Ver Peças</a>', url)