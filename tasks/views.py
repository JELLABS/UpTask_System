import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q, Case, When, Value, IntegerField, Count, Sum
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from datetime import timedelta # <--- NECESARIO PARA EL RADAR DE FECHAS
from .models import Tarea, HistorialAvance, Perfil, Etiqueta, Proyecto
from .forms import TareaForm, HistorialForm, PerfilUpdateForm, EtiquetaForm, ProyectoForm, UserUpdateForm

# --- API BUSCADOR ---
@login_required
def buscar_usuarios(request):
    query = request.GET.get('q', '')
    proyecto_id = request.GET.get('pid', None)
    
    if not query or len(query) < 2: return JsonResponse([], safe=False)

    # --- CORRECCIÓN AQUÍ: .exclude(is_superuser=True) ---
    usuarios = User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).exclude(is_superuser=True) # <--- El Superusuario se vuelve invisible
    
    # Si estamos en contexto de proyecto...
    if proyecto_id:
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        # Aquí también podríamos filtrar, pero el filtro principal ya lo sacó.
        # Solo aseguramos que mostramos al dueño (si no es superuser) y al equipo.
        usuarios = usuarios.filter(Q(id=proyecto.usuario.id) | Q(proyectos_asignados=proyecto))

    usuarios = usuarios.distinct()[:5]
    
    resultados = []
    for u in usuarios:
        foto_url = '/media/default.jpg'
        if hasattr(u, 'perfil') and u.perfil.imagen:
            try: foto_url = u.perfil.imagen.url
            except: pass
        resultados.append({'id': u.id, 'username': u.username, 'text': f"@{u.username}", 'foto': foto_url})
    
    return JsonResponse(resultados, safe=False)

# --- GESTIÓN DE PROYECTOS ---
# En tasks/views.py

@login_required
def lista_proyectos(request):
    # 1. Base: Proyectos donde soy dueño o equipo
    proyectos = Proyecto.objects.filter(
        Q(usuario=request.user) | Q(equipo=request.user)
    ).distinct().order_by('-creado_el')

    # 2. Captura de Filtros
    query = request.GET.get('q') or ""
    status_filter = request.GET.get('status')

    # 3. Aplicar Filtro de Búsqueda (Texto)
    if query:
        proyectos = proyectos.filter(
            Q(titulo__icontains=query) | Q(descripcion__icontains=query)
        )

    # 4. Aplicar Filtro de Estado (Botones)
    if status_filter == 'activos':
        # Muestra todo lo que NO esté terminado ni cancelado
        proyectos = proyectos.exclude(estado__in=['COMPLETADA', 'CANCELADO'])
    elif status_filter == 'completados':
        proyectos = proyectos.filter(estado='COMPLETADA')
    # Si es 'todos' o no hay filtro, no hacemos nada (pasa todo)

    # 5. Paginación
    paginator = Paginator(proyectos, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'tasks/lista_proyectos.html', {
        'proyectos': page_obj, 
        'query': query,
        'status_filter': status_filter # Pasamos el filtro para mantener el botón activo
    })

@login_required
def crear_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            p.usuario = request.user
            p.save()
            form.save_m2m()
            messages.success(request, 'Proyecto iniciado correctamente.')
            return redirect('detalle_proyecto', pk=p.id)
    else: form = ProyectoForm()
    return render(request, 'tasks/formulario_proyecto.html', {'form': form, 'titulo': 'Nuevo Proyecto'})

@login_required
def detalle_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, id=pk)
    # Seguridad: Solo dueño o equipo entra
    if proyecto.usuario != request.user and request.user not in proyecto.equipo.all():
        messages.error(request, 'Acceso denegado: Zona restringida.')
        return redirect('lista_proyectos')

    tareas = proyecto.tareas.all().order_by('fecha_objetivo')
    
    contexto = {
        'proyecto': proyecto,
        'tareas': tareas,
        'gastado': proyecto.presupuesto_gastado(),
        'restante': proyecto.presupuesto_restante(),
        'avance': proyecto.porcentaje_avance()
    }
    return render(request, 'tasks/detalle_proyecto.html', contexto)

