from django.db import models
from django.utils.translation import gettext_lazy as _
from src.apps.core.models import TenantAwareModel

class CategoriaPeca(TenantAwareModel):
    nome = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Categoria de Peça"
        verbose_name_plural = "Categorias de Peças"

    def __str__(self):
        return self.nome

class CatalogoPeca(TenantAwareModel):
    """
    O 'DNA' da peça. Aqui definimos quanto tempo ela dura.
    O usuário não cadastra 'Vela' toda vez, ele puxa deste cadastro.
    """
    nome = models.CharField(max_length=200)
    codigo_fabricante = models.CharField(max_length=100, blank=True, null=True)
    categoria = models.ForeignKey(CategoriaPeca, on_delete=models.PROTECT)
    
    # --- LÓGICA DE COMPATIBILIDADE ---
    aplicacao_universal = models.BooleanField(
        default=False,
        verbose_name="Uso Universal / Genérico",
        help_text="Marque se esta peça serve para qualquer aplicação (ex: Óleo, Ferramentas). Se marcado, a lista de modelos será ignorada."
    )

    modelos_compativeis = models.ManyToManyField(
        'assets.ModeloMotor', 
        blank=True, 
        related_name='pecas_compativeis',
        verbose_name="Modelos Compatíveis",
        help_text="Se não for universal, selecione quais modelos de motor podem usar esta peça."
    )
    # ---------------------------------------

    # Configurações de Rastreabilidade
    requer_serial_number = models.BooleanField(
        default=False, 
        help_text="Se marcado, exige digitar o Nº de Série ao instalar (ex: Baterias, Turbos)."
    )
    quantidade_por_jogo = models.IntegerField(
        default=1,
        help_text="Ex: Anéis de segmento usam 3 por cilindro. Velas usam 1."
    )

    # Inteligência de Vida Útil (SLA)
    vida_util_horas = models.IntegerField(
        null=True, blank=True, 
        help_text="Limite de horas de operação (Ex: 2000h para Velas)"
    )
    vida_util_arranques = models.IntegerField(
        null=True, blank=True, 
        help_text="Limite de partidas (Ex: 1000 arranques para Baterias)"
    )
    vida_util_meses = models.IntegerField(
        null=True, blank=True, 
        help_text="Validade temporal (Ex: 6 meses para Óleo, mesmo parado)"
    )
    
    # Ponto de Alerta (Ex: Avisar quando atingir 90% da vida)
    alerta_amarelo_pct = models.IntegerField(default=90)

    class Meta:
        verbose_name = "Catálogo de Peça (Mestre)"
        verbose_name_plural = "Catálogo de Peças (Mestre)"
        unique_together = ('tenant', 'codigo_fabricante')

    def __str__(self):
        return f"{self.nome} ({self.codigo_fabricante or 'S/N'})"

class LocalEstoque(TenantAwareModel):
    nome = models.CharField(max_length=100, help_text="Ex: Armário A, Filial SP, Container 2")
    
    class Meta:
        verbose_name = "Local de Estoque"
        verbose_name_plural = "Locais de Estoque"

    def __str__(self):
        return self.nome

class EstoqueItem(TenantAwareModel):
    """
    A quantidade física. Relaciona o Catálogo com o Local.
    """
    catalogo = models.ForeignKey(CatalogoPeca, on_delete=models.CASCADE, related_name='estoques')
    local = models.ForeignKey(LocalEstoque, on_delete=models.CASCADE)
    
    # Quantidade inteira
    quantidade = models.IntegerField(default=0, help_text="Quantidade física (Inteiro)")
    minimo_seguranca = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Item em Estoque"
        verbose_name_plural = "Itens em Estoque"
        unique_together = ('tenant', 'catalogo', 'local')

    def __str__(self):
        return f"{self.catalogo.nome} em {self.local.nome}: {self.quantidade}"

# --- TABELA DE SERIAIS INDIVIDUAIS (Filhos do EstoqueItem) ---
class SerialPeca(TenantAwareModel):
    item_estoque = models.ForeignKey(EstoqueItem, on_delete=models.CASCADE, related_name='seriais')
    serial_number = models.CharField(max_length=100, verbose_name="Nº de Série")
    data_entrada = models.DateField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Serial Individual"
        verbose_name_plural = "Seriais em Estoque"
        unique_together = ('item_estoque', 'serial_number') 

    def __str__(self):
        return f"SN: {self.serial_number}"

# --- HISTÓRICO DE MOVIMENTAÇÃO ---
class MovimentoEstoque(TenantAwareModel):
    TIPO_MOVIMENTO = [
        ('ENTRADA', 'Entrada (Compra/Retorno)'),
        ('SAIDA', 'Saída (Uso/Perda)'),
        ('AJUSTE', 'Ajuste de Inventário'),
    ]
    
    item = models.ForeignKey(EstoqueItem, on_delete=models.CASCADE, related_name='movimentos')
    tipo = models.CharField(max_length=20, choices=TIPO_MOVIMENTO)
    quantidade = models.IntegerField()
    data_movimento = models.DateTimeField(auto_now_add=True)
    origem = models.CharField(max_length=100, help_text="Ex: Manutenção #123", blank=True, null=True)
    
    class Meta:
        verbose_name = "Movimento de Estoque"
        verbose_name_plural = "Histórico de Movimentações"
        ordering = ['-data_movimento']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.quantidade} un"