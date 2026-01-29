from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 1. IMPORTAR VISTAS DE AUTENTICACIÓN
from django.contrib.auth import views as auth_views 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tasks.urls')),
    
    # 2. RUTA DE SALIDA (LOGOUT)
    # Al salir, Django necesita saber que vista usar. Usamos la nativa.
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Opcional: Ruta de Login (si no la tenía definida en tasks/urls.py)
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)