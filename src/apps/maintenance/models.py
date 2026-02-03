from django.db import models
from django.conf import settings
from src.apps.core.models import TenantAwareModel
from src.apps.assets.models import Motor, PosicaoComponente
from src.apps.inventory.models import EstoqueItem

class RegistroManutencao(TenantAwareModel):
    TIPO_ATIVIDADE = [
        ('TROCA', 'Substituição de Peça'),
        ('INSPECAO', 'Inspeção / Verificação'),
        ('LUBRIFICACAO', 'Lubrificação / Engraxamento'),
        ('AJUSTE', 'Ajuste / Regulagem'),
        ('FALHA', 'Registro de Falha (Quebra)'),
    ]

    # Quem e Quando
    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    data_ocorrencia = models.DateTimeField()
    criado_em = models.DateTimeField(auto_now_add=True)

    # Onde (Contexto)
    motor = models.ForeignKey(Motor, on_delete=models.PROTECT)
    posicao = models.ForeignKey(PosicaoComponente, on_delete=models.PROTECT, verbose_name="Componente Afetado")
    
    # O que foi feito
    tipo_atividade = models.CharField(max_length=20, choices=TIPO_ATIVIDADE)
    horimetro_na_execucao = models.DecimalField(max_digits=10, decimal_places=2, help_text="Horas do motor no momento da ação")
    
    # Se houve troca de peça
    item_estoque_utilizado = models.ForeignKey(
        EstoqueItem, 
        on_delete=models.PROTECT, 
        null=True, blank=True,
        help_text="Se houve troca, de qual estoque saiu a peça nova?"
    )
    novo_serial_number = models.CharField(max_length=100, blank=True, null=True, help_text="Serial da nova peça (se aplicável)")

    observacao = models.TextField(blank=True, verbose_name="Relato do Técnico")

    class Meta:
        verbose_name = "Registro de Manutenção"
        verbose_name_plural = "Livro de Ocorrências"
        ordering = ['-data_ocorrencia']

    def __str__(self):
        return f"{self.get_tipo_atividade_display()} - {self.posicao} ({self.data_ocorrencia.date()})"