@login_required
def editar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, id=pk)
    # Seguridad: Solo el dueño edita el proyecto
    if proyecto.usuario != request.user:
        messages.error(request, "Solo el Comandante (Creador) puede modificar el proyecto.")
        return redirect('detalle_proyecto', pk=pk)

    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proyecto actualizado.')
            return redirect('detalle_proyecto', pk=pk)
    else: form = ProyectoForm(instance=proyecto)
    return render(request, 'tasks/formulario_proyecto.html', {'form': form, 'titulo': 'Editar Proyecto'})

@login_required
def eliminar_proyecto(request, pk):
    proyecto = get_object_or_404(Proyecto, id=pk)
    if proyecto.usuario != request.user: return redirect('lista_proyectos')
    
    if request.method == 'POST':
        proyecto.delete()
        messages.success(request, 'Proyecto desmantelado.')
        return redirect('lista_proyectos')
    return render(request, 'tasks/eliminar_generico.html', {'objeto': proyecto, 'tipo': 'Proyecto', 'cancel_url': 'lista_proyectos'})

# --- DASHBOARD & OPERACIONES ---
# tasks/views.py

# tasks/views.py

@login_required
def home(request):
    # 1. Base de operaciones
    misiones = Tarea.objects.filter(
        Q(usuario=request.user) | 
        Q(compartida_con=request.user) | 
        Q(responsable=request.user)
    ).distinct()
    
    # 2. Captura de parámetros (AHORA SON INDEPENDIENTES)
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '') # Antes era 'filter', ahora 'status'
    time_filter = request.GET.get('time', '')     # Nuevo canal para tiempo
    ownership = request.GET.get('ownership', '')
    
    hoy = timezone.now().date()

    # 3. Filtro de Búsqueda
    if search:
        misiones = misiones.filter(titulo__icontains=search)
    
    # 4. APLICACIÓN DE FILTROS CRUZADOS (Uno no anula al otro)
    
    # A) Filtro de Estado
    if status_filter:
        misiones = misiones.filter(estado=status_filter)

    # B) Filtro de Tiempo
    if time_filter == 'retrasadas':
        misiones = misiones.filter(fecha_objetivo__lt=hoy).exclude(estado='COMPLETADA')
    elif time_filter == 'hoy':
        misiones = misiones.filter(fecha_objetivo=hoy)
    elif time_filter == 'proximas':
        misiones = misiones.filter(fecha_objetivo__gt=hoy)

    # 5. Filtro de Propiedad
    if ownership == 'mis_tareas':
        misiones = misiones.filter(usuario=request.user)
    elif ownership == 'compartidas':
        misiones = misiones.filter(compartida_con=request.user)
    
    # 6. Ordenamiento y Paginación
    misiones = misiones.annotate(
        orden_estado=Case(
            When(estado='COMPLETADA', then=Value(3)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('orden_estado', 'fecha_objetivo')
    
    paginator = Paginator(misiones, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Pasamos ambas variables al template para mantener los botones activos
    return render(request, 'tasks/home.html', {
        'misiones': page_obj, 
        'search_query': search, 
        'status_filter': status_filter, 
        'time_filter': time_filter, # <--- Enviamos esto al HTML
        'ownership_filter': ownership, 
        'hoy': hoy
    })

@login_required
def dashboard(request):
    # 1. BASE DE DATOS
    mis_misiones = Tarea.objects.filter(Q(usuario=request.user) | Q(compartida_con=request.user)).distinct()
    mis_proyectos = Proyecto.objects.filter(Q(usuario=request.user) | Q(equipo=request.user)).distinct()
    
    # 2. KPIS BÁSICOS
    total_pendientes = mis_misiones.filter(estado='PENDIENTE').count()
    total_proceso = mis_misiones.filter(estado='EN_PROCESO').count()
    total_completadas = mis_misiones.filter(estado='COMPLETADA').count()
    total_revision = mis_misiones.filter(estado='EN_REVISION').count()
    total_espera = mis_misiones.filter(estado='EN_ESPERA').count()

    # CORRECCIÓN DE ETIQUETAS (INTELIGENCIA DE USO REAL)
    # =========================================================
    # Antes: Buscaba solo las creadas por el usuario (ERROR)
    # Ahora: Busca etiquetas presentes en 'mis_misiones', sin importar quién las creó.
    
    etiquetas_data = Etiqueta.objects.filter(
        tareas__in=mis_misiones
    ).annotate(
        # Contamos cuántas veces aparece esta etiqueta SOLO en mis misiones
        num_uso=Count('tareas', filter=Q(tareas__in=mis_misiones))
    ).order_by('-num_uso').distinct()[:5]
    
    # =========================================================
    
    # 4. FINANZAS GLOBALES (Solo Proyectos Propios)
    proyectos_propios = Proyecto.objects.filter(usuario=request.user)
    total_presupuesto = proyectos_propios.aggregate(Sum('presupuesto'))['presupuesto__sum'] or 0
    total_gastado = HistorialAvance.objects.filter(tarea__proyecto__in=proyectos_propios).aggregate(Sum('monto'))['monto__sum'] or 0

    # 5. --- NUEVO: RADAR DE VENCIMIENTOS (Próximos 7 días) ---
    hoy = timezone.now().date()
    limite = hoy + timedelta(days=7)
    vencimientos = mis_misiones.filter(
        fecha_objetivo__range=[hoy, limite]
    ).exclude(estado='COMPLETADA').order_by('fecha_objetivo')[:5]

    # 6. --- NUEVO: BITÁCORA EN VIVO (Últimos 5 movimientos) ---
    # Traemos historial de MIS tareas o tareas compartidas conmigo
    ultimos_movimientos = HistorialAvance.objects.filter(
        tarea__in=mis_misiones
    ).order_by('-fecha')[:5]

    # 7. --- NUEVO: DETALLE DE PROYECTOS (Para la tabla) ---
    # Calculamos datos al vuelo para mostrarlos en la tabla
    detalle_proyectos = []
    for p in mis_proyectos:
        gastado = p.presupuesto_gastado()
        avance = p.porcentaje_avance()
        detalle_proyectos.append({
            'info': p,
            'gastado': gastado,
            'avance': avance,
            'restante': p.presupuesto - gastado
        })

    contexto = {
        # KPIs
        'total_pendientes': total_pendientes,
        'total_proceso': total_proceso,
        'total_revision': total_revision,
        'total_completadas': total_completadas,
        'total_espera': total_espera,
        'total_general': mis_misiones.count(),
        
        # Gráficos
        'etiqueta_nombres': [e.nombre for e in etiquetas_data],
        'etiqueta_cantidades': [e.num_uso for e in etiquetas_data],
        
        # Finanzas
        'total_presupuesto': total_presupuesto,
        'total_gastado': total_gastado,
        'saldo_restante': total_presupuesto - total_gastado,

        # --- NUEVOS DATOS TÁCTICOS ---
        'vencimientos': vencimientos,
        'ultimos_movimientos': ultimos_movimientos,
        'detalle_proyectos': detalle_proyectos,
    }
    return render(request, 'tasks/dashboard.html', contexto)

@login_required
def crear_tarea(request):
    pid = request.GET.get('proyecto_id')
    p_obj = get_object_or_404(Proyecto, id=pid) if pid else None
    
    if request.method == 'POST':
        form = TareaForm(request.POST, user=request.user, proyecto_vinculado=p_obj)
        if form.is_valid():
            t = form.save(commit=False)
            t.usuario = request.user
            if p_obj: t.proyecto = p_obj
            t.save()
            form.save_m2m()
            
            # Notificar por correo
            destinatarios = [u.email for u in t.compartida_con.all() if u.email]
            if t.responsable and t.responsable.email: destinatarios.append(t.responsable.email)
            
            if destinatarios:
                send_mail(
                    f"Nueva Misión: {t.titulo}",
                    f"Asignada por @{request.user.username}.\nProyecto: {t.proyecto}\nVer en UpTask.",
                    settings.EMAIL_HOST_USER,
                    list(set(destinatarios)), # Eliminar duplicados
                    fail_silently=True
                )

            messages.success(request, 'Tarea creada.')
            if t.proyecto: return redirect('detalle_proyecto', pk=t.proyecto.id)
            return redirect('home')
    else:
        initial = {'proyecto': p_obj} if p_obj else {}
        form = TareaForm(user=request.user, proyecto_vinculado=p_obj, initial=initial)
    return render(request, 'tasks/formulario_tarea.html', {'form': form, 'titulo_pagina': 'Nueva Tarea', 'proyecto_id': pid})

@login_required
def editar_tarea(request, pk):
    t = get_object_or_404(Tarea, id=pk)
    
    # --- SEGURIDAD: SOLO EL DUEÑO EDITA ---
    if t.usuario != request.user:
        messages.error(request, "Solo el Comandante (Creador) puede modificar las órdenes.")
        # Redirigimos al colaborador a la pantalla de reporte
        return redirect('reportar_avance', pk=pk)

    if request.method == 'POST':
        form = TareaForm(request.POST, instance=t, user=request.user, proyecto_vinculado=t.proyecto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Órdenes actualizadas.')
            if t.proyecto: return redirect('detalle_proyecto', pk=t.proyecto.id)
            return redirect('home')
    else:
        form = TareaForm(instance=t, user=request.user, proyecto_vinculado=t.proyecto)
    
    resp_init = {'id': t.responsable.id, 'text': f"@{t.responsable.username}"} if t.responsable else None
    return render(request, 'tasks/formulario_tarea.html', {'form': form, 'titulo_pagina': 'Editar', 'responsable_inicial': resp_init, 'proyecto_id': t.proyecto.id if t.proyecto else None})

@login_required
def eliminar_tarea(request, pk):
    t = get_object_or_404(Tarea, id=pk)
    if t.usuario != request.user: return redirect('home')
    p_orig = t.proyecto
    if request.method == 'POST':
        t.delete()
        messages.success(request, 'Misión abortada (Eliminada).')
        if p_orig: return redirect('detalle_proyecto', pk=p_orig.id)
        return redirect('home')
    return render(request, 'tasks/eliminar_generico.html', {'objeto': t, 'tipo': 'Tarea', 'cancel_url': 'home'})

@login_required
def crear_etiqueta(request):
    if request.method == 'POST':
        f = EtiquetaForm(request.POST)
        if f.is_valid(): e=f.save(commit=False); e.usuario=request.user; e.save(); messages.success(request, 'Etiqueta creada.'); return redirect('crear_tarea')
    else: f = EtiquetaForm()
    return render(request, 'tasks/crear_etiqueta.html', {'form': f})

@login_required
def cambiar_estado(request, pk, nuevo_estado):
    t = get_object_or_404(Tarea, id=pk)
    # Cualquiera asignado puede cambiar estado
    if t.usuario == request.user or request.user in t.compartida_con.all() or t.responsable == request.user:
        t.estado = nuevo_estado
        t.fecha_cierre = timezone.now().date() if nuevo_estado == 'COMPLETADA' else None
        t.save()
        messages.success(request, f'Estado actualizado: {nuevo_estado}')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def reportar_avance(request, pk):
    tarea = get_object_or_404(Tarea, id=pk)
    
    # Validación de acceso
    if tarea.usuario != request.user and request.user not in tarea.compartida_con.all() and tarea.responsable != request.user:
        messages.error(request, 'No tienes permiso en esta misión.')
        return redirect('home')

    if request.method == 'POST':
        form = HistorialForm(request.POST, request.FILES) 
        if form.is_valid():
            # 1. Guardar el Historial (Bitácora)
            avance = form.save(commit=False)
            avance.tarea = tarea
            avance.usuario = request.user
            avance.save()

            # 2. Actualizar el Estado de la Tarea (Si se seleccionó uno nuevo)
            nuevo_estado = form.cleaned_data.get('nuevo_estado')
            estado_cambiado = False
            if nuevo_estado and nuevo_estado != tarea.estado:
                tarea.estado = nuevo_estado
                if nuevo_estado == 'COMPLETADA':
                    tarea.fecha_cierre = timezone.now().date()
                else:
                    tarea.fecha_cierre = None
                tarea.save()
                estado_cambiado = True

            # 3. Notificar al Dueño (Radio Frecuencia)
            # Si yo NO soy el dueño, le aviso al dueño que reporté
            if tarea.usuario != request.user and tarea.usuario.email:
                asunto = f"Avance en: {tarea.titulo}"
                mensaje = f"""
                El agente @{request.user.username} ha reportado novedades.
                
                Comentario: {avance.comentario}
                Gasto: ${avance.monto}
                Nuevo Estado: {nuevo_estado if estado_cambiado else 'Sin cambios'}
                """
                send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [tarea.usuario.email], fail_silently=True)

            messages.success(request, 'Bitácora actualizada y órdenes ejecutadas.')
            
            # Retorno inteligente
            if tarea.proyecto: return redirect('detalle_proyecto', pk=tarea.proyecto.id)
            return redirect('home')
    else:
        # Pre-cargamos el estado actual para que el usuario vea en qué está
        form = HistorialForm(initial={'nuevo_estado': tarea.estado})

    return render(request, 'tasks/reportar_avance.html', {'form': form, 'tarea': tarea})

# En tasks/views.py

@login_required
def perfil(request):
    if request.method == 'POST':
        # Instanciamos ambos formularios con los datos que llegan (POST y FILES)
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = PerfilUpdateForm(request.POST, request.FILES, instance=request.user.perfil)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Su ficha personal ha sido actualizada.')
            return redirect('perfil')
    else:
        # Carga inicial de datos
        u_form = UserUpdateForm(instance=request.user)
        p_form = PerfilUpdateForm(instance=request.user.perfil)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'tasks/perfil.html', context)

def signup(request):
    if request.method == 'POST':
        f = UserCreationForm(request.POST)
        if f.is_valid(): login(request, f.save()); return redirect('dashboard')
    else: f = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': f})

@login_required
def exportar_csv(request):
    r = HttpResponse(content_type='text/csv')
    r['Content-Disposition'] = 'attachment; filename="reporte.csv"'
    w = csv.writer(r)
    w.writerow(['ID', 'Título', 'Estado', 'Proyecto'])
    for m in Tarea.objects.filter(Q(usuario=request.user)|Q(compartida_con=request.user)): w.writerow([m.id, m.titulo, m.get_estado_display(), m.proyecto])
    return r

def landing_page(request):
    if request.user.is_authenticated: return redirect('dashboard')
    return render(request, 'tasks/landing.html')

@login_required
def detalle_tarea(request, pk):
    tarea = get_object_or_404(Tarea, pk=pk)
    
    # --- CORRECCIÓN AQUÍ ---
    # Usamos '-fecha' porque así se llama el campo en su base de datos
    bitacoras = HistorialAvance.objects.filter(tarea=tarea).order_by('-fecha')
    
    return render(request, 'tasks/detalle_tarea.html', {
        'tarea': tarea, 
        'bitacoras': bitacoras 
    })