from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ======================================================
# 1. NUEVO MODELO: ETIQUETA (Marcadores de Terreno)
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
# 2. MODELO TAREA (Operación Principal)
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
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_objetivo = models.DateField()
    fecha_cierre = models.DateField(null=True, blank=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    
    avance = models.CharField(max_length=100, blank=True, help_text="Ej: 50%, En validación...")
    observaciones = models.TextField(blank=True)

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tareas_creadas')
    compartida_con = models.ManyToManyField(User, related_name='tareas_asignadas', blank=True)
    etiquetas = models.ManyToManyField(Etiqueta, blank=True)

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ['fecha_objetivo']

    def __str__(self):
        return f"{self.titulo} ({self.usuario.username})"

# ======================================================
# 3. HISTORIAL Y ADJUNTOS (Bitácora)
# ======================================================
class HistorialAvance(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    comentario = models.TextField()
    archivo = models.FileField(upload_to='archivos_adjuntos', blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.fecha.strftime('%d/%m %H:%M')}"

# ======================================================
# 4. PERFIL DE USUARIO (Identidad)
# ======================================================
class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='perfiles_fotos', default='default.jpg')
    
    def __str__(self):
        return f'Perfil de {self.usuario.username}'

# Señales para crear perfil automático
@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        Perfil.objects.create(usuario=instance)

@receiver(post_save, sender=User)
def guardar_perfil(sender, instance, **kwargs):
    instance.perfil.save()