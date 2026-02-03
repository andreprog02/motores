from django.db import models
from src.apps.core.models import TenantAwareModel
from src.apps.assets.models import Motor, PosicaoComponente
from src.apps.inventory.models import EstoqueItem
from django.conf import settings

class RegistroManutencao(TenantAwareModel):
    TIPO_ATIVIDADE = [
        ('PREVENTIVA', 'Manutenção Preventiva'),
        ('CORRETIVA', 'Manutenção Corretiva'),
        ('LUBRIFICACAO', 'Lubrificação / Engraxamento'),
        ('TROCA', 'Substituição de Peça'),
        ('INSPECAO', 'Inspeção de Rotina'),
    ]

    responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    motor = models.ForeignKey(Motor, on_delete=models.CASCADE)
    posicao = models.ForeignKey(PosicaoComponente, on_delete=models.CASCADE, verbose_name="Posição / Componente")
    
    tipo_atividade = models.CharField(max_length=20, choices=TIPO_ATIVIDADE)
    
    data_ocorrencia = models.DateField(default=models.functions.Now)
    
    # --- MUDANÇA AQUI: De Float/Decimal para IntegerField ---
    horimetro_na_execucao = models.IntegerField(
        verbose_name="Horímetro no momento",
        help_text="Quantas horas totais o motor tinha nesta data?"
    )

    # Peças
    item_estoque_utilizado = models.ForeignKey(
        EstoqueItem, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name="Peça do Estoque",
        help_text="Selecione a peça que foi consumida"
    )
    novo_serial_number = models.CharField(max_length=100, blank=True, null=True)
    
    observacao = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Manutenção"
        verbose_name_plural = "Livro de Ocorrências"
        ordering = ['-data_ocorrencia']

    def __str__(self):
        return f"{self.data_ocorrencia} - {self.motor.nome} - {self.tipo_atividade}"