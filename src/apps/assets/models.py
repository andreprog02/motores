from django.db import models
from src.apps.core.models import TenantAwareModel

# --- Marca e Modelo ---
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

# --- Motor (Apenas a definição do Motor e suas quantidades) ---
class Motor(TenantAwareModel):
    nome = models.CharField(max_length=100)
    modelo = models.ForeignKey(ModeloMotor, on_delete=models.PROTECT, verbose_name="Modelo")
    numero_serie = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=100)
    
    # Quantidades (Usadas pelo signal na outra app)
    qtd_cilindros = models.IntegerField(default=16)
    qtd_filtros_oleo = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Óleo")
    qtd_trocadores_oleo = models.IntegerField(default=1, verbose_name="Qtd. Trocadores de Óleo")
    qtd_turbos = models.IntegerField(default=2, verbose_name="Qtd. Turbos")
    qtd_blowby = models.IntegerField(default=1, verbose_name="Qtd. Blowby")
    qtd_motores_partida = models.IntegerField(default=1, verbose_name="Qtd. Motores de Arranque")
    qtd_intercoolers = models.IntegerField(default=1, verbose_name="Qtd. Intercoolers")
    qtd_alternadores = models.IntegerField(default=1, verbose_name="Qtd. Alternadores")
    qtd_dampers = models.IntegerField(default=1, verbose_name="Qtd. Dampers")
    qtd_compensadores = models.IntegerField(default=1, verbose_name="Qtd. Compensadores Escape")
    qtd_resistencias = models.IntegerField(default=1, verbose_name="Qtd. Resistências Aquec.")
    qtd_bypass = models.IntegerField(default=1, verbose_name="Qtd. Válvulas Bypass")
    qtd_pre_filtros_ar = models.IntegerField(default=1, verbose_name="Qtd. Pré-Filtros de Ar")
    qtd_filtros_ar = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Ar")
    qtd_filtros_gas = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Gás")
    modelo_filtro_ar = models.CharField(max_length=100, blank=True, null=True)
    
    potencia_nominal = models.CharField(max_length=50, blank=True)
    qtd_baterias = models.IntegerField(default=2)
    qtd_bobinas = models.IntegerField(blank=True, null=True)
    qtd_cabos_vela = models.IntegerField(blank=True, null=True)
    
    horas_totais = models.IntegerField(default=0)
    total_arranques = models.IntegerField(default=0)
    em_operacao = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Motor"
        verbose_name_plural = "Motores"

    def save(self, *args, **kwargs):
        if self.qtd_bobinas is None: self.qtd_bobinas = self.qtd_cilindros
        if self.qtd_cabos_vela is None: self.qtd_cabos_vela = self.qtd_cilindros
        super().save(*args, **kwargs)
    def __str__(self): return f"{self.nome} ({self.modelo.nome})"