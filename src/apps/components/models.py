from datetime import date
from django.db import models
from src.apps.core.models import TenantAwareModel
from src.apps.inventory.models import CatalogoPeca
from src.apps.assets.models import Motor, Equipamento  # Importamos o novo modelo Equipamento

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

# --- 1. O GRUPO (A Pasta Virtual) ---
class GrupoComponente(TenantAwareModel):
    """
    Agrupador de componentes. Pode pertencer a um Motor ou a um Equipamento.
    """
    motor = models.ForeignKey(
        Motor, 
        related_name='grupos', 
        on_delete=models.CASCADE,
        null=True, blank=True  # Opcional
    )
    equipamento = models.ForeignKey(
        Equipamento,
        related_name='grupos',
        on_delete=models.CASCADE,
        null=True, blank=True  # Opcional (Novo)
    )
    
    nome = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, blank=True, null=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Gerenciar Categoria"
        verbose_name_plural = "Gerenciar Categorias"
        ordering = ['ordem', 'nome']
        # Removemos unique_together estrito pois agora um dos dois pode ser null
        # unique_together = ('motor', 'nome') 

    def __str__(self):
        if self.motor:
            return f"{self.nome} (Motor: {self.motor.nome})"
        if self.equipamento:
            return f"{self.nome} (Eqp: {self.equipamento.nome})"
        return self.nome

