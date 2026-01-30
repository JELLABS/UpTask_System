import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q, Case, When, Value, IntegerField, Count # <--- IMPORTANTE: Case/When para ordenar
from django.contrib.auth.models import User
from django.core.mail import send_mail # <--- IMPORTANTE: Para enviar correos
from django.conf import settings
from django.core.paginator import Paginator

from .models import Tarea, HistorialAvance, Perfil, Etiqueta
from .forms import TareaForm, HistorialForm, PerfilUpdateForm, EtiquetaForm

# --- API BUSCADOR ---
@login_required
def buscar_usuarios(request):
    query = request.GET.get('q', '')
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)

    usuarios = User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).exclude(id=request.user.id).distinct()[:5]

    resultados = []
    for u in usuarios:
        foto_url = '/media/default.jpg'
        if hasattr(u, 'perfil') and u.perfil.imagen:
            foto_url = u.perfil.imagen.url

        resultados.append({
            'id': u.id,
            'username': u.username,
            'text': f"@{u.username}",
            'foto': foto_url
        })
    return JsonResponse(resultados, safe=False)

# --- VISTAS ---

@login_required
def home(request):
    # 1. Filtro base
    misiones = Tarea.objects.filter(
        Q(usuario=request.user) | Q(compartida_con=request.user)
    ).distinct()

    # 2. Filtros de búsqueda visual
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

    # 3. ORDENAMIENTO TÁCTICO (Cirugía solicitada)
    # Primero las NO completadas (1), luego las completadas (2).
    # Dentro de eso, ordenadas por fecha objetivo.
    misiones = misiones.annotate(
        orden_estado=Case(
            When(estado='COMPLETADA', then=Value(2)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('orden_estado', 'fecha_objetivo')

    paginator = Paginator(misiones, 5) 
    page_obj = paginator.get_page(request.GET.get('page'))

    contexto = {
        'misiones': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'ownership_filter': ownership_filter,
        'hoy': timezone.now().date()
    }
    return render(request, 'tasks/home.html', contexto)


# 2. MODIFICAR LA VISTA DASHBOARD COMPLETA
@login_required
def dashboard(request):
    # Filtramos las tareas del usuario
    mis_misiones = Tarea.objects.filter(
        Q(usuario=request.user) | Q(compartida_con=request.user)
    ).distinct()

    # DATOS PARA GRÁFICO DE DONA (ESTADOS)
    total_pendientes = mis_misiones.filter(estado='PENDIENTE').count()
    total_proceso = mis_misiones.filter(estado='EN_PROCESO').count()
    total_completadas = mis_misiones.filter(estado='COMPLETADA').count()
    # Sumamos Espera y Revisión como "Otros" para simplificar el gráfico, o los mostramos todos.
    # Vamos a mostrarlos todos en el template.

    # DATOS PARA GRÁFICO DE BARRAS (ETIQUETAS)
    # Buscamos las etiquetas del usuario y contamos cuántas tareas tienen
    etiquetas_data = Etiqueta.objects.filter(usuario=request.user).annotate(num_tareas=Count('tarea')).order_by('-num_tareas')[:5]
    
    # Preparamos listas para JavaScript
    etiqueta_nombres = [e.nombre for e in etiquetas_data]
    etiqueta_cantidades = [e.num_tareas for e in etiquetas_data]

    contexto = {
        'total_pendientes': total_pendientes,
        'total_espera': mis_misiones.filter(estado='EN_ESPERA').count(),
        'total_proceso': total_proceso,
        'total_revision': mis_misiones.filter(estado='EN_REVISION').count(),
        'total_completadas': total_completadas,
        'total_general': mis_misiones.count(),
        
        # Datos para los gráficos
        'etiqueta_nombres': etiqueta_nombres,
        'etiqueta_cantidades': etiqueta_cantidades,
    }
    return render(request, 'tasks/dashboard.html', contexto)

@login_required
def crear_tarea(request):
    if request.method == 'POST':
        form = TareaForm(request.POST, user=request.user) 
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.usuario = request.user
            tarea.save() 
            form.save_m2m() # Guarda etiquetas y compartidos
            
            # --- OPERACIÓN RADIO FRECUENCIA (ENVIAR EMAIL) ---
            destinatarios = []
            for colaborador in tarea.compartida_con.all():
                if colaborador.email:
                    destinatarios.append(colaborador.email)
            
            if destinatarios:
                asunto = f"Nueva Misión Asignada: {tarea.titulo}"
                mensaje = f"""
                Atención Soldado,
                
                El Manager @{request.user.username} le ha asignado una nueva misión en UpTask.
                
                Misión: {tarea.titulo}
                Fecha Objetivo: {tarea.fecha_objetivo}
                
                Ingrese al cuartel para más detalles: https://www.uptask.com.ar
                
                Cambio y fuera.
                """
                try:
                    send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, destinatarios, fail_silently=True)
                except:
                    pass # Si falla el correo, no detenemos la operación
            # -------------------------------------------------

            return redirect('home')
    else:
        form = TareaForm(user=request.user)

    contexto = {'form': form, 'titulo_pagina': 'Crear Nueva Tarea'}
    return render(request, 'tasks/formulario_tarea.html', contexto)

@login_required
def crear_etiqueta(request):
    if request.method == 'POST':
        form = EtiquetaForm(request.POST)
        if form.is_valid():
            etiqueta = form.save(commit=False)
            etiqueta.usuario = request.user
            etiqueta.save()
            return redirect('crear_tarea') 
    else:
        form = EtiquetaForm()
    contexto = {'form': form}
    return render(request, 'tasks/crear_etiqueta.html', contexto)

@login_required
def editar_tarea(request, pk):
    tarea = get_object_or_404(Tarea, id=pk)
    if tarea.usuario != request.user:
        return redirect('home') 

    if request.method == 'POST':
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
    es_dueno = tarea.usuario == request.user
    es_colaborador = request.user in tarea.compartida_con.all()

    if es_dueno or es_colaborador:
        tarea.estado = nuevo_estado
        if nuevo_estado == 'COMPLETADA':
            tarea.fecha_cierre = timezone.now().date()
        else:
            tarea.fecha_cierre = None
        tarea.save()
        
    return redirect('home')

@login_required
def reportar_avance(request, pk):
    tarea = get_object_or_404(Tarea, id=pk)
    es_dueno = tarea.usuario == request.user
    es_colaborador = request.user in tarea.compartida_con.all()

    if not es_dueno and not es_colaborador:
        return redirect('home')

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
            messages.success(request, '¡Tu foto de perfil ha sido actualizada!')
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
            return redirect('dashboard') # Redirección a Dashboard al registrarse
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def exportar_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reporte_misiones.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Título', 'Estado', 'Fecha Objetivo', 'Etiquetas', 'Manager', 'Avance'])
    misiones = Tarea.objects.filter(Q(usuario=request.user) | Q(compartida_con=request.user)).distinct()
    for mision in misiones:
        tags = ", ".join([t.nombre for t in mision.etiquetas.all()])
        writer.writerow([
            mision.id,
            mision.titulo,
            mision.get_estado_display(),
            mision.fecha_objetivo,
            tags,
            mision.usuario.username,
            mision.avance or "0%"
        ])
    return response

def landing_page(request):
    # Si el usuario ya está logueado, quizás queramos mandarlo directo al dashboard
    # Si prefiere que vean la landing igual, borre las siguientes 2 líneas:
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    return render(request, 'tasks/landing.html')