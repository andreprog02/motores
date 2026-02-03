from django.db import models
from src.apps.core.models import TenantAwareModel
from src.apps.inventory.models import CatalogoPeca

# 1. Novas Tabelas para Organização (Normalização)
class MarcaMotor(TenantAwareModel):
    nome = models.CharField(max_length=100, unique=True, help_text="Ex: Jenbacher, Caterpillar, MWM")

    class Meta:
        verbose_name = "Marca de Motor"
        verbose_name_plural = "Marcas de Motor"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ModeloMotor(TenantAwareModel):
    marca = models.ForeignKey(MarcaMotor, on_delete=models.CASCADE, related_name='modelos')
    nome = models.CharField(max_length=100, help_text="Ex: J620, J420, G3516")
    
    class Meta:
        verbose_name = "Modelo de Motor"
        verbose_name_plural = "Modelos de Motor"
        ordering = ['marca', 'nome']
        unique_together = ('marca', 'nome') 

    def __str__(self):
        return f"{self.marca.nome} - {self.nome}"


class Motor(TenantAwareModel):
    # Identificação
    nome = models.CharField(max_length=100, help_text="Ex: Gerador 01 - Principal")
    
    modelo = models.ForeignKey(
        ModeloMotor, 
        on_delete=models.PROTECT,
        verbose_name="Modelo do Motor",
        help_text="Selecione o modelo (A marca será identificada automaticamente)"
    )
    
    numero_serie = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=100, help_text="Ex: Sala de Máquinas A")
    
    # Dados Técnicos
    potencia_nominal = models.CharField(max_length=50, blank=True)
    qtd_cilindros = models.IntegerField(default=16, help_text="Define quantos kits de cilindro serão criados")
    
    # Periféricos Variáveis
    qtd_baterias = models.IntegerField(default=2, verbose_name="Qtd. Baterias")
    qtd_motores_partida = models.IntegerField(default=1, verbose_name="Qtd. Motores de Partida")
    qtd_turbos = models.IntegerField(default=2, verbose_name="Qtd. Turbinas")
    qtd_filtros_oleo = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Óleo")

    # --- NOVOS CAMPOS ADICIONADOS ---
    
    # Sistema de Combustível
    qtd_filtros_gas = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Gás/Combustível")

    # Sistema de Admissão
    qtd_filtros_ar = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Ar")
    modelo_filtro_ar = models.CharField(
        max_length=100, blank=True, null=True, 
        verbose_name="Modelo do Filtro de Ar",
        help_text="Ex: Cônico, Inbox, ou Código da Peça"
    )

    # Sistema de Ignição
    qtd_bobinas = models.IntegerField(
        blank=True, null=True, 
        verbose_name="Qtd. Bobinas",
        help_text="Se vazio, assume a quantidade de cilindros"
    )
    qtd_cabos_vela = models.IntegerField(
        blank=True, null=True, 
        verbose_name="Qtd. Cabos de Vela",
        help_text="Se vazio, assume a quantidade de cilindros"
    )

    # Outros Componentes
    blowby = models.CharField(
        max_length=100, blank=True, default="Padrão",
        verbose_name="Sistema Blowby",
        help_text="Tipo de respiro ou filtro de blowby"
    )

    # -------------------------------

    # Horímetros (VITAIS PARA O CÁLCULO)
    horas_totais = models.IntegerField(default=0, help_text="Horas Totais (Inteiro)")
    total_arranques = models.IntegerField(default=0, help_text="Número total de partidas dadas")
    
    # Controle
    em_operacao = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir valores padrão dinâmicos.
        """
        # Se não informou bobinas, assume igual aos cilindros
        if self.qtd_bobinas is None and self.qtd_cilindros:
            self.qtd_bobinas = self.qtd_cilindros
        
        # Se não informou cabos, assume igual aos cilindros
        if self.qtd_cabos_vela is None and self.qtd_cilindros:
            self.qtd_cabos_vela = self.qtd_cilindros

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} ({self.modelo.marca.nome} {self.modelo.nome})"


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
    
    hora_motor_instalacao = models.IntegerField(
        default=0,
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