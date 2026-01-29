from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from tasks import views # Importante: Importar las vistas aquí también

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # RUTA RAÍZ (Vacía): Apunta directo al Dashboard
    path('', views.dashboard, name='root_dashboard'),
    
    # INCLUIR LAS RUTAS DE TASKS (Para que funcionen /tablero/, /dashboard/, etc.)
    path('', include('tasks.urls')),
    
    # AUTENTICACIÓN (Login/Logout)
    path('accounts/', include('django.contrib.auth.urls')),
]

# Configuración para ver imágenes en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)