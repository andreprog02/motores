from datetime import date
from django.db import models
from src.apps.core.models import TenantAwareModel
from src.apps.inventory.models import CatalogoPeca
from src.apps.assets.models import Motor

# --- OPÇÕES COMPARTILHADAS ---

TIPOS_SERVICO_OPCOES = [
    ('SUBSTITUICAO', 'Substituição (Troca de Peça)'),
    ('INSTALACAO', 'Instalação (Nova Peça)'),
    ('REGULAGEM', 'Regulagem'),
    ('LUBRIFICACAO', 'Lubrificação'),
    ('CALIBRACAO', 'Calibração'),
    ('INSPECAO', 'Inspeção / Rotina'),
    ('LIMPEZA', 'Limpeza'),
]

UNIDADES_MEDIDA = [
    ('HORAS', 'Horas de Operação'),
    ('ARRANQUES', 'Arranques / Partidas'),
    ('DIAS', 'Dias Corridos'),
    ('MESES', 'Meses'),
]

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

    # --- CAMPOS PARA ORDENAÇÃO ---
    nome_base = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo do Item")
    numero = models.PositiveIntegerField(default=0, verbose_name="Sequência")
    # -----------------------------------

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
        ordering = ['grupo__ordem', 'nome_base', 'numero'] 
        verbose_name = "Componente"
        verbose_name_plural = "Todos os Componentes"

    def __str__(self):
        return f"{self.nome} [{self.peca_instalada.nome if self.peca_instalada else 'Vazio'}]"

    @property
    def horas_uso_atual(self):
        """Calcula as horas rodadas desde a instalação nesta posição"""
        return self.motor.horas_totais - self.hora_motor_instalacao

    @property
    def status_preventivas(self):
        """
        Analisa todos os planos de preventiva deste slot.
        CORRIGIDO: Agora lê corretamente 'total_arranques' do Motor.
        """
        planos = self.planos_preventiva.all()
        alertas = []
        
        # Dados Atuais (Contexto)
        hoje = date.today()
        horas_atuais = self.motor.horas_totais
        
        # --- CORREÇÃO AQUI: Usando o nome do campo correto do seu Motor ---
        arranques_atuais = self.motor.total_arranques
        
        for plano in planos:
            vencido = False
            proximo = False
            
            # --- CÁLCULO 1: HORAS ---
            if plano.unidade == 'HORAS':
                base = plano.ultima_execucao_valor
                if base == 0 and self.hora_motor_instalacao:
                    base = self.hora_motor_instalacao
                
                rodado = horas_atuais - base
                if rodado < 0: rodado = 0 
                
                if rodado >= plano.intervalo_valor: vencido = True
                elif rodado >= (plano.intervalo_valor * 0.9): proximo = True

            # --- CÁLCULO 2: ARRANQUES ---
            elif plano.unidade == 'ARRANQUES':
                base = plano.ultima_execucao_valor
                # Se nunca executou (0), tenta usar a instalação da peça
                if base == 0 and self.arranques_motor_instalacao:
                    base = self.arranques_motor_instalacao
                
                ciclos = arranques_atuais - base
                if ciclos < 0: ciclos = 0
                
                if ciclos >= plano.intervalo_valor: vencido = True
                elif ciclos >= (plano.intervalo_valor * 0.9): proximo = True

            # --- CÁLCULO 3: TEMPO (DIAS/MESES) ---
            elif plano.unidade in ['DIAS', 'MESES']:
                base_data = plano.ultima_execucao_data
                if not base_data:
                    base_data = self.data_instalacao or hoje
                
                dias_passados = (hoje - base_data).days
                
                limite_dias = plano.intervalo_valor
                if plano.unidade == 'MESES':
                    limite_dias = plano.intervalo_valor * 30 
                
                if dias_passados >= limite_dias: vencido = True
                elif dias_passados >= (limite_dias * 0.9): proximo = True

            # --- GERA OS TEXTOS ---
            if vencido:
                alertas.append(f"VENCIDO: {plano.tarefa}")
            elif proximo:
                alertas.append(f"PRÓXIMO: {plano.tarefa}")
                
        return alertas

# --- 3. PLANOS DE PREVENTIVA (Flexível) ---
class PlanoPreventiva(TenantAwareModel):
    posicao = models.ForeignKey(
        PosicaoComponente, 
        related_name='planos_preventiva', 
        on_delete=models.CASCADE
    )
    
    tarefa = models.CharField(max_length=100, verbose_name="Nome da Tarefa") 
    
    # GATILHO DE RESET (Para automação)
    tipo_servico = models.CharField(
        max_length=50,
        choices=TIPOS_SERVICO_OPCOES, 
        verbose_name="Gatilho de Reset",
        help_text="Qual serviço no Livro de Ocorrências zera este plano?"
    )

    # --- DEFINIÇÃO DO INTERVALO ---
    unidade = models.CharField(
        max_length=20, 
        choices=UNIDADES_MEDIDA, 
        default='HORAS',
        verbose_name="Controlar por"
    )
    
    intervalo_valor = models.PositiveIntegerField(
        verbose_name="Intervalo",
        help_text="Ex: 500 (Horas), 6 (Meses), 1000 (Arranques)"
    )

    # --- CONTROLE DE EXECUÇÃO ---
    # Armazena o valor do contador no momento da última execução
    ultima_execucao_valor = models.IntegerField(
        default=0, 
        verbose_name="Último Contador (Horas/Arranques)",
        help_text="Armazena o horímetro ou nº de arranques da última troca"
    )
    
    # Armazena a data da última execução (Para planos de TEMPO)
    ultima_execucao_data = models.DateField(
        null=True, blank=True,
        verbose_name="Data Última Execução"
    )

    def __str__(self):
        return f"{self.tarefa} (A cada {self.intervalo_valor} {self.get_unidade_display()})"

# --- 4. OS MENUS (Proxies) ---

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

class MenuOutros(PosicaoComponente):
    class Meta:
        proxy = True
        verbose_name = "Outro Item"
        verbose_name_plural = "7. Outros / Personalizados"