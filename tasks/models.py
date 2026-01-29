from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# ======================================================
# 1. NUEVO MODELO: ETIQUETA (Marcadores de Terreno)
# ======================================================
class Etiqueta(models.Model):
    COLORES = [
        ('bg-primary', 'Azul (Estratégico)'),
        ('bg-secondary', 'Gris (General)'),
        ('bg-success', 'Verde (Logística/Ventas)'),
        ('bg-danger', 'Rojo (Crítico/Urgente)'),
        ('bg-warning text-dark', 'Amarillo (Alerta)'),
        ('bg-info text-dark', 'Celeste (Inteligencia)'),
        ('bg-dark', 'Negro (Operaciones Especiales)'),
    ]
    
    nombre = models.CharField(max_length=50)
    color = models.CharField(max_length=50, choices=COLORES, default='bg-secondary')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE) # Cada general tiene sus propias etiquetas

    def __str__(self):
        return self.nombre

# ======================================================
# 2. MODELO TAREA (Operación Principal)
# ======================================================
class Tarea(models.Model):
    ESTADOS_OPCIONES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    ]

    # Relaciones
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mis_tareas')

    # Campos Básicos
    titulo = models.CharField(max_length=200, verbose_name="Título de la Tarea")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    # Fechas
    fecha_objetivo = models.DateField(verbose_name="Fecha Límite (Objetivo)")
    fecha_cierre = models.DateField(null=True, blank=True, verbose_name="Fecha Real de Cierre")
    
    # Progreso
    avance = models.CharField(max_length=100, blank=True, verbose_name="Reporte de Avance")
    
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS_OPCIONES, 
        default='PENDIENTE'
    )

    # --- CAMPO FALTANTE AGREGADO ---
    # Relación Muchos a Muchos con Etiquetas
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, related_name='tareas', verbose_name="Etiquetas")
    # -------------------------------

    # Colaboración
    compartida_con = models.ManyToManyField(
        User, 
        related_name='tareas_compartidas', 
        blank=True,
        verbose_name="Compartir con"
    )

    # Auditoría
    observaciones = models.TextField(blank=True, verbose_name="Observaciones Finales")
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

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
    
    # Archivos Adjuntos (Opción A)
    archivo = models.FileField(upload_to='adjuntos_tareas/', null=True, blank=True)
    
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario.username} - {self.tarea.titulo}"

# ======================================================
# 4. PERFIL DE USUARIO (Identidad)
# ======================================================
class Perfil(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    imagen = models.ImageField(default='default.jpg', upload_to='perfiles_fotos')

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