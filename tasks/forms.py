from django import forms
from django.contrib.auth.models import User
from .models import Tarea, HistorialAvance, Perfil, Etiqueta

class TareaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Capturamos el usuario que viene desde la vista
        self.user = kwargs.pop('user', None)
        super(TareaForm, self).__init__(*args, **kwargs)
        
        if self.user:
            # FILTRO 1: Mostrar solo mis etiquetas
            self.fields['etiquetas'].queryset = Etiqueta.objects.filter(usuario=self.user)
            # FILTRO 2: No mostrarme a mí mismo en la lista de compartir
            self.fields['compartida_con'].queryset = User.objects.exclude(id=self.user.id)

    class Meta:
        model = Tarea
        fields = [
            'titulo', 'descripcion', 'fecha_objetivo', 
            'etiquetas', # <--- NUEVO CAMPO
            'avance', 'estado', 'compartida_con', 
            'observaciones'
        ]
        
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Revisar inventario'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_objetivo': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'avance': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 50%, Falta firma...'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            
            # Widget especial para etiquetas (Checkboxes horizontales)
            'etiquetas': forms.CheckboxSelectMultiple(attrs={'class': 'list-unstyled d-flex gap-3 flex-wrap'}),
            
            # Widget para compartir (Select múltiple)
            'compartida_con': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class HistorialForm(forms.ModelForm):
    class Meta:
        model = HistorialAvance
        fields = ['comentario', 'archivo']
        
        widgets = {
            'comentario': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': 'Escriba el reporte de avance...'
            }),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm'}),
        }

# tasks/forms.py

class EtiquetaForm(forms.ModelForm):
    class Meta:
        model = Etiqueta
        fields = ['nombre', 'color']
        
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Urgente, Ventas...'}),
            'color': forms.Select(attrs={'class': 'form-select'}),
        }

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['imagen']