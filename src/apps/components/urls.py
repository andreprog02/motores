from django.urls import path
from .views import PosicaoComponenteDetailView

app_name = 'components'

urlpatterns = [
    # Exemplo de URL: /components/item/15/
    path('item/<int:pk>/', PosicaoComponenteDetailView.as_view(), name='posicaocomponente_detail'),
]