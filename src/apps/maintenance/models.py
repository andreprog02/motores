from django.db import models
from src.apps.core.models import TenantAwareModel
from src.apps.assets.models import Motor
from src.apps.components.models import PosicaoComponente

class RegistroManutencao(TenantAwareModel):
    motor = models.ForeignKey(Motor, on_delete=models.CASCADE, related_name='manutencoes')
    posicao = models.ForeignKey(PosicaoComponente, on_delete=models.CASCADE, related_name='historico_manutencao')
    
    data_ocorrencia = models.DateField(verbose_name="Data da Ocorrência")
    tipo_atividade = models.CharField(
        max_length=50, 
        choices=[('CORRETIVA', 'Corretiva'), ('PREVENTIVA', 'Preventiva')],
        default='PREVENTIVA'
    )
    
    # --- Campos do Livro de Registro ---
    horimetro_na_execucao = models.IntegerField(verbose_name="Horímetro na Execução", default=0)
    responsavel = models.CharField(max_length=100, blank=True, null=True, verbose_name="Responsável")
    observacao = models.TextField(blank=True, null=True, verbose_name="Observações")
    novo_serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Novo Nº de Série (Se houve troca)")

    # --- CAMPO DESATIVADO TEMPORARIAMENTE (Causa do Erro) ---
    # O Django não está achando o modelo 'ItemEstoque'. Descomente quando criar o Inventory.
    # item_estoque_utilizado = models.ForeignKey(
    #     'inventory.ItemEstoque', 
    #     on_delete=models.SET_NULL, 
    #     null=True, blank=True,
    #     verbose_name="Item de Estoque Utilizado"
    # )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Registro de Manutenção"
        verbose_name_plural = "Registros de Manutenção"
        ordering = ['-data_ocorrencia']

    def __str__(self):
        return f"{self.data_ocorrencia} - {self.motor} - {self.posicao}"