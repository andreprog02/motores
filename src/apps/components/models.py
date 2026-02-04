from django.db import models
from src.apps.core.models import TenantAwareModel
from src.apps.inventory.models import CatalogoPeca
from src.apps.assets.models import Motor

class PosicaoComponente(TenantAwareModel):
    # ... (Mantenha os campos que já definimos antes: motor, nome, serial, datas...)
    motor = models.ForeignKey(Motor, related_name='componentes', on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    peca_instalada = models.ForeignKey(CatalogoPeca, on_delete=models.SET_NULL, null=True, blank=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nº de Série")
    
    data_instalacao = models.DateField(null=True, blank=True, verbose_name="Data Última Troca")
    hora_motor_instalacao = models.IntegerField(default=0)
    
    # Campos Extras
    arranques_motor_instalacao = models.IntegerField(default=0)
    data_ultima_coleta = models.DateField(null=True, blank=True)
    horas_na_coleta = models.IntegerField(null=True, blank=True)
    data_ultima_analise = models.DateField(null=True, blank=True)
    resultado_ultima_coleta = models.CharField(max_length=20, null=True, blank=True)
    ultima_medicao_vibracao = models.DateField(null=True, blank=True)
    ultimo_engraxamento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = "Componente Geral"
        verbose_name_plural = "1. Lista Geral" # Item 1 do Menu Componentes

    def __str__(self):
        return f"{self.nome} [{self.peca_instalada.nome if self.peca_instalada else 'Vazio'}]"

    @property
    def horas_uso_atual(self):
        return self.motor.horas_totais - self.hora_motor_instalacao


# --- PROXIES (AGORA NA PASTA CERTA) ---

class SistemaOleo(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Item de Óleo"
        verbose_name_plural = "2. Óleo" # Item 2 do Menu Componentes

class Periferico(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Periférico"
        verbose_name_plural = "3. Periféricos" # Item 3 do Menu Componentes