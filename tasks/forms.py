from django import forms
from django.db.models import Q 
from django.contrib.auth.models import User
from .models import Tarea, HistorialAvance, Perfil, Etiqueta, Proyecto

# ======================================================
# 1. FORMULARIO DE PROYECTOS
# ======================================================
class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = ['titulo', 'descripcion', 'presupuesto', 'fecha_inicio', 'fecha_fin', 'equipo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del Proyecto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'presupuesto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'fecha_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'equipo': forms.SelectMultiple(attrs={'style': 'display:none;'}),
        }

# ======================================================
# 2. FORMULARIO DE TAREAS
# ======================================================
class TareaForm(forms.ModelForm):
    responsable = forms.ModelChoiceField(
        queryset=User.objects.all(), 
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Tarea
        fields = ['titulo', 'descripcion', 'proyecto', 'costo', 'fecha_objetivo', 'estado', 'responsable', 'etiquetas', 'avance', 'observaciones', 'compartida_con']
        
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'proyecto': forms.Select(attrs={'class': 'form-select'}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Costo Estimado (Opcional)'}),
            'fecha_objetivo': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'responsable': forms.HiddenInput(),
            'avance': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'etiquetas': forms.CheckboxSelectMultiple(),
            'compartida_con': forms.SelectMultiple(attrs={'style': 'display:none;'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.proyecto_vinculado = kwargs.pop('proyecto_vinculado', None) 
        super(TareaForm, self).__init__(*args, **kwargs)
        self.fields['responsable'].queryset = User.objects.all()

        if self.user:
            self.fields['proyecto'].queryset = Proyecto.objects.filter(
                Q(usuario=self.user) | Q(equipo=self.user)
            ).distinct()

        if self.proyecto_vinculado:
            equipo_autorizado = User.objects.filter(
                Q(id=self.proyecto_vinculado.usuario.id) | 
                Q(proyectos_asignados=self.proyecto_vinculado)
            ).distinct()
            self.fields['responsable'].queryset = equipo_autorizado
            self.fields['compartida_con'].queryset = equipo_autorizado
            self.fields['proyecto'].initial = self.proyecto_vinculado

# ======================================================
# 3. FORMULARIO DE HISTORIAL (MEJORADO)
# ======================================================
class HistorialForm(forms.ModelForm):
    # Campo extra: No se guarda en Historial, sirve para actualizar la Tarea
    nuevo_estado = forms.ChoiceField(
        choices=Tarea.ESTADOS, 
        required=False, 
        label="¿Actualizar Estado?",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = HistorialAvance
        fields = ['comentario', 'monto', 'archivo'] 
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Describa el avance o gasto...'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm'}),
        }

class EtiquetaForm(forms.ModelForm):
    class Meta:
        model = Etiqueta
        fields = ['nombre', 'color']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.Select(attrs={'class': 'form-select'}),
        }

class PerfilUpdateForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['imagen']