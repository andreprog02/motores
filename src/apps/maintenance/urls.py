from django.urls import path
from .views import RegistroManutencaoCreateView

app_name = 'maintenance'  # <--- Isso define o namespace 'maintenance'

urlpatterns = [
    # A rota que o botão procura: 'maintenance:registro_add'
    path('novo/', RegistroManutencaoCreateView.as_view(), name='registro_add'),
]