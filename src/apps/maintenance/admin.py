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
        help_text="Segure Ctrl (ou Cmd) para selecionar vários itens. O sistema criará um registro individual para cada um."
    )

    class Meta:
        model = RegistroManutencao
        fields = '__all__'
        exclude = ('posicao',) 

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        queryset = PosicaoComponente.objects.none()

        # 2. Base: Filtro por Tenant
        if self.request:
            user = self.request.user
            # Se for superuser sem tenant, vê tudo. Se tiver tenant, filtra.
            if user.is_superuser and not getattr(user, 'tenant_id', None):
                queryset = PosicaoComponente.objects.all()
            elif getattr(user, 'tenant_id', None):
                queryset = PosicaoComponente.objects.filter(tenant=user.tenant)

        # 3. Refinamento: Filtro por Motor (Contexto)
        motor_id = None
        
        if self.data and self.data.get('motor'):
            try:
                motor_id = int(self.data.get('motor'))
            except (ValueError, TypeError):
                pass
        
        elif self.instance and self.instance.pk and self.instance.motor_id:
            motor_id = self.instance.motor_id
            
        elif self.request and self.request.GET.get('motor'):
            try:
                motor_id = int(self.request.GET.get('motor'))
            except (ValueError, TypeError):
                pass

        if motor_id:
            queryset = queryset.filter(motor_id=motor_id)

        self.fields['selecao_multipla'].queryset = queryset


@admin.register(RegistroManutencao)
class RegistroManutencaoAdmin(TenantModelAdmin):
    form = RegistroManutencaoForm
    list_display = ('data_ocorrencia', 'motor', 'posicao', 'tipo_atividade', 'quantidade_utilizada')
    list_filter = ('tipo_atividade', 'motor')
    search_fields = ('motor__nome', 'posicao__nome', 'observacao')
    
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
        FormClass = super().get_form(request, obj, **kwargs)

        class RequestForm(FormClass):
            def __init__(self, *args, **kwargs):
                kwargs['request'] = request
                super().__init__(*args, **kwargs)

        return RequestForm

    def save_model(self, request, obj, form, change):
        # 1. Estratégia de Definição do Tenant (CORRIGIDO)
        # Se o objeto ainda não tem tenant_id (ID numérico)...
        if not obj.tenant_id:
            
            # Opção A: Pega do Usuário Logado (Padrão)
            if getattr(request.user, 'tenant_id', None):
                obj.tenant_id = request.user.tenant_id
            
            # Opção B: Pega do Motor Selecionado (Salvação para Superusuário)
            # Se eu escolhi um motor, esse motor TEM um tenant. Copiamos dele.
            elif obj.motor:
                # obj.motor é seguro aqui pois é obrigatório no form
                obj.tenant_id = obj.motor.tenant_id

        # Nota: Removemos a checagem 'obj.tenant' que causava o erro 500.
        # Agora confiamos apenas no tenant_id preenchido acima.

        # 2. Pega os itens selecionados
        componentes = form.cleaned_data.get('selecao_multipla')
        
        # Se NÃO selecionou múltiplos componentes, salva normal (Edição ou Único)
        if not componentes:
            if obj.pk or obj.posicao_id:
                obj.save()
            return

        # 3. Lógica da Multiplicação (Explosão de Registros)
        qtd_individual = obj.quantidade_utilizada
        
        # Prepara dados para clonagem usando IDs seguros
        dados_base = {
            'tenant_id': obj.tenant_id,  # Usa o ID resolvido no passo 1
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
                obj.posicao = componente
                obj.save() # Salva o registro "pai/primeiro"
                primeiro = False
            else:
                RegistroManutencao.objects.create(
                    posicao=componente,
                    **dados_base
                )