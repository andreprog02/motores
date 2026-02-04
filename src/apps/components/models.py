from django.db import models
from src.apps.core.models import TenantAwareModel
from src.apps.inventory.models import CatalogoPeca
from src.apps.assets.models import Motor

# --- 1. O GRUPO (A Pasta Real) ---
class GrupoComponente(TenantAwareModel):
    motor = models.ForeignKey(Motor, related_name='grupos', on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, blank=True, null=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Gerenciar Categoria"
        verbose_name_plural = "Gerenciar Categorias"
        ordering = ['ordem', 'nome']
        unique_together = ('motor', 'nome')

    def __str__(self):
        return f"{self.nome} ({self.motor.nome})"

# --- 2. O ITEM (Componente Físico) ---
class PosicaoComponente(TenantAwareModel):
    motor = models.ForeignKey(Motor, related_name='componentes', on_delete=models.CASCADE)
    grupo = models.ForeignKey(GrupoComponente, related_name='itens', on_delete=models.SET_NULL, null=True, blank=True)
    
    nome = models.CharField(max_length=200)
    peca_instalada = models.ForeignKey(CatalogoPeca, on_delete=models.SET_NULL, null=True, blank=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nº de Série")
    
    data_instalacao = models.DateField(null=True, blank=True, verbose_name="Data Última Troca")
    hora_motor_instalacao = models.IntegerField(default=0)
    arranques_motor_instalacao = models.IntegerField(default=0)
    
    # Monitoramento
    data_ultima_coleta = models.DateField(null=True, blank=True)
    horas_na_coleta = models.IntegerField(null=True, blank=True)
    data_ultima_analise = models.DateField(null=True, blank=True)
    resultado_ultima_coleta = models.CharField(max_length=20, null=True, blank=True)
    ultima_medicao_vibracao = models.DateField(null=True, blank=True)
    ultimo_engraxamento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['grupo__ordem', 'nome']
        verbose_name = "Componente"
        verbose_name_plural = "Todos os Componentes"

    def __str__(self):
        return f"{self.nome} [{self.peca_instalada.nome if self.peca_instalada else 'Vazio'}]"

    @property
    def horas_uso_atual(self):
        return self.motor.horas_totais - self.hora_motor_instalacao

# --- 3. OS MENUS (Proxies) ---

class MenuOleo(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Item de Óleo"
        verbose_name_plural = "1. Sistema de Óleo"

class MenuFiltros(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Item de Filtro"
        verbose_name_plural = "2. Filtros (Ar/Gás)"

class MenuPerifericos(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Periférico"
        verbose_name_plural = "3. Periféricos"

class MenuIgnicao(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Item de Ignição"
        verbose_name_plural = "4. Ignição / Elétrica"

# --- NOVAS CATEGORIAS ---
class MenuCilindros(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Item de Cilindro"
        verbose_name_plural = "5. Cilindros (Power Pack)"

class MenuCabecotes(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Item de Cabeçote"
        verbose_name_plural = "6. Cabeçotes"

# Ajustei a numeração para 7
class MenuOutros(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Outro Item"
        verbose_name_plural = "7. Outros / Personalizados"