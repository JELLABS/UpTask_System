from django.contrib import admin
from .models import Tarea, Etiqueta, Perfil, HistorialAvance, Proyecto

class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'proyecto', 'fecha_objetivo', 'estado')
    list_filter = ('estado', 'usuario', 'proyecto')
    search_fields = ('titulo', 'usuario__username')
    filter_horizontal = ('etiquetas', 'compartida_con')

class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'presupuesto', 'fecha_inicio')
    filter_horizontal = ('equipo',)

admin.site.register(Tarea, TareaAdmin)
admin.site.register(Proyecto, ProyectoAdmin)
admin.site.register(Etiqueta)
admin.site.register(Perfil)
admin.site.register(HistorialAvance)