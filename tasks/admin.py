from django.contrib import admin
from .models import Tarea, Etiqueta, Perfil, HistorialAvance

# 1. Configuración para TAREAS
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'fecha_objetivo', 'estado', 'get_etiquetas')
    list_filter = ('estado', 'usuario', 'fecha_objetivo', 'etiquetas')
    search_fields = ('titulo', 'usuario__username', 'descripcion')
    
    # Widget especial para seleccionar muchas etiquetas/usuarios fácilmente
    filter_horizontal = ('etiquetas', 'compartida_con')

    # Método para mostrar etiquetas en la lista (Django no muestra ManyToMany directo)
    def get_etiquetas(self, obj):
        return ", ".join([e.nombre for e in obj.etiquetas.all()])
    get_etiquetas.short_description = 'Etiquetas'

# 2. Configuración para ETIQUETAS
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'color', 'usuario')
    list_filter = ('usuario', 'color')

# 3. Configuración para HISTORIAL (Bitácora)
class HistorialAdmin(admin.ModelAdmin):
    list_display = ('tarea', 'usuario', 'fecha', 'comentario')
    list_filter = ('usuario', 'fecha')

# --- REGISTRO DE TROPAS ---
admin.site.register(Tarea, TareaAdmin)
admin.site.register(Etiqueta, EtiquetaAdmin) # <--- ¡Aquí está lo nuevo!
admin.site.register(Perfil)
admin.site.register(HistorialAvance, HistorialAdmin)