from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# ======================================================
# 1. MODELO ETIQUETA
# ======================================================
class Etiqueta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='etiquetas')
    nombre = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default='bg-primary', choices=[
        ('bg-primary', 'Azul'),
        ('bg-secondary', 'Gris'),
        ('bg-success', 'Verde'),
        ('bg-danger', 'Rojo'),
        ('bg-warning text-dark', 'Amarillo'),
        ('bg-info text-dark', 'Celeste'),
        ('bg-dark', 'Negro'),
    ])

    def __str__(self):
        return self.nombre

# ======================================================
# 2. MODELO: PROYECTO
# ======================================================
class Proyecto(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proyectos_creados')
    equipo = models.ManyToManyField(User, related_name='proyectos_asignados', blank=True)
    
    # FINANZAS
    presupuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField(null=True, blank=True)
    creado_el = models.DateTimeField(auto_now_add=True)

    # --- AGREGUE ESTO DE NUEVO ---
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS, default='EN_PROCESO')
    # -----------------------------

    def __str__(self):
        return self.titulo

    def presupuesto_gastado(self):
        # Sumamos los montos reportados en el historial
        gastado = HistorialAvance.objects.filter(tarea__proyecto=self).aggregate(total=models.Sum('monto'))['total']
        return gastado or 0

    def presupuesto_restante(self):
        return self.presupuesto - self.presupuesto_gastado()

    def porcentaje_avance(self):
        total_tareas = self.tareas.count()
        if total_tareas == 0: return 0
        completadas = self.tareas.filter(estado='COMPLETADA').count()
        return int((completadas / total_tareas) * 100)

# ======================================================
# 3. MODELO TAREA (CORREGIDO)
# ======================================================
class Tarea(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_ESPERA', 'En Espera'),
        ('EN_PROCESO', 'En Progreso'),
        ('EN_REVISION', 'En Revisión'),
        ('COMPLETADA', 'Completada'),
    ]

    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='tareas', null=True, blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_objetivo = models.DateField()
    fecha_cierre = models.DateField(null=True, blank=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    avance = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tareas_creadas')
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tareas_responsable')
    compartida_con = models.ManyToManyField(User, related_name='tareas_asignadas', blank=True)
    
    # --- CAMBIO CRÍTICO AQUÍ ABAJO ---
    # Agregamos related_name='tareas' para que la etiqueta sepa contar sus tareas
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, related_name='tareas')

    def __str__(self):
        return f"{self.titulo}"

    class Meta:
        ordering = ['fecha_objetivo']

# ======================================================
# 4. HISTORIAL
# ======================================================
class HistorialAvance(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    comentario = models.TextField()
    archivo = models.FileField(upload_to='archivos_adjuntos', blank=True, null=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.fecha.strftime('%d/%m %H:%M')}"

# ======================================================
# 5. PERFIL
# ======================================================
class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='perfiles_fotos', default='default.jpg')
    
    def __str__(self):
        return f'Perfil de {self.usuario.username}'

@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created: Perfil.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def guardar_perfil(sender, instance, **kwargs):
    instance.perfil.save()