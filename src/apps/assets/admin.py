from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q
from src.apps.core.admin import TenantModelAdmin
from .models import Motor, PosicaoComponente, MarcaMotor, ModeloMotor, SistemaOleo, Periferico

@admin.register(MarcaMotor)
class MarcaMotorAdmin(TenantModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(ModeloMotor)
class ModeloMotorAdmin(TenantModelAdmin):
    list_display = ('nome', 'marca')
    search_fields = ('nome', 'marca__nome')
    autocomplete_fields = ['marca']

@admin.register(Motor)
class MotorAdmin(TenantModelAdmin):
    autocomplete_fields = ['modelo']
    list_display = ('nome', 'get_marca_modelo', 'horas_totais', 'ver_componentes_link', 'em_operacao')
    list_filter = ('modelo__marca', 'em_operacao')
    search_fields = ('nome', 'modelo__nome', 'numero_serie')
    
    fieldsets = (
        ('Identificação', {'fields': ('nome', 'modelo', 'numero_serie', 'localizacao')}),
        ('Horímetros', {'fields': ('horas_totais', 'total_arranques', 'em_operacao')}),
        ('Categoria: Óleo', {'fields': ('qtd_filtros_oleo', 'qtd_trocadores_oleo')}),
        ('Categoria: Periféricos', {'fields': (
            'qtd_turbos', 'qtd_blowby', 'qtd_motores_partida', 'qtd_intercoolers', 'qtd_alternadores',
            'qtd_dampers', 'qtd_compensadores', 'qtd_resistencias', 'qtd_bypass', 
            'qtd_filtros_ar', 'qtd_pre_filtros_ar', 'qtd_filtros_gas'
        )}),
        ('Outros', {'fields': ('qtd_cilindros', 'potencia_nominal', 'qtd_baterias', 'qtd_bobinas', 'qtd_cabos_vela')}),
    )

    def get_marca_modelo(self, obj): return f"{obj.modelo.marca.nome} - {obj.modelo.nome}"
    def ver_componentes_link(self, obj):
        url = reverse('admin:assets_posicaocomponente_changelist') + f'?motor__id__exact={obj.id}'
        return format_html('<a class="button" href="{}">🔧 Ver Peças</a>', url)
    class Media: js = ('js/mascaras.js',)


# --- ADMIN GERAL (Esconde Óleo e Periféricos) ---
@admin.register(PosicaoComponente)
class PosicaoAdmin(TenantModelAdmin):
    list_display = ('nome', 'motor', 'peca_instalada', 'exibir_horas_uso')
    list_filter = ('motor',)
    search_fields = ('nome', 'serial_number')
    autocomplete_fields = ['peca_instalada']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Esconde o que já está nas outras abas
        exclude_terms = ["Óleo", "Turbo", "Blowby", "Arranque", "Intercooler", "Alternador", "Damper", "Compensador", "Resistência", "Filtro de Ar", "Filtro de Gás", "Pré-Filtro", "Bypass"]
        for term in exclude_terms:
            qs = qs.exclude(nome__icontains=term)
        return qs

    def exibir_horas_uso(self, obj): return f"{obj.horas_uso_atual} h"


# --- ABA 1: ÓLEO ---
@admin.register(SistemaOleo)
class SistemaOleoAdmin(TenantModelAdmin):
    list_display = ('nome', 'motor', 'serial_number', 'data_instalacao', 'horas_uso_display')
    list_filter = ('motor',)
    search_fields = ('nome', 'serial_number')
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(nome__icontains="Óleo")
    
    def has_add_permission(self, request): return False
    @admin.display(description="Horas Operação")
    def horas_uso_display(self, obj): return f"{obj.horas_uso_atual} h"


# --- ABA 2: PERIFÉRICOS ---
@admin.register(Periferico)
class PerifericoAdmin(TenantModelAdmin):
    """
    Exibe: Turbo, Blowby, Motor de arranque, Intercooler, Alternador, 
    Dampers, Compensadores, Resistência, Filtros (Ar/Gás/Pré), Bypass.
    """
    list_display = ('nome', 'motor', 'serial_number', 'data_instalacao', 'horas_uso_display')
    list_filter = ('motor',)
    search_fields = ('nome', 'serial_number')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Filtra usando uma busca ampla para pegar todos os itens da lista
        terms = [
            "Turbo", "Blowby", "Arranque", "Intercooler", "Alternador", 
            "Damper", "Compensador", "Resistência", "Filtro de Ar", 
            "Filtro de Gás", "Pré-Filtro", "Bypass"
        ]
        # Monta uma query OR (Termo1 OU Termo2 OU Termo3...)
        query = Q()
        for term in terms:
            query |= Q(nome__icontains=term)
        
        return qs.filter(query)

    def has_add_permission(self, request): return False
    @admin.display(description="Horas Operação")
    def horas_uso_display(self, obj): return f"{obj.horas_uso_atual} h"