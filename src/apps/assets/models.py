from django.db import models
from src.apps.core.models import TenantAwareModel

# --- Marca e Modelo (Mantém igual) ---
class MarcaMotor(TenantAwareModel):
    nome = models.CharField(max_length=100, unique=True)
    class Meta: verbose_name = "Marca"; ordering = ['nome']
    def __str__(self): return self.nome

class ModeloMotor(TenantAwareModel):
    marca = models.ForeignKey(MarcaMotor, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    class Meta: verbose_name = "Modelo"; unique_together = ('marca', 'nome')
    def __str__(self): return f"{self.marca.nome} - {self.nome}"

# --- Motor (Atualizado com os novos campos) ---
class Motor(TenantAwareModel):
    nome = models.CharField(max_length=100)
    modelo = models.ForeignKey(ModeloMotor, on_delete=models.PROTECT)
    numero_serie = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=100)
    
    # Base
    qtd_cilindros = models.IntegerField(default=12, verbose_name="Qtd. Cilindros (Geral)")
    
    # 1. Sistema de Óleo
    qtd_filtros_oleo = models.IntegerField(default=1, verbose_name="Qtd. Filtros de Óleo")
    qtd_trocadores_oleo = models.IntegerField(default=1, verbose_name="Qtd. Trocadores de Óleo")
    
    # 2. Periféricos
    qtd_turbos = models.IntegerField(default=2, verbose_name="Qtd. Turbos")
    qtd_intercoolers = models.IntegerField(default=2, verbose_name="Qtd. Intercoolers")
    qtd_alternadores = models.IntegerField(default=1, verbose_name="Qtd. Alternadores")
    qtd_dampers = models.IntegerField(default=1, verbose_name="Qtd. Dampers")
    qtd_compensadores = models.IntegerField(default=1, verbose_name="Qtd. Compensadores Escape")
    qtd_resistencias = models.IntegerField(default=1, verbose_name="Qtd. Resistências Aquec.")
    qtd_bypass = models.IntegerField(default=1, verbose_name="Qtd. Válvulas Bypass")
    
    # 3. Filtros
    qtd_filtros_ar = models.IntegerField(default=2, verbose_name="Qtd. Filtros de Ar")
    qtd_pre_filtros_ar = models.IntegerField(default=0, verbose_name="Qtd. Pré-Filtros de Ar")
    qtd_filtros_gas = models.IntegerField(default=0, verbose_name="Qtd. Filtros de Gás")
    modelo_filtro_ar = models.CharField(max_length=100, blank=True, null=True)

    # 4. Cilindros (Detalhado)
    qtd_pistoes = models.IntegerField(default=0, verbose_name="Qtd. Pistões")
    qtd_camisas = models.IntegerField(default=0, verbose_name="Qtd. Camisas")
    qtd_bronzinas = models.IntegerField(default=0, verbose_name="Qtd. Bronzinas")
    qtd_bielas = models.IntegerField(default=0, verbose_name="Qtd. Bielas")
    qtd_velas = models.IntegerField(default=0, verbose_name="Qtd. Velas") # Movido para cá
    
    # 5. Ignição
    qtd_bobinas = models.IntegerField(default=0, verbose_name="Qtd. Bobinas")
    qtd_cabos_vela = models.IntegerField(default=0, verbose_name="Qtd. Cabos de Vela")
    qtd_baterias = models.IntegerField(default=2, verbose_name="Qtd. Baterias")
    qtd_motores_partida = models.IntegerField(default=1, verbose_name="Qtd. Motores de Arranque")

    # Campos Operacionais
    horas_totais = models.IntegerField(default=0)
    total_arranques = models.IntegerField(default=0)
    em_operacao = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Motor"
        verbose_name_plural = "Motores"

    def save(self, *args, **kwargs):
        # Automação inteligente: Se deixar 0, assume a quantidade de cilindros
        if not self.pk: # Apenas na criação
            if self.qtd_pistoes == 0: self.qtd_pistoes = self.qtd_cilindros
            if self.qtd_camisas == 0: self.qtd_camisas = self.qtd_cilindros
            if self.qtd_bronzinas == 0: self.qtd_bronzinas = self.qtd_cilindros
            if self.qtd_bielas == 0: self.qtd_bielas = self.qtd_cilindros
            if self.qtd_velas == 0: self.qtd_velas = self.qtd_cilindros
            if self.qtd_bobinas == 0: self.qtd_bobinas = self.qtd_cilindros
            if self.qtd_cabos_vela == 0: self.qtd_cabos_vela = self.qtd_cilindros
            
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.nome} ({self.modelo.nome})"


class Equipamento(TenantAwareModel):
    """
    Ativos independentes (Periféricos) que possuem horímetro próprio.
    Ex: Compressores, Geradores, Blowers, Ar Condicionado.
    """
    nome = models.CharField(max_length=100)
    fabricante = models.CharField(max_length=100, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    numero_serie = models.CharField(max_length=100, blank=True, null=True)
    localizacao = models.CharField(max_length=100, verbose_name="Localização")
    
    # Horímetro Independente (O coração da mudança)
    horas_totais = models.IntegerField(default=0, verbose_name="Horímetro Atual")
    em_operacao = models.BooleanField(default=True, verbose_name="Em Operação?")
    
    # Link Opcional (Apenas para saber a qual motor ele serve, se servir a algum)
    motor_associado = models.ForeignKey(
        Motor, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='perifericos_externos',
        verbose_name="Motor Associado (Opcional)",
        help_text="Se este equipamento atende a um motor específico (ex: Blower da Sala 1)"
    )

    class Meta:
        verbose_name = "Equipamento / Periférico"
        verbose_name_plural = "Equipamentos e Periféricos"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.horas_totais}h)"