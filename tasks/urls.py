from django.urls import path
from . import views

urlpatterns = [
    # 1. RUTAS PRINCIPALES
    path('tablero/', views.home, name='home'),          # El Tablero con las tarjetas
    path('dashboard/', views.dashboard, name='dashboard'), # Las Estadísticas
    
    # 2. OPERACIONES (Crear/Editar)
    path('crear-tarea/', views.crear_tarea, name='crear_tarea'),
    path('crear-etiqueta/', views.crear_etiqueta, name='crear_etiqueta'), # <--- Faltaba esta
    path('editar-tarea/<int:pk>/', views.editar_tarea, name='editar_tarea'),
    path('eliminar-tarea/<int:pk>/', views.eliminar_tarea, name='eliminar_tarea'),
    
    # 3. ACCIONES RÁPIDAS
    path('cambiar-estado/<int:pk>/<str:nuevo_estado>/', views.cambiar_estado, name='cambiar_estado'),
    path('reportar-avance/<int:pk>/', views.reportar_avance, name='reportar_avance'),
    
    # 4. EXTRAS
    path('perfil/', views.perfil, name='perfil'),
    path('exportar-csv/', views.exportar_csv, name='exportar_csv'),
    path('signup/', views.signup, name='signup'),

    # 5. INTELIGENCIA (API)
    path('api/buscar-usuarios/', views.buscar_usuarios, name='buscar_usuarios'),
]