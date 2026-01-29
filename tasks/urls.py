from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('crear/', views.crear_tarea, name='crear_tarea'), # <--- Ruta para crear tarea     
    path('editar/<int:pk>/', views.editar_tarea, name='editar_tarea'), # <--- Ruta para editar tarea     
    path('eliminar/<int:pk>/', views.eliminar_tarea, name='eliminar_tarea'), # <--- Ruta para eliminar tarea
    path('reportar_avance/<int:pk>/', views.reportar_avance, name='reportar_avance'), # <--- Ruta para reportar avance
    path('estado/<int:pk>/<str:nuevo_estado>/', views.cambiar_estado, name='cambiar_estado'), # <--- Ruta para cambiar estado
    path('dashboard/', views.dashboard, name='dashboard'), # <--- Nueva ruta para el dashboard
    path('perfil/', views.perfil, name='perfil'), # <--- Nueva ruta para el perfil
    path('signup/', views.signup, name='signup'), # <--- ESTA ES LA CLAVE PARA ARREGLAR EL ERROR
    path('exportar/', views.exportar_csv, name='exportar_csv'), # <--- Ruta para exportar tareas a CSV
    path('crear-etiqueta/', views.crear_etiqueta, name='crear_etiqueta'), # <--- Ruta para crear etiqueta
    path('api/buscar-usuarios/', views.buscar_usuarios, name='buscar_usuarios'), # <--- Ruta para la API de búsqueda de usuarios
]