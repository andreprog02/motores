from django import forms
from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin
from src.apps.components.models import PosicaoComponente
from .models import RegistroManutencao

# --- FORMULÁRIO PERSONALIZADO ---
class RegistroManutencaoForm(forms.ModelForm):
    selecao_multipla = forms.ModelMultipleChoiceField(
        queryset=PosicaoComponente.objects.none(),
        required=False, 
        label="Selecione os Componentes",
        widget=admin.widgets.FilteredSelectMultiple("Componentes", is_stacked=False),
        help_text="Segure Ctrl (ou Cmd) para selecionar vários itens."
    )

    class Meta:
        model = RegistroManutencao
        fields = '__all__'
        exclude = ('posicao',) 

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        queryset = PosicaoComponente.objects.none()

        # 1. Filtro Base por Tenant
        if self.request:
            user = self.request.user
            if user.is_superuser and not getattr(user, 'tenant_id', None):
                queryset = PosicaoComponente.objects.all()
            elif getattr(user, 'tenant_id', None):
                queryset = PosicaoComponente.objects.filter(tenant=user.tenant)

        # 2. Identificação do Contexto (Motor OU Equipamento)
        motor_id = None
        equipamento_id = None
        
        # Tenta pegar dos dados POST (se deu erro de validação e recarregou)
        if self.data:
            motor_id = self.data.get('motor')
            equipamento_id = self.data.get('equipamento')
        
        # Tenta pegar da instância (edição)
        elif self.instance and self.instance.pk:
            motor_id = self.instance.motor_id
            equipamento_id = self.instance.equipamento_id
            
        # Tenta pegar da URL (se veio filtrado de outra tela)
        elif self.request:
            motor_id = self.request.GET.get('motor')
            equipamento_id = self.request.GET.get('equipamento')

        # 3. Aplica o Filtro no Queryset de Componentes
        if motor_id:
            try:
                queryset = queryset.filter(motor_id=int(motor_id))
            except (ValueError, TypeError): pass
            
        elif equipamento_id:
            try:
                queryset = queryset.filter(equipamento_id=int(equipamento_id))
            except (ValueError, TypeError): pass

        self.fields['selecao_multipla'].queryset = queryset


@admin.register(RegistroManutencao)
class RegistroManutencaoAdmin(TenantModelAdmin):
    form = RegistroManutencaoForm
    # Adicionado equipamento na lista
    list_display = ('data_ocorrencia', 'get_ativo', 'posicao', 'tipo_atividade', 'quantidade_utilizada')
    list_filter = ('tipo_atividade', 'motor', 'equipamento')
    search_fields = ('motor__nome', 'equipamento__nome', 'posicao__nome', 'observacao')
    
    autocomplete_fields = ['motor', 'equipamento', 'item_estoque'] 

    fieldsets = (
        ('1. Contexto (Selecione UM)', {
            'fields': (
                'data_ocorrencia', 
                ('motor', 'equipamento'), # Lado a lado
                ('horimetro_na_execucao', 'arranques_na_execucao')
            ),
            'description': 'Escolha o Motor OU o Equipamento onde a manutenção ocorreu.'
        }),
        ('2. Seleção de Componentes', {
            'fields': ('selecao_multipla', 'tipo_atividade', 'novo_serial_number'),
            'description': 'Selecione todas as peças que sofreram manutenção.'
        }),
        ('3. Estoque (Por Peça)', {
            'fields': ('item_estoque', 'quantidade_utilizada'),
            'description': 'Informe a quantidade gasta PER CAPITA (por peça).'
        }),
        ('4. Detalhes', {
            'fields': ('responsavel', 'observacao')
        }),
    )

    def get_ativo(self, obj):
        return obj.motor if obj.motor else obj.equipamento
    get_ativo.short_description = "Ativo"

    def get_form(self, request, obj=None, **kwargs):
        FormClass = super().get_form(request, obj, **kwargs)
        class RequestForm(FormClass):
            def __init__(self, *args, **kwargs):
                kwargs['request'] = request
                super().__init__(*args, **kwargs)
        return RequestForm

    def save_model(self, request, obj, form, change):
        # 1. Definição do Tenant
        if not obj.tenant_id:
            if getattr(request.user, 'tenant_id', None):
                obj.tenant_id = request.user.tenant_id
            elif obj.motor:
                obj.tenant_id = obj.motor.tenant_id
            elif obj.equipamento:
                obj.tenant_id = obj.equipamento.tenant_id

        # 2. Pega os itens selecionados
        componentes = form.cleaned_data.get('selecao_multipla')
        
        # Se NÃO selecionou múltiplos componentes, salva normal (Edição ou Único)
        if not componentes:
            if obj.pk or obj.posicao_id:
                obj.save()
            return

        # 3. Lógica da Multiplicação (Explosão de Registros)
        qtd_individual = obj.quantidade_utilizada
        
        dados_base = {
            'tenant_id': obj.tenant_id,
            'data_ocorrencia': obj.data_ocorrencia,
            'motor': obj.motor,
            'equipamento': obj.equipamento, # Importante passar o equipamento
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
                obj.posicao = componente
                obj.save() 
                primeiro = False
            else:
                RegistroManutencao.objects.create(
                    posicao=componente,
                    **dados_base
                )