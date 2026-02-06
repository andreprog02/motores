from django.db import models
from src.apps.core.models import TenantAwareModel
from src.apps.assets.models import Motor
from src.apps.components.models import PosicaoComponente
from src.apps.inventory.models import EstoqueItem

class RegistroManutencao(TenantAwareModel):
    TIPOS_SERVICO = [
        ('SUBSTITUICAO', 'Substituição (Troca de Peça)'),
        ('INSTALACAO', 'Instalação (Nova Peça)'),
        ('REGULAGEM', 'Regulagem'),
        ('LUBRIFICACAO', 'Lubrificação'),
        ('CALIBRACAO', 'Calibração'),
        ('INSPECAO', 'Inspeção / Rotina'),
        ('CORRETIVA', 'Reparo Corretivo'),
        ('LIMPEZA', 'Limpeza'),
    ]

    # --- 1. IDENTIFICAÇÃO ---
    data_ocorrencia = models.DateField(verbose_name="Data da Ocorrência")
    motor = models.ForeignKey(Motor, on_delete=models.CASCADE, related_name='manutencoes')
    
    # ALTERADO: Voltamos para ForeignKey (1 para 1)
    # Cada linha no banco será referente a UMA peça específica.
    posicao = models.ForeignKey(
        PosicaoComponente, 
        on_delete=models.CASCADE,
        related_name='historico_manutencao',
        verbose_name="Componente Afetado"
    )

    
    # --- 2. DADOS OPERACIONAIS ---
    horimetro_na_execucao = models.IntegerField(
        verbose_name="Horas de Operação (Atual)", 
        help_text="Atualizará o horímetro de todos os componentes selecionados."
    )
    arranques_na_execucao = models.IntegerField(
        verbose_name="Nº de Arranques (Opcional)", 
        null=True, blank=True,
        help_text="Deixe em branco se não quiser alterar."
    )
    tipo_atividade = models.CharField(
        max_length=50, 
        choices=TIPOS_SERVICO,
        default='INSPECAO',
        verbose_name="Tipo de Serviço"
    )

    # --- 3. ESTOQUE ---
    item_estoque = models.ForeignKey(
        EstoqueItem, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name="Item de Estoque (Para Baixa)"
    )
    quantidade_utilizada = models.IntegerField(
        default=0, 
        verbose_name="Quantidade a Baixar"
    )

    # --- 4. DETALHES ---
    responsavel = models.CharField(max_length=100, blank=True, null=True, verbose_name="Responsável")
    observacao = models.TextField(blank=True, null=True, verbose_name="Detalhes / Observações")
    novo_serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Novo Serial (Se houver)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Ocorrência"
        verbose_name_plural = "Livro de Ocorrências"
        ordering = ['-data_ocorrencia']

    def __str__(self):
        return f"{self.data_ocorrencia} - {self.motor} ({self.get_tipo_atividade_display()})"