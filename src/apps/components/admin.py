from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponseRedirect
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

# --- NOVO: Formulário para a Ação em Massa ---
class PreventivaMassaForm(forms.ModelForm):
    class Meta:
        model = PlanoPreventiva
        fields = ['tarefa', 'tipo_servico', 'unidade', 'intervalo_valor']
        help_texts = {
            'tipo_servico': 'Qual serviço no diário zera este contador?',
            'intervalo_valor': 'Ex: 500 (se for Horas), 6 (se for Meses)'
        }

# --- 2. Configuração Base para todos os Menus ---
class ComponenteBaseAdmin(TenantModelAdmin):
    list_display = ('nome', 'motor', 'horas_uso_atual', 'exibir_alertas_visual', 'acessar_dashboard')
    list_filter = ('motor', 'grupo')
    search_fields = ('nome', 'serial_number')
    
    # Adiciona a tabelinha de preventivas na tela de edição também
    inlines = [PlanoPreventivaInline]

    # --- NOVA AÇÃO REGISTRADA ---
    actions = ['adicionar_preventiva_em_massa']

    # --- LÓGICA DA AÇÃO EM MASSA ---
    @admin.action(description="➕ Adicionar Plano de Preventiva (Massa)")
    def adicionar_preventiva_em_massa(self, request, queryset):
        # Se o formulário foi enviado (Clicou em "Confirmar" na tela intermediária)
        if 'apply' in request.POST:
            form = PreventivaMassaForm(request.POST)
            if form.is_valid():
                tarefa = form.cleaned_data['tarefa']
                tipo = form.cleaned_data['tipo_servico']
                unidade = form.cleaned_data['unidade']
                intervalo = form.cleaned_data['intervalo_valor']
                
                count = 0
                for item in queryset:
                    # Cria o plano para cada item selecionado
                    # Usa o tenant do próprio item para garantir consistência
                    tenant_id = item.tenant_id if hasattr(item, 'tenant_id') else request.user.tenant_id

                    PlanoPreventiva.objects.create(
                        tenant_id=tenant_id, 
                        posicao=item,
                        tarefa=tarefa,
                        tipo_servico=tipo,
                        unidade=unidade,
                        intervalo_valor=intervalo,
                        ultima_execucao_valor=0 # Começa zerado
                    )
                    count += 1
                
                self.message_user(request, f"Sucesso! Plano '{tarefa}' criado para {count} componentes.")
                return HttpResponseRedirect(request.get_full_path())
        
        # Se é a primeira vez (Clicou na Ação), exibe o formulário intermediário
        else:
            form = PreventivaMassaForm()

        return render(request, 'admin/components/adicionar_preventiva_massa.html', {
            'itens': queryset,
            'form': form,
            'title': 'Definir Preventiva em Massa'
        })

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