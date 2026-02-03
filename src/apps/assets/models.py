from django.db import models
from src.apps.core.models import TenantAwareModel
from src.apps.inventory.models import CatalogoPeca

class Motor(TenantAwareModel):
    # Identificação
    nome = models.CharField(max_length=100, help_text="Ex: Gerador 01 - Principal")
    marca = models.CharField(max_length=100, default="Jenbacher")
    modelo = models.CharField(max_length=100, help_text="Ex: J620")
    numero_serie = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=100, help_text="Ex: Sala de Máquinas A")
    
    # Dados Técnicos
    potencia_nominal = models.CharField(max_length=50, blank=True)
    qtd_cilindros = models.IntegerField(default=16, help_text="Define quantos kits de cilindro serão criados")
    
    # Periféricos Variáveis (Perguntas do Wizard)
    qtd_baterias = models.IntegerField(default=2, verbose_name="Qtd. Baterias")
    qtd_motores_partida = models.IntegerField(default=1, verbose_name="Qtd. Motores de Partida")
    qtd_turbos = models.IntegerField(default=2, verbose_name="Qtd. Turbinas")
    qtd_filtros_oleo = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Óleo")

    # Horímetros (VITAIS PARA O CÁLCULO)
    horas_totais = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_arranques = models.IntegerField(default=0, help_text="Número total de partidas dadas")
    
    # Controle
    em_operacao = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} ({self.modelo})"


class PosicaoComponente(TenantAwareModel):
    """
    Representa um 'Slot' no motor. Ex: 'Cilindro 1 - Vela'.
    O slot nunca morre, a peça dentro dele muda.
    """
    motor = models.ForeignKey(Motor, related_name='componentes', on_delete=models.CASCADE)
    nome = models.CharField(max_length=200, help_text="Ex: Cilindro 1 - Vela")
    
    # O que está instalado lá agora?
    peca_instalada = models.ForeignKey(
        CatalogoPeca, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        help_text="Qual modelo de peça está aqui?"
    )
    
    # Rastreabilidade
    serial_number = models.CharField(max_length=100, blank=True, null=True, help_text="Serial da peça física (se houver)")
    
    # O 'Snapshot' do momento da instalação
    data_instalacao = models.DateField(null=True, blank=True)
    hora_motor_instalacao = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="Quantas horas o motor tinha quando essa peça foi colocada?"
    )
    arranques_motor_instalacao = models.IntegerField(
        default=0,
        help_text="Quantos arranques o motor tinha quando essa peça foi colocada?"
    )

    # Campos de manutenção específica (Engraxamento/Vibração)
    ultima_medicao_vibracao = models.DateField(null=True, blank=True)
    ultimo_engraxamento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = "Posição/Componente"
        verbose_name_plural = "Posições/Componentes"

    def __str__(self):
        peca = self.peca_instalada.nome if self.peca_instalada else "Vazio"
        return f"{self.nome} [{peca}]"

    @property
    def horas_uso_atual(self):
        """Calcula quantas horas a peça rodou"""
        return self.motor.horas_totais - self.hora_motor_instalacao

    @property
    def arranques_uso_atual(self):
        """Calcula quantos arranques a peça sofreu (Baterias/Start)"""
        return self.motor.total_arranques - self.arranques_motor_instalacao