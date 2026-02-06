from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PosicaoComponente

class PosicaoComponenteDetailView(LoginRequiredMixin, DetailView):
    model = PosicaoComponente
    template_name = 'components/posicaocomponente_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Opcional: Adiciona dados extras se precisar no futuro
        return context