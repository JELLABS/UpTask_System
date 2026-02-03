from django.urls import path
from . import views

urlpatterns = [
    # 1. RUTAS PRINCIPALES
    path('tablero/', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # 2. PROYECTOS (ASANA)
    path('proyectos/', views.lista_proyectos, name='lista_proyectos'),
    path('crear-proyecto/', views.crear_proyecto, name='crear_proyecto'),
    path('proyecto/<int:pk>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('proyecto/editar/<int:pk>/', views.editar_proyecto, name='editar_proyecto'),
    path('proyecto/eliminar/<int:pk>/', views.eliminar_proyecto, name='eliminar_proyecto'),

    # 3. OPERACIONES TÁCTICAS
    path('crear-tarea/', views.crear_tarea, name='crear_tarea'),
    path('crear-etiqueta/', views.crear_etiqueta, name='crear_etiqueta'),
    path('editar-tarea/<int:pk>/', views.editar_tarea, name='editar_tarea'),
    path('eliminar-tarea/<int:pk>/', views.eliminar_tarea, name='eliminar_tarea'),
    path('tarea/<int:pk>/detalle/', views.detalle_tarea, name='detalle_tarea'),
    
    # 4. ACCIONES
    path('cambiar-estado/<int:pk>/<str:nuevo_estado>/', views.cambiar_estado, name='cambiar_estado'),
    path('reportar-avance/<int:pk>/', views.reportar_avance, name='reportar_avance'),
    
    # 5. SISTEMA
    path('perfil/', views.perfil, name='perfil'),
    path('exportar-csv/', views.exportar_csv, name='exportar_csv'),
    path('signup/', views.signup, name='signup'),
    path('api/buscar-usuarios/', views.buscar_usuarios, name='buscar_usuarios'),
]