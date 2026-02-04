from django.contrib import admin
from django.db.models import Q
from src.apps.core.admin import TenantModelAdmin
from .models import PosicaoComponente, SistemaOleo, Periferico

# --- 1. LISTA GERAL ---
@admin.register(PosicaoComponente)
class PosicaoAdmin(TenantModelAdmin):
    list_display = ('nome', 'motor', 'peca_instalada', 'exibir_horas_uso')
    list_filter = ('motor',)
    search_fields = ('nome', 'serial_number')
    autocomplete_fields = ['peca_instalada']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Esconde Óleo e Periféricos desta lista geral
        exclude_terms = ["Óleo", "Turbo", "Blowby", "Arranque", "Intercooler", "Alternador", "Damper", "Compensador", "Resistência", "Filtro de Ar", "Filtro de Gás", "Pré-Filtro", "Bypass"]
        for term in exclude_terms:
            qs = qs.exclude(nome__icontains=term)
        return qs

    def exibir_horas_uso(self, obj): return f"{obj.horas_uso_atual} h"

# --- 2. ÓLEO ---
@admin.register(SistemaOleo)
class SistemaOleoAdmin(TenantModelAdmin):
    list_display = ('nome', 'motor', 'serial_number', 'data_instalacao', 'horas_uso_display')
    list_filter = ('motor',)
    search_fields = ('nome', 'serial_number')
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(nome__icontains="Óleo")
    
    def has_add_permission(self, request): return False
    @admin.display(description="Horas Uso")
    def horas_uso_display(self, obj): return f"{obj.horas_uso_atual} h"

# --- 3. PERIFÉRICOS ---
@admin.register(Periferico)
class PerifericoAdmin(TenantModelAdmin):
    list_display = ('nome', 'motor', 'serial_number', 'horas_uso_display')
    list_filter = ('motor',)
    search_fields = ('nome', 'serial_number')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        terms = ["Turbo", "Blowby", "Arranque", "Intercooler", "Alternador", "Damper", "Compensador", "Resistência", "Filtro de Ar", "Filtro de Gás", "Pré-Filtro", "Bypass"]
        query = Q()
        for term in terms: query |= Q(nome__icontains=term)
        return qs.filter(query)

    def has_add_permission(self, request): return False
    @admin.display(description="Horas Uso")
    def horas_uso_display(self, obj): return f"{obj.horas_uso_atual} h"