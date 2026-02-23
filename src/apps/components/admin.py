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
    """
    Permite adicionar os planos de manutenção (ex: Troca a cada 500h)
    diretamente na tela da peça.
    """
    model = PlanoPreventiva
    extra = 1
    fields = ('tarefa', 'tipo_servico', 'unidade', 'intervalo_valor', 'ultima_execucao_data', 'ultima_execucao_valor')
    classes = ('collapse',) # Opcional: Deixa recolhido para economizar espaço

# --- 2. Formulário para a Ação em Massa ---
class PreventivaMassaForm(forms.ModelForm):
    class Meta:
        model = PlanoPreventiva
        fields = ['tarefa', 'tipo_servico', 'unidade', 'intervalo_valor']
        help_texts = {
            'tipo_servico': 'Qual serviço no diário zera este contador?',
            'intervalo_valor': 'Ex: 500 (se for Horas), 6 (se for Meses)'
        }

# --- 3. Configuração Base (Motor + Equipamento) ---
class ComponenteBaseAdmin(TenantModelAdmin):
    # 'get_ativo_pai' substitui a coluna fixa de 'motor' para aceitar equipamentos
    list_display = ('nome', 'get_ativo_pai', 'horas_uso_atual', 'exibir_alertas_visual', 'acessar_dashboard')
    
    # Filtros para ambos os tipos de ativo
    list_filter = ('motor', 'equipamento', 'grupo', 'peca_instalada__categoria') 
    
    search_fields = ('nome', 'serial_number', 'motor__nome', 'equipamento__nome')
    
    inlines = [PlanoPreventivaInline]
    actions = ['adicionar_preventiva_em_massa']

    # --- Organização Visual do Formulário ---
    fieldsets = (
        ('Vínculo e Localização', {
            'fields': (
                ('motor', 'equipamento'), # Exibe lado a lado
                'grupo', 
                'nome', 
                'numero'
            ),
            'description': 'Selecione o Motor OU o Equipamento a que esta peça pertence.'
        }),
        ('Peça Instalada', {
            'fields': ('peca_instalada', 'serial_number', 'data_instalacao')
        }),
        ('Contadores (Snapshot da Instalação)', {
            'fields': ('hora_motor_instalacao', 'arranques_motor_instalacao'),
            'classes': ('collapse',),
            'description': 'Registra o horímetro do ativo no momento da troca.'
        }),
        ('Monitoramento', {
            'fields': ('ultimo_engraxamento', 'ultima_medicao_vibracao'),
            'classes': ('collapse',)
        })
    )

    # --- Coluna Inteligente: Mostra Ícone do Pai ---
    def get_ativo_pai(self, obj):
        if obj.motor:
            return f"Ⓜ️ {obj.motor.nome}"
        if obj.equipamento:
            return f"⚙️ {obj.equipamento.nome}"
        return "-"
    get_ativo_pai.short_description = "Pertence a"
    get_ativo_pai.admin_order_field = 'motor__nome' # Ordenação padrão

    # --- Botão para Dashboard ---
    def acessar_dashboard(self, obj):
        try:
            url = reverse('components:posicaocomponente_detail', args=[obj.id])
            return format_html(
                '<a class="button" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;" href="{}">📊 Ver Status</a>',
                url
            )
        except Exception:
            return "-"
    acessar_dashboard.short_description = "Painel"
    acessar_dashboard.allow_tags = True

    # --- Alertas Visuais (Bolinhas) ---
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

    # --- Lógica da Ação em Massa ---
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

# --- 4. Registro dos Menus ---

# Este é o registro PRINCIPAL para ver tudo (Motores e Equipamentos)
@admin.register(PosicaoComponente)
class PosicaoComponenteAdmin(ComponenteBaseAdmin):
    verbose_name = "Todos os Componentes"

# Proxies (Menus Filtrados) - Mantêm a herança
@admin.register(MenuOleo)
class MenuOleoAdmin(ComponenteBaseAdmin): pass

@admin.register(MenuFiltros)
class MenuFiltrosAdmin(ComponenteBaseAdmin): pass

@admin.register(MenuPerifericos)
class MenuPerifericosAdmin(ComponenteBaseAdmin): pass

@admin.register(MenuIgnicao)
class MenuIgnicaoAdmin(ComponenteBaseAdmin): pass

@admin.register(MenuCilindros)
class MenuCilindrosAdmin(ComponenteBaseAdmin): pass

@admin.register(MenuCabecotes)
class MenuCabecotesAdmin(ComponenteBaseAdmin): pass

@admin.register(MenuOutros)
class MenuOutrosAdmin(ComponenteBaseAdmin): pass

# --- 5. Configuração dos Grupos (Categorias) ---
@admin.register(GrupoComponente)
class GrupoComponenteAdmin(TenantModelAdmin):
    list_display = ('nome', 'motor', 'equipamento', 'ordem')
    list_filter = ('motor', 'equipamento')
    search_fields = ('nome', 'motor__nome', 'equipamento__nome')