import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Tarea, HistorialAvance, Perfil
from .forms import TareaForm, HistorialForm, PerfilUpdateForm

# ==========================================================
# VISTAS DE NAVEGACIÓN
# ==========================================================

@login_required
def home(request):
    misiones = Tarea.objects.filter(
        Q(usuario=request.user) | Q(compartida_con=request.user)
    ).distinct()

    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('filter', '')
    ownership_filter = request.GET.get('ownership', '')

    if search_query:
        misiones = misiones.filter(titulo__icontains=search_query)

    if status_filter:
        misiones = misiones.filter(estado=status_filter)

    if ownership_filter == 'mis_tareas':
        misiones = misiones.filter(usuario=request.user)
    elif ownership_filter == 'compartidas':
        misiones = misiones.filter(compartida_con=request.user)

    # Paginación (5 items)
    paginator = Paginator(misiones, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    contexto = {
        'misiones': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'ownership_filter': ownership_filter,
        'hoy': timezone.now().date()
    }
    return render(request, 'tasks/home.html', contexto)

@login_required
def dashboard(request):
    mis_misiones = Tarea.objects.filter(
        Q(usuario=request.user) | Q(compartida_con=request.user)
    ).distinct()

    contexto = {
        'total_pendientes': mis_misiones.filter(estado='PENDIENTE').count(),
        'total_proceso': mis_misiones.filter(estado='EN_PROCESO').count(),
        'total_completadas': mis_misiones.filter(estado='COMPLETADA').count(),
        'total_canceladas': mis_misiones.filter(estado='CANCELADA').count(),
        'total_general': mis_misiones.count()
    }
    return render(request, 'tasks/dashboard.html', contexto)

# ==========================================================
# VISTAS CRUD (ACTUALIZADAS PARA ETIQUETAS)
# ==========================================================

@login_required
def crear_tarea(request):
    if request.method == 'POST':
        # Pasamos el usuario para filtrar etiquetas
        form = TareaForm(request.POST, user=request.user) 
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.usuario = request.user
            tarea.save() 
            form.save_m2m() # Guarda etiquetas y compartidos
            return redirect('home')
    else:
        form = TareaForm(user=request.user)

    contexto = {'form': form, 'titulo_pagina': 'Crear Nueva Tarea'}
    return render(request, 'tasks/formulario_tarea.html', contexto)

@login_required
def editar_tarea(request, pk):
    tarea = get_object_or_404(Tarea, id=pk)

    if tarea.usuario != request.user:
        return redirect('home') 

    if request.method == 'POST':
        # Pasamos el usuario para filtrar etiquetas
        form = TareaForm(request.POST, instance=tarea, user=request.user)
        if form.is_valid():
            tarea_editada = form.save(commit=False)
            
            if tarea_editada.estado == 'COMPLETADA' and not tarea_editada.fecha_cierre:
                tarea_editada.fecha_cierre = timezone.now().date()
            elif tarea_editada.estado != 'COMPLETADA':
                tarea_editada.fecha_cierre = None
            
            tarea_editada.save()
            form.save_m2m()
            return redirect('home')
    else:
        form = TareaForm(instance=tarea, user=request.user)

    contexto = {'form': form, 'titulo_pagina': 'Editar Operación'}
    return render(request, 'tasks/formulario_tarea.html', contexto)

@login_required
def eliminar_tarea(request, pk):
    tarea = get_object_or_404(Tarea, id=pk)

    if tarea.usuario != request.user:
        return redirect('home') 

    if request.method == 'POST':
        tarea.delete()
        return redirect('home')

    contexto = {'tarea': tarea}
    return render(request, 'tasks/eliminar_tarea.html', contexto)

@login_required
def cambiar_estado(request, pk, nuevo_estado):
    tarea = get_object_or_404(Tarea, id=pk)
    
    # --- SEGURIDAD POLICÍA MILITAR ---
    # Permitimos cambio si es dueño O colaborador
    es_dueno = tarea.usuario == request.user
    es_colaborador = request.user in tarea.compartida_con.all()

    if es_dueno or es_colaborador:
        tarea.estado = nuevo_estado
        
        # Lógica de fecha de cierre
        if nuevo_estado == 'COMPLETADA':
            tarea.fecha_cierre = timezone.now().date()
        else:
            tarea.fecha_cierre = None
            
        tarea.save()
        
    return redirect('home')

# ==========================================================
# VISTAS DE REPORTE Y PERFIL
# ==========================================================

@login_required
def reportar_avance(request, pk):
    tarea = get_object_or_404(Tarea, id=pk)

    # --- SEGURIDAD POLICÍA MILITAR ---
    # Solo pasa si es el DUEÑO o si está en la lista de COLABORADORES
    es_dueno = tarea.usuario == request.user
    es_colaborador = request.user in tarea.compartida_con.all()

    if not es_dueno and not es_colaborador:
        return redirect('home') # ¡Acceso Denegado!
    # ---------------------------------

    if request.method == 'POST':
        form = HistorialForm(request.POST, request.FILES) 
        if form.is_valid():
            avance = form.save(commit=False)
            avance.tarea = tarea
            avance.usuario = request.user
            avance.save()
            return redirect('home')
    else:
        form = HistorialForm()

    contexto = {'form': form, 'tarea': tarea}
    return render(request, 'tasks/reportar_avance.html', contexto)

@login_required
def perfil(request):
    if request.method == 'POST':
        p_form = PerfilUpdateForm(request.POST, request.FILES, instance=request.user.perfil)
        if p_form.is_valid():
            p_form.save()
            messages.success(request, f'¡Tu foto de perfil ha sido actualizada!')
            return redirect('perfil')
    else:
        p_form = PerfilUpdateForm(instance=request.user.perfil)

    contexto = {'p_form': p_form}
    return render(request, 'tasks/perfil.html', contexto)

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def exportar_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_misiones.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Título', 'Estado', 'Fecha Objetivo', 'Etiquetas', 'Usuario', 'Avance'])

    misiones = Tarea.objects.filter(
        Q(usuario=request.user) | Q(compartida_con=request.user)
    ).distinct()

    for mision in misiones:
        # Lógica para exportar etiquetas en el CSV también
        tags = ", ".join([t.nombre for t in mision.etiquetas.all()])
        
        writer.writerow([
            mision.id,
            mision.titulo,
            mision.get_estado_display(),
            mision.fecha_objetivo,
            tags, # <--- Agregamos las etiquetas al reporte
            mision.usuario.username,
            mision.avance or "0%"
        ])

    return response