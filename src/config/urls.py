from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('components/', include('src.apps.components.urls', namespace='components')),

   
    path('maintenance/', include('src.apps.maintenance.urls')),
]