# --- 2. O ITEM (Componente Físico) ---
class PosicaoComponente(TenantAwareModel):
    # --- Vínculos (Um dos dois deve ser preenchido) ---
    motor = models.ForeignKey(
        Motor, 
        related_name='componentes', 
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    equipamento = models.ForeignKey(
        Equipamento,
        related_name='componentes',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    
    grupo = models.ForeignKey(GrupoComponente, related_name='itens', on_delete=models.SET_NULL, null=True, blank=True)
    
    nome = models.CharField(max_length=200)

    # --- CAMPOS PARA ORDENAÇÃO ---
    nome_base = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo do Item")
    numero = models.PositiveIntegerField(default=0, verbose_name="Sequência")
    # -----------------------------------

    peca_instalada = models.ForeignKey(CatalogoPeca, on_delete=models.SET_NULL, null=True, blank=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nº de Série")
    
    data_instalacao = models.DateField(null=True, blank=True, verbose_name="Data Última Troca")
    
    # Snapshot da instalação (Horas/Arranques do Ativo Pai naquele momento)
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
        ativo = self.ativo_pai
        nome_ativo = ativo.nome if ativo else "Sem Vínculo"
        peca = self.peca_instalada.nome if self.peca_instalada else 'Vazio'
        return f"{self.nome} ({nome_ativo}) [{peca}]"

    @property
    def ativo_pai(self):
        """Retorna o objeto Motor ou Equipamento dono deste componente."""
        return self.motor if self.motor else self.equipamento

    @property
    def horas_uso_atual(self):
        """Calcula as horas rodadas desde a instalação nesta posição, 
           independente se é Motor ou Equipamento."""
        ativo = self.ativo_pai
        if not ativo:
            return 0
        return ativo.horas_totais - self.hora_motor_instalacao

    @property
    def status_preventivas(self):
        """
        Retorna uma lista simples de strings para alertas rápidos.
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
        Retorna uma lista detalhada de todos os planos, calculando
        com base no horímetro/arranques do ativo pai (Motor ou Equipamento).
        """
        lista_status = []
        
        ativo = self.ativo_pai
        
        # Se não tiver pai, não há como calcular horas
        if not ativo:
            return []

        horas_ativo = ativo.horas_totais
        # Equipamentos podem não ter arranques, usamos getattr para segurança
        arranques_ativo = getattr(ativo, 'total_arranques', 0)
        
        hoje = date.today()

        for plano in self.planos_preventiva.all():
            dados = {
                'id_plano': plano.id,
                'tarefa': plano.tarefa,
                'tipo': plano.get_tipo_servico_display(),
                'frequencia': f"{plano.intervalo_valor} {plano.get_unidade_display()}",
                
                # Dados da Última Execução
                'ultima_data': plano.ultima_execucao_data,
                'ultimo_valor': plano.ultima_execucao_valor, 
                
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
                if base == 0 and self.hora_motor_instalacao:
                    base = self.hora_motor_instalacao
                
                uso = horas_ativo - base
                if uso < 0: uso = 0
                
                falta = plano.intervalo_valor - uso
                dados['rodado'] = f"{uso} h"
                
                # Lógica de Vencimento
                if falta < 0:
                    vencido = True
                    dados['restante'] = f"Vencido há {abs(falta)} h"
                else:
                    dados['restante'] = f"{falta} h"
                
                if plano.intervalo_valor > 0:
                    dados['progresso_pct'] = (uso / plano.intervalo_valor) * 100
                
                if not vencido and uso >= (plano.intervalo_valor * 0.9): 
                    atencao = True

            # --- 2. Lógica para ARRANQUES ---
            elif plano.unidade == 'ARRANQUES':
                base = plano.ultima_execucao_valor
                if base == 0 and self.arranques_motor_instalacao:
                    base = self.arranques_motor_instalacao
                
                uso = arranques_ativo - base
                if uso < 0: uso = 0
                
                falta = plano.intervalo_valor - uso
                dados['rodado'] = f"{uso} part."
                
                if falta < 0:
                    vencido = True
                    dados['restante'] = f"Vencido há {abs(falta)} part."
                else:
                    dados['restante'] = f"{falta} part."
                
                if plano.intervalo_valor > 0:
                    dados['progresso_pct'] = (uso / plano.intervalo_valor) * 100

                if not vencido and uso >= (plano.intervalo_valor * 0.9): 
                    atencao = True

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
                
                # Exibição Amigável de Rodado
                if dias_passados > 30:
                    dados['rodado'] = f"{dias_passados // 30} meses"
                else:
                    dados['rodado'] = f"{dias_passados} dias"
                
                # Lógica de Vencimento
                if falta_dias < 0:
                    vencido = True
                    dias_vencidos = abs(falta_dias)
                    if dias_vencidos > 30:
                        dados['restante'] = f"Vencido há {dias_vencidos // 30} meses"
                    else:
                        dados['restante'] = f"Vencido há {dias_vencidos} dias"
                else:
                    dados['restante'] = f"{falta_dias} dias"
                
                if limite_dias > 0:
                    dados['progresso_pct'] = (dias_passados / limite_dias) * 100

                if not vencido and dias_passados >= (limite_dias * 0.9): 
                    atencao = True

            # Ajuste Final de Status e Cores
            if vencido:
                dados['status'] = 'VENCIDO'
                dados['cor'] = 'danger' # Vermelho
                dados['progresso_pct'] = 100 
                
            elif atencao:
                dados['status'] = 'ATENÇÃO'
                dados['cor'] = 'warning' # Amarelo

            lista_status.append(dados)

        return lista_status

# --- 3. PLANOS DE PREVENTIVA (Mantém Igual) ---
class PlanoPreventiva(TenantAwareModel):
    posicao = models.ForeignKey(
        PosicaoComponente, 
        related_name='planos_preventiva', 
        on_delete=models.CASCADE
    )
    
    tarefa = models.CharField(max_length=100, verbose_name="Nome da Tarefa") 
    
    tipo_servico = models.CharField(
        max_length=50,
        choices=TIPOS_SERVICO_OPCOES, 
        verbose_name="Gatilho de Reset",
        help_text="Qual serviço no Livro de Ocorrências zera este plano?"
    )

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

    ultima_execucao_valor = models.IntegerField(
        default=0, 
        verbose_name="Último Contador (Horas/Arranques)",
        help_text="Armazena o horímetro ou nº de arranques da última troca"
    )
    
    ultima_execucao_data = models.DateField(
        null=True, blank=True,
        verbose_name="Data Última Execução"
    )

    def __str__(self):
        return f"{self.tarefa} (A cada {self.intervalo_valor} {self.get_unidade_display()})"

# --- 4. OS MENUS (Proxies - Filtros Visuais) ---

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