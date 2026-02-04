from django.db import models
from src.apps.core.models import TenantAwareModel
from src.apps.inventory.models import CatalogoPeca

# --- (Marca e Modelo - IGUAIS) ---
class MarcaMotor(TenantAwareModel):
    nome = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name = "Marca de Motor"
        verbose_name_plural = "Marcas de Motor"
        ordering = ['nome']
    def __str__(self): return self.nome

class ModeloMotor(TenantAwareModel):
    marca = models.ForeignKey(MarcaMotor, on_delete=models.CASCADE, related_name='modelos')
    nome = models.CharField(max_length=100)
    class Meta:
        verbose_name = "Modelo de Motor"
        verbose_name_plural = "Modelos de Motor"
        unique_together = ('marca', 'nome') 
    def __str__(self): return f"{self.marca.nome} - {self.nome}"

class Motor(TenantAwareModel):
    nome = models.CharField(max_length=100)
    modelo = models.ForeignKey(ModeloMotor, on_delete=models.PROTECT, verbose_name="Modelo")
    numero_serie = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=100)
    
    # --- QUANTIDADES (Configuração dos Slots) ---
    qtd_cilindros = models.IntegerField(default=16)
    
    # 1. Óleo
    qtd_filtros_oleo = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Óleo")
    qtd_trocadores_oleo = models.IntegerField(default=1, verbose_name="Qtd. Trocadores de Óleo")

    # 2. Periféricos (Novos e Existentes)
    qtd_turbos = models.IntegerField(default=2, verbose_name="Qtd. Turbos")
    qtd_blowby = models.IntegerField(default=1, verbose_name="Qtd. Blowby")
    qtd_motores_partida = models.IntegerField(default=1, verbose_name="Qtd. Motores de Arranque")
    qtd_intercoolers = models.IntegerField(default=1, verbose_name="Qtd. Intercoolers")
    qtd_alternadores = models.IntegerField(default=1, verbose_name="Qtd. Alternadores")
    
    # Novos solicitados
    qtd_dampers = models.IntegerField(default=1, verbose_name="Qtd. Dampers")
    qtd_compensadores = models.IntegerField(default=1, verbose_name="Qtd. Compensadores Escape")
    qtd_resistencias = models.IntegerField(default=1, verbose_name="Qtd. Resistências Aquec.")
    qtd_bypass = models.IntegerField(default=1, verbose_name="Qtd. Válvulas Bypass")
    qtd_pre_filtros_ar = models.IntegerField(default=1, verbose_name="Qtd. Pré-Filtros de Ar")
    
    # Filtros
    qtd_filtros_ar = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Ar")
    qtd_filtros_gas = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Gás")
    
    # Outros (Ignicao/Eletrica)
    qtd_baterias = models.IntegerField(default=2)
    qtd_bobinas = models.IntegerField(blank=True, null=True)
    qtd_cabos_vela = models.IntegerField(blank=True, null=True)
    
    # Dados Técnicos
    potencia_nominal = models.CharField(max_length=50, blank=True)
    modelo_filtro_ar = models.CharField(max_length=100, blank=True, null=True)

    # Horímetros
    horas_totais = models.IntegerField(default=0)
    total_arranques = models.IntegerField(default=0)
    em_operacao = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.qtd_bobinas is None: self.qtd_bobinas = self.qtd_cilindros
        if self.qtd_cabos_vela is None: self.qtd_cabos_vela = self.qtd_cilindros
        super().save(*args, **kwargs)
    def __str__(self): return f"{self.nome} ({self.modelo.nome})"


class PosicaoComponente(TenantAwareModel):
    motor = models.ForeignKey(Motor, related_name='componentes', on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    peca_instalada = models.ForeignKey(CatalogoPeca, on_delete=models.SET_NULL, null=True, blank=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nº de Série")
    
    # Rastreabilidade
    data_instalacao = models.DateField(null=True, blank=True, verbose_name="Data Última Troca")
    hora_motor_instalacao = models.IntegerField(default=0)
    
    # Campos extras (mantidos no banco)
    arranques_motor_instalacao = models.IntegerField(default=0)
    data_ultima_coleta = models.DateField(null=True, blank=True)
    horas_na_coleta = models.IntegerField(null=True, blank=True)
    data_ultima_analise = models.DateField(null=True, blank=True)
    resultado_ultima_coleta = models.CharField(max_length=20, null=True, blank=True)
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
        return self.motor.horas_totais - self.hora_motor_instalacao


# --- CATEGORIAS DO MENU (Proxies) ---

class SistemaOleo(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Item de Óleo"
        verbose_name_plural = "Óleo"

class Periferico(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Periférico"
        verbose_name_plural = "Periféricos"