from django import forms
from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin
from src.apps.components.models import PosicaoComponente
from .models import RegistroManutencao

# --- FORMULÁRIO PERSONALIZADO ---
class RegistroManutencaoForm(forms.ModelForm):
    # Campo virtual para seleção múltipla na interface
    selecao_multipla = forms.ModelMultipleChoiceField(
        queryset=PosicaoComponente.objects.none(), # Inicializa vazio, preenchemos no __init__
        required=False, # Opcional, pois na edição pode não ser usado
        label="Selecione os Componentes",
        widget=admin.widgets.FilteredSelectMultiple("Componentes", is_stacked=False),
        help_text="Segure Ctrl (ou Cmd) para selecionar vários itens. O sistema criará um registro individual para cada um."
    )

    class Meta:
        model = RegistroManutencao
        fields = '__all__'
        # Escondemos o campo real 'posicao', o script vai preencher no save
        exclude = ('posicao',) 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se tivermos acesso ao request (passado pelo Admin), filtramos pelo Tenant
        if hasattr(self, 'request'):
            self.fields['selecao_multipla'].queryset = PosicaoComponente.objects.filter(
                tenant=self.request.user.tenant
            )

@admin.register(RegistroManutencao)
class RegistroManutencaoAdmin(TenantModelAdmin):
    form = RegistroManutencaoForm
    list_display = ('data_ocorrencia', 'motor', 'posicao', 'tipo_atividade', 'quantidade_utilizada')
    list_filter = ('tipo_atividade', 'motor')
    search_fields = ('motor__nome', 'posicao__nome', 'observacao')
    
    # 'posicao' foi removido do autocomplete pois agora é gerado via script
    autocomplete_fields = ['motor', 'item_estoque'] 

    fieldsets = (
        ('1. Contexto', {
            'fields': ('data_ocorrencia', 'motor', 'horimetro_na_execucao', 'arranques_na_execucao')
        }),
        ('2. Seleção de Componentes', {
            'fields': ('selecao_multipla', 'tipo_atividade', 'novo_serial_number'),
            'description': 'Selecione todas as peças que sofreram manutenção. Será gerado um registro para cada.'
        }),
        ('3. Estoque (Por Peça)', {
            'fields': ('item_estoque', 'quantidade_utilizada'),
            'description': 'Informe a quantidade gasta PER CAPITA (por peça). Ex: se trocou 1 anel em cada pistão, coloque 1.'
        }),
        ('4. Detalhes', {
            'fields': ('responsavel', 'observacao')
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        # Injeta o request no formulário para podermos filtrar o QuerySet pelo Tenant
        Form = super().get_form(request, obj, **kwargs)
        Form.request = request
        return Form

    def save_model(self, request, obj, form, change):
        # 1. CORREÇÃO DO ERRO: Garantir que o Tenant está preenchido
        if not obj.tenant_id:
            obj.tenant = request.user.tenant

        # 2. Pega os itens selecionados no campo virtual
        componentes = form.cleaned_data.get('selecao_multipla')
        
        # Se for uma edição simples ou não tiver seleção múltipla, salva o objeto original e sai
        if not componentes:
            # Se já tem posição (edição), salva normal
            if obj.pk or obj.posicao_id:
                obj.save()
            return

        # 3. Lógica da Multiplicação (Explosão de Registros)
        qtd_individual = obj.quantidade_utilizada
        
        # Dicionário com os dados base para clonagem
        dados_base = {
            'tenant': obj.tenant,
            'data_ocorrencia': obj.data_ocorrencia,
            'motor': obj.motor,
            'horimetro_na_execucao': obj.horimetro_na_execucao,
            'arranques_na_execucao': obj.arranques_na_execucao,
            'tipo_atividade': obj.tipo_atividade,
            'item_estoque': obj.item_estoque,
            'quantidade_utilizada': qtd_individual,
            'responsavel': obj.responsavel,
            'observacao': obj.observacao,
            'novo_serial_number': obj.novo_serial_number
        }

        primeiro = True
        for componente in componentes:
            if primeiro:
                # Na primeira iteração, usamos o objeto 'obj' que o Django já instanciou
                obj.posicao = componente
                obj.save() # Salva o registro "pai/primeiro"
                primeiro = False
            else:
                # Nas próximas, criamos novos registros (Clones)
                RegistroManutencao.objects.create(
                    posicao=componente,
                    **dados_base
                )