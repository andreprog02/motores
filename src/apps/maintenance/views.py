from django.views.generic import CreateView            # <--- Faltava isso
from django.contrib.auth.mixins import LoginRequiredMixin # <--- Faltava isso
from .models import RegistroManutencao 

class RegistroManutencaoCreateView(LoginRequiredMixin, CreateView):
    model = RegistroManutencao
    fields = '__all__' 
    template_name = 'maintenance/registro_form.html'
    
    def get_initial(self):
        # Preenche automaticamente o componente se vier pela URL (?posicao=ID)
        initial = super().get_initial()
        posicao_id = self.request.GET.get('posicao')
        if posicao_id:
            # Garanta que seu Model RegistroManutencao tem um campo chamado 'posicao'
            # Se o nome do campo for outro (ex: 'componente'), troque abaixo.
            initial['posicao'] = posicao_id 
        return initial