from django.contrib import admin
from src.apps.core.admin import TenantModelAdmin 
from .models import CategoriaPeca, CatalogoPeca, LocalEstoque, EstoqueItem

@admin.register(CategoriaPeca)
class CategoriaAdmin(TenantModelAdmin): 
    list_display = ('nome',)
    search_fields = ('nome',)
    ordering = ('nome',)

@admin.register(CatalogoPeca)
class CatalogoAdmin(TenantModelAdmin):
    list_display = ('nome', 'categoria', 'exibir_compatibilidade', 'aplicacao_universal', 'vida_util_horas')
    list_filter = ('aplicacao_universal', 'categoria', 'modelos_compativeis')
    search_fields = ('nome', 'codigo_fabricante')
    filter_horizontal = ('modelos_compativeis',)
    ordering = ('nome',)

    def exibir_compatibilidade(self, obj):
        if obj.aplicacao_universal:
            return "🟢 UNIVERSAL"
        modelos = [str(m) for m in obj.modelos_compativeis.all()[:3]]
        if obj.modelos_compativeis.count() > 3:
            modelos.append("...")
        return ", ".join(modelos) if modelos else "-"
    exibir_compatibilidade.short_description = "Aplicação Resumida"

    class Media:
        js = ('js/mascaras.js',)

@admin.register(LocalEstoque)
class LocalAdmin(TenantModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
    ordering = ('nome',)

@admin.register(EstoqueItem)
class EstoqueAdmin(TenantModelAdmin):
    list_display = ('catalogo', 'aplicacao_detalhada', 'local', 'quantidade')
    list_filter = ('local', 'catalogo__categoria', 'catalogo__modelos_compativeis__marca')
    autocomplete_fields = ['catalogo', 'local']
    ordering = ('catalogo__nome',)

    # --- CORREÇÃO DO ERRO E040 ---
    # Estes campos permitem que o autocomplete funcione!
    search_fields = [
        'catalogo__nome',
        'catalogo__codigo_fabricante',
        'catalogo__modelos_compativeis__nome',
        'catalogo__modelos_compativeis__marca__nome'
    ]

    class Media:
        js = ('js/mascaras.js',)

    def aplicacao_detalhada(self, obj):
        peca = obj.catalogo
        if peca.aplicacao_universal:
            return "🟢 UNIVERSAL"
        
        lista_motores = peca.modelos_compativeis.all()
        if not lista_motores:
            return "⚠️ Sem vínculo"
            
        textos = []
        for modelo in lista_motores:
            textos.append(f"{modelo.marca.nome} {modelo.nome}")
        return ", ".join(textos)

    aplicacao_detalhada.short_description = "Aplicação (Marca/Modelo)"