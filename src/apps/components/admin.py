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
    extra = 1  # Mudei para 1 para facilitar a adição rápida
    fields = ('tarefa', 'tipo_servico', 'unidade', 'intervalo_valor', 'ultima_execucao_data', 'ultima_execucao_valor')
    classes = ('collapse',) 

# --- NOVO: Formulário para a Ação em Massa ---
class PreventivaMassaForm(forms.ModelForm):
    class Meta:
        model = PlanoPreventiva
        fields = ['tarefa', 'tipo_servico', 'unidade', 'intervalo_valor']
        help_texts = {
            'tipo_servico': 'Qual serviço no diário zera este contador?',
            'intervalo_valor': 'Ex: 500 (se for Horas), 6 (se for Meses)'
        }

# --- 2. Configuração Base (AGORA HÍBRIDA: MOTOR E EQUIPAMENTO) ---
class ComponenteBaseAdmin(TenantModelAdmin):
    # Alterado: Trocamos 'motor' por 'get_ativo_pai' para mostrar o dono correto
    list_display = ('nome', 'get_ativo_pai', 'horas_uso_atual', 'exibir_alertas_visual', 'acessar_dashboard')
    
    # Alterado: Adicionado filtro por Equipamento
    list_filter = ('motor', 'equipamento', 'grupo') 
    
    search_fields = ('nome', 'serial_number', 'motor__nome', 'equipamento__nome')
    
    inlines = [PlanoPreventivaInline]
    actions = ['adicionar_preventiva_em_massa']

    # --- Coluna Inteligente: Mostra Motor ou Equipamento ---
    def get_ativo_pai(self, obj):
        if obj.motor:
            return f"Ⓜ️ {obj.motor.nome}"
        if obj.equipamento:
            return f"⚙️ {obj.equipamento.nome}"
        return "-"
    get_ativo_pai.short_description = "Pertence a"
    get_ativo_pai.admin_order_field = 'motor__nome'

    # --- LÓGICA DA AÇÃO EM MASSA (Mantida) ---
    @admin.action(description="➕ Adicionar Plano de Preventiva (Massa)")
    def adicionar_preventiva_em_massa(self, request, queryset):
        if 'apply' in request.POST:
            form = PreventivaMassaForm(request.POST)
            if form.is_valid():
                tarefa = form.cleaned_data['tarefa']
                tipo = form.cleaned_data['tipo_servico']
                unidade = form.cleaned_data['unidade']
                intervalo = form.cleaned_data['intervalo_valor']
                
                count = 0
                for item in queryset:
                    tenant_id = item.tenant_id if hasattr(item, 'tenant_id') else request.user.tenant_id

                    PlanoPreventiva.objects.create(
                        tenant_id=tenant_id, 
                        posicao=item,
                        tarefa=tarefa,
                        tipo_servico=tipo,
                        unidade=unidade,
                        intervalo_valor=intervalo,
                        ultima_execucao_valor=0 
                    )
                    count += 1
                
                self.message_user(request, f"Sucesso! Plano '{tarefa}' criado para {count} componentes.")
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = PreventivaMassaForm()

        return render(request, 'admin/components/adicionar_preventiva_massa.html', {
            'itens': queryset,
            'form': form,
            'title': 'Definir Preventiva em Massa'
        })

    def acessar_dashboard(self, obj):
        # Gera o link para a página de detalhes (certifique-se que essa URL existe)
        # Se der erro, pode comentar temporariamente ou criar a URL
        try:
            url = reverse('components:posicaocomponente_detail', args=[obj.id])
            return format_html(
                '<a class="button" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;" href="{}">📊 Ver Status</a>',
                url
            )
        except:
            return "-"
    acessar_dashboard.short_description = "Painel"
    acessar_dashboard.allow_tags = True

    def exibir_alertas_visual(self, obj):
        alertas = obj.status_preventivas
        if not alertas:
            return format_html('<span style="color: green;">✔ OK</span>')
        
        html = ""
        for alerta in alertas:
            cor = "red" if "VENCIDO" in alerta else "orange"
            html += f'<div style="color: {cor}; font-weight: bold; font-size: 11px;">• {alerta}</div>'
        return format_html(html)
    exibir_alertas_visual.short_description = "Status"

# --- 3. Registro dos Menus ---

# IMPORTANTE: Registramos a classe PRINCIPAL para ver peças de Equipamentos
# que talvez não se encaixem nos menus de motor (Filtros, Cilindros, etc)
@admin.register(PosicaoComponente)
class PosicaoComponenteAdmin(ComponenteBaseAdmin):
    verbose_name = "Todos os Componentes"

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
    # Adicionamos equipamento aqui também
    list_display = ('nome', 'motor', 'equipamento', 'ordem')
    list_filter = ('motor', 'equipamento')