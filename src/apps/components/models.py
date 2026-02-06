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
        Retorna uma lista simples de strings para alertas rápidos (ex: no Admin ou Listagem).
        Reutiliza a lógica do método detalhado para evitar duplicidade de código.
        """
        detalhes = self.get_detalhes_preventivas()
        alertas = []
        for d in detalhes:
            if d['status'] == 'VENCIDO':
                alertas.append(f"VENCIDO: {d['tarefa']}")
            elif d['status'] == 'ATENÇÃO':
                alertas.append(f"PRÓXIMO: {d['tarefa']}")
        return alertas

    # --- MÉTODO PRINCIPAL PARA O DASHBOARD (TABELA DINÂMICA) ---
    def get_detalhes_preventivas(self):
        """
        Retorna uma lista detalhada de todos os planos para exibição em tabela.
        Calcula prazos, restos, datas e status (Vencido/Atenção/Em dia).
        """
        lista_status = []
        
        horas_motor = self.motor.horas_totais
        arranques_motor = self.motor.total_arranques
        hoje = date.today()

        for plano in self.planos_preventiva.all():
            dados = {
                'id_plano': plano.id,
                'tarefa': plano.tarefa,
                'tipo': plano.get_tipo_servico_display(),
                'frequencia': f"{plano.intervalo_valor} {plano.get_unidade_display()}",
                
                # Dados da Última Execução
                'ultima_data': plano.ultima_execucao_data,
                'ultimo_valor': plano.ultima_execucao_valor, # Horimetro ou Arranques na época
                
                # Cálculos (Padrão)
                'rodado': '-',
                'restante': '-',
                'status': 'EM DIA',
                'cor': 'success', # Verde
                'progresso_pct': 0,
            }

            vencido = False
            atencao = False

            # --- 1. Lógica para HORAS ---
            if plano.unidade == 'HORAS':
                base = plano.ultima_execucao_valor
                # Se nunca foi feito (0), considera a instalação do componente
                if base == 0 and self.hora_motor_instalacao:
                    base = self.hora_motor_instalacao
                
                uso = horas_motor - base
                if uso < 0: uso = 0
                
                falta = plano.intervalo_valor - uso
                
                dados['rodado'] = f"{uso} h"
                dados['restante'] = f"{max(0, falta)} h"
                
                if plano.intervalo_valor > 0:
                    dados['progresso_pct'] = (uso / plano.intervalo_valor) * 100
                
                if uso >= plano.intervalo_valor: vencido = True
                elif uso >= (plano.intervalo_valor * 0.9): atencao = True

            # --- 2. Lógica para ARRANQUES ---
            elif plano.unidade == 'ARRANQUES':
                base = plano.ultima_execucao_valor
                if base == 0 and self.arranques_motor_instalacao:
                    base = self.arranques_motor_instalacao
                
                uso = arranques_motor - base
                if uso < 0: uso = 0
                
                falta = plano.intervalo_valor - uso

                dados['rodado'] = f"{uso} part."
                dados['restante'] = f"{max(0, falta)} part."
                
                if plano.intervalo_valor > 0:
                    dados['progresso_pct'] = (uso / plano.intervalo_valor) * 100

                if uso >= plano.intervalo_valor: vencido = True
                elif uso >= (plano.intervalo_valor * 0.9): atencao = True

            # --- 3. Lógica para TEMPO (DIAS/MESES) ---
            elif plano.unidade in ['DIAS', 'MESES']:
                base_data = plano.ultima_execucao_data
                if not base_data:
                    base_data = self.data_instalacao or hoje
                
                dias_passados = (hoje - base_data).days
                
                limite_dias = plano.intervalo_valor
                if plano.unidade == 'MESES':
                    limite_dias = plano.intervalo_valor * 30
                
                falta_dias = limite_dias - dias_passados
                
                # Exibição Amigável
                if dias_passados > 30:
                    dados['rodado'] = f"{dias_passados // 30} meses"
                else:
                    dados['rodado'] = f"{dias_passados} dias"
                
                dados['restante'] = f"{max(0, falta_dias)} dias"
                
                if limite_dias > 0:
                    dados['progresso_pct'] = (dias_passados / limite_dias) * 100

                if dias_passados >= limite_dias: vencido = True
                elif dias_passados >= (limite_dias * 0.9): atencao = True

            # Ajuste Final de Status e Cores
            if vencido:
                dados['status'] = 'VENCIDO'
                dados['cor'] = 'danger' # Vermelho
                dados['restante'] = '0 (Vencido)'
            elif atencao:
                dados['status'] = 'ATENÇÃO'
                dados['cor'] = 'warning' # Amarelo

            lista_status.append(dados)

        return lista_status

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