from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from src.apps.core.admin import TenantModelAdmin
from .models import (
    GrupoComponente, 
    PosicaoComponente, 
    PlanoPreventiva,
    MenuOleo, MenuFiltros, MenuPerifericos, 
    MenuIgnicao, MenuCilindros, MenuCabecotes, MenuOutros
)

# --- 1. Inline para cadastrar preventivas dentro do Item ---
class PlanoPreventivaInline(admin.TabularInline):
    model = PlanoPreventiva
    extra = 0
    fields = ('tarefa', 'tipo_servico', 'unidade', 'intervalo_valor', 'ultima_execucao_data', 'ultima_execucao_valor')
    classes = ('collapse',) # Deixa recolhido para não poluir

# --- 2. Configuração Base para todos os Menus ---
class ComponenteBaseAdmin(TenantModelAdmin):
    list_display = ('nome', 'motor', 'horas_uso_atual', 'exibir_alertas_visual', 'acessar_dashboard')
    list_filter = ('motor', 'grupo')
    search_fields = ('nome', 'serial_number')
    
    # Adiciona a tabelinha de preventivas na tela de edição também
    inlines = [PlanoPreventivaInline]

    # --- O BOTÃO MÁGICO QUE VOCÊ QUERIA ---
    def acessar_dashboard(self, obj):
        # Gera o link para a página que criamos (posicaocomponente_detail)
        url = reverse('components:posicaocomponente_detail', args=[obj.id])
        return format_html(
            '<a class="button" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;" href="{}">📊 Ver Status / Preventivas</a>',
            url
        )
    acessar_dashboard.short_description = "Painel de Manutenção"
    acessar_dashboard.allow_tags = True

    # Coluna de Alertas Visuais (Bolinhas Coloridas na lista)
    def exibir_alertas_visual(self, obj):
        alertas = obj.status_preventivas
        if not alertas:
            return format_html('<span style="color: green;">✔ Em dia</span>')
        
        html = ""
        for alerta in alertas:
            cor = "red" if "VENCIDO" in alerta else "orange"
            html += f'<div style="color: {cor}; font-weight: bold; font-size: 11px;">• {alerta}</div>'
        return format_html(html)
    exibir_alertas_visual.short_description = "Situação Atual"

# --- 3. Registro dos Menus (Proxies) ---

@admin.register(MenuOleo)
class MenuOleoAdmin(ComponenteBaseAdmin):
    pass

@admin.register(MenuFiltros)
class MenuFiltrosAdmin(ComponenteBaseAdmin):
    pass

@admin.register(MenuPerifericos)
class MenuPerifericosAdmin(ComponenteBaseAdmin):
    pass

@admin.register(MenuIgnicao)
class MenuIgnicaoAdmin(ComponenteBaseAdmin):
    pass

@admin.register(MenuCilindros)
class MenuCilindrosAdmin(ComponenteBaseAdmin):
    pass

@admin.register(MenuCabecotes)
class MenuCabecotesAdmin(ComponenteBaseAdmin):
    pass

@admin.register(MenuOutros)
class MenuOutrosAdmin(ComponenteBaseAdmin):
    pass

# --- 4. Outros Cadastros ---
@admin.register(GrupoComponente)
class GrupoComponenteAdmin(TenantModelAdmin):
    list_display = ('nome', 'motor', 'ordem')
    list_filter = ('motor',)