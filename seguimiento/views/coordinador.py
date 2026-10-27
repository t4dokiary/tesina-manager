from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from seguimiento.models import (
    PerfilUsuario,
    Asesor,
    Coordinador,
    ConfiguracionUsuario,
    Convocatoria,
    ProyectoTesis, 
    EntregableVersion, 
    MinutaAsesoria,
)
from seguimiento.forms import (
    RegistroCoordinadorForm,
    EditarAsesorPorCoordinadorForm,
    EditarAlumnoPorCoordinadorForm,
    ConvocatoriaForm,
)


# =============================================================================
# PANEL DE CONTROL GENERAL DE COORDINACIÓN (CU04)
# =============================================================================

@login_required
def coordinador_dashboard(request):
    """Panel de Coordinación: Directorio de alumnos, docentes y métricas contra rezago (CU04)."""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'Acceso restringido a la Coordinación.')
        return redirect('index')

    # 1. Filtros de Asesores (Pendientes y Activos)
    asesores_pendientes = PerfilUsuario.objects.filter(
        tipo_usuario='ASESOR'
    ).filter(
        Q(cuenta_activa=False) | Q(estado_registro='PENDIENTE')
    ).select_related('user', 'datos_asesor')

    asesores_activos = PerfilUsuario.objects.filter(
        tipo_usuario='ASESOR',
        cuenta_activa=True
    ).exclude(
        estado_registro='PENDIENTE'
    ).select_related('user', 'datos_asesor')

    coordinadores_activos = PerfilUsuario.objects.filter(
        tipo_usuario='COORDINADOR'
    ).select_related('user', 'datos_coordinador')

    # 2. Directorio de alumnos y proyectos de tesis (Optimizado para evitar N+1 queries)
    alumnos_registrados = PerfilUsuario.objects.filter(
        tipo_usuario='ALUMNO'
    ).select_related('user', 'datos_alumno')

    # Diccionario en memoria con los proyectos existentes indexados por el id del alumno
    proyectos_map = {
        p.alumno_id: p 
        for p in ProyectoTesis.objects.select_related('asesor').all()
    }

    hoy = timezone.now().date()
    lista_alumnos = []

    for al in alumnos_registrados:
        proyecto = proyectos_map.get(al.id_usuario)

        matricula_str = "S/M"
        if hasattr(al, 'datos_alumno') and al.datos_alumno:
            matricula_str = al.datos_alumno.matricula

        # Cálculo dinámico de inactividad
        if proyecto and proyecto.fecha_ultimo_avance:
            fecha_ref = proyecto.fecha_ultimo_avance
            if hasattr(fecha_ref, 'date'):
                fecha_ref = fecha_ref.date()
        else:
            fecha_ref = al.fecha_registro.date() if hasattr(al, 'fecha_registro') else al.user.date_joined.date()

        dias_inactividad = max(0, (hoy - fecha_ref).days)
        alerta = (dias_inactividad > 30) and (not proyecto or proyecto.estado_proyecto != 'CONCLUIDO')[cite: 1, 2]

        lista_alumnos.append({
            'perfil': al,
            'matricula': matricula_str,
            'proyecto': proyecto,
            'ultimo_avance': fecha_ref,
            'dias_inactividad': dias_inactividad,
            'alerta': alerta,
        })

    return render(request, 'seguimiento/coordinador/dashboard.html', {
        'asesores_pendientes': asesores_pendientes,
        'asesores_activos': asesores_activos,
        'coordinadores_activos': coordinadores_activos,
        'lista_alumnos': lista_alumnos,
    })


# =============================================================================
# GESTIÓN Y VALIDACIÓN DE PROTOCOLOS DE TESIS
# =============================================================================

@login_required
def coordinador_validar_protocolos(request):
    """Lista las propuestas de protocolo pendientes de revisión por la Coordinación."""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'Acceso exclusivo para Coordinación.')
        return redirect('index')

    pendientes = ProyectoTesis.objects.filter(
        estado_proyecto__in=['PENDIENTE', 'PROPUESTA']
    ).select_related('alumno', 'asesor', 'convocatoria')

    aprobados = ProyectoTesis.objects.filter(
        estado_proyecto__in=['APROBADO', 'EN_DESARROLLO']
    ).select_related('alumno', 'asesor', 'convocatoria')

    asesores = PerfilUsuario.objects.filter(
        tipo_usuario='ASESOR',
        cuenta_activa=True
    ).exclude(estado_registro='PENDIENTE').select_related('datos_asesor')

    return render(request, 'seguimiento/coordinador/validar_protocolos.html', {
        'pendientes': pendientes,
        'aprobados': aprobados,
        'asesores': asesores,
    })


@login_required
def resolver_protocolo(request, id_proyecto, accion):
    """Aprueba o rechaza el protocolo de tesis."""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'Acceso exclusivo para Coordinación.')
        return redirect('index')

    proyecto = get_object_or_404(ProyectoTesis, id_proyecto=id_proyecto)
    hoy = timezone.now().date()

    if request.method == 'POST':
        observaciones = request.POST.get('comentarios', '').strip()
        proyecto.observaciones_coordinador = observaciones

        if accion == 'aprobar':
            nuevo_asesor_id = request.POST.get('asesor_id')
            if nuevo_asesor_id:
                proyecto.asesor = get_object_or_404(PerfilUsuario, id_usuario=nuevo_asesor_id, tipo_usuario='ASESOR')

            proyecto.estado_proyecto = 'APROBADO'
            proyecto.fecha_dictamen_coordinador = hoy
            proyecto.fecha_ultimo_avance = hoy
            proyecto.save()
            messages.success(request, f'Protocolo "{proyecto.titulo_tesis}" aprobado formalmente.')
        elif accion == 'rechazar':
            proyecto.estado_proyecto = 'RECHAZADO'
            proyecto.fecha_dictamen_coordinador = hoy
            proyecto.save()
            messages.warning(request, f'Protocolo devuelto con observaciones al alumno.')

    return redirect('coordinador_validar_protocolos')


@login_required
def coordinador_ver_expediente(request, id_perfil):
    """Ficha integral del expediente escolar para la Coordinación (CU02, CU03)."""
    perfil_coord = getattr(request.user, 'perfil', None)
    if not perfil_coord or perfil_coord.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'Acceso restringido a la Coordinación.')
        return redirect('index')

    alumno_perfil = get_object_or_404(PerfilUsuario, id_usuario=id_perfil, tipo_usuario='ALUMNO')
    proyecto = ProyectoTesis.objects.filter(alumno=alumno_perfil).first()

    entregables = []
    minutas = []

    if proyecto:
        entregables = EntregableVersion.objects.filter(
            proyecto=proyecto
        ).prefetch_related('mensajes__emisor').order_by('-numero_version')
        
        minutas = MinutaAsesoria.objects.filter(
            proyecto=proyecto
        ).prefetch_related('acuerdos').order_by('-fecha_reunion')

    return render(request, 'seguimiento/coordinador/expediente_alumno.html', {
        'alumno': alumno_perfil,
        'proyecto': proyecto,
        'entregables': entregables,
        'minutas': minutas,
    })


@login_required
def finalizar_proyecto_tesis(request, id_proyecto):
    """Permite al Coordinador dar por terminada la tesis al entregar la constancia."""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'Acceso no autorizado.')
        return redirect('index')

    proyecto = get_object_or_404(ProyectoTesis, id_proyecto=id_proyecto)
    proyecto.estado_proyecto = 'CONCLUIDO'
    proyecto.save()
    
    messages.success(request, f'El proyecto de {proyecto.alumno.primer_nombre} {proyecto.alumno.apellido_paterno} se marcó como CONCLUIDO.')
    return redirect('coordinador_dashboard')


@login_required
def coordinador_alertas(request):
    """CU04: Monitoreo exclusivo de alumnos activos con más de 30 días sin avance."""[cite: 1, 2]
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'Acceso restringido a la Coordinación.')
        return redirect('index')

    alumnos = PerfilUsuario.objects.filter(
        tipo_usuario='ALUMNO'
    ).select_related('user', 'datos_alumno')

    proyectos_map = {
        p.alumno_id: p 
        for p in ProyectoTesis.objects.all()
    }

    hoy = timezone.now().date()
    alumnos_en_rezago = []

    for al in alumnos:
        proyecto = proyectos_map.get(al.id_usuario)
        
        if proyecto and proyecto.estado_proyecto == 'CONCLUIDO':
            continue

        if proyecto and proyecto.fecha_ultimo_avance:
            ultimo_avance = proyecto.fecha_ultimo_avance
            if hasattr(ultimo_avance, 'date'):
                ultimo_avance = ultimo_avance.date()
        else:
            ultimo_avance = al.fecha_registro.date() if hasattr(al, 'fecha_registro') else al.user.date_joined.date()

        dias = (hoy - ultimo_avance).days

        if dias > 30:
            alumnos_en_rezago.append({
                'perfil': al,
                'matricula': al.datos_alumno.matricula if hasattr(al, 'datos_alumno') and al.datos_alumno else 'S/M',
                'proyecto': proyecto,
                'ultimo_avance': ultimo_avance,
                'dias_inactividad': dias,
            })

    alumnos_en_rezago.sort(key=lambda x: x['dias_inactividad'], reverse=True)

    return render(request, 'seguimiento/coordinador/alertas.html', {
        'alumnos_en_rezago': alumnos_en_rezago,
    })


# =============================================================================
# ADMINISTRACIÓN DE USUARIOS, ROLES Y ACCESOS
# =============================================================================

@login_required
def activar_asesor(request, id_perfil):
    """Acción del Coordinador para validar y activar la cuenta de un docente."""
    perfil_coord = getattr(request.user, 'perfil', None)
    if not perfil_coord or perfil_coord.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('index')

    docente = get_object_or_404(PerfilUsuario, id_usuario=id_perfil, tipo_usuario='ASESOR')
    docente.cuenta_activa = True
    docente.estado_registro = 'ACTIVO'
    docente.save()

    messages.success(request, f'La cuenta del profesor {docente.primer_nombre} {docente.apellido_paterno} fue activada exitosamente.')
    return redirect('coordinador_dashboard')


@login_required
def rechazar_asesor(request, id_perfil):
    """Rechaza y elimina una solicitud pendiente de docente."""
    perfil_coord = getattr(request.user, 'perfil', None)
    if not perfil_coord or perfil_coord.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('index')

    solicitud = get_object_or_404(PerfilUsuario, id_usuario=id_perfil, tipo_usuario='ASESOR', cuenta_activa=False)
    nombre = f"{solicitud.primer_nombre} {solicitud.apellido_paterno}"
    solicitud.user.delete()
    messages.warning(request, f"La solicitud de {nombre} fue eliminada.")
    return redirect('coordinador_dashboard')


@login_required
def coordinador_editar_asesor(request, id_perfil):
    """Edita correo, contraseña o datos de un asesor."""
    perfil_coord = getattr(request.user, 'perfil', None)
    if not perfil_coord or perfil_coord.tipo_usuario != 'COORDINADOR':
        return redirect('index')

    docente_perfil = get_object_or_404(PerfilUsuario, id_usuario=id_perfil, tipo_usuario='ASESOR')
    docente_user = docente_perfil.user
    docente_asesor = getattr(docente_perfil, 'datos_asesor', None)

    if request.method == 'POST':
        form = EditarAsesorPorCoordinadorForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            nuevo_email = datos['email'].strip().lower()

            if User.objects.filter(email__iexact=nuevo_email).exclude(pk=docente_user.pk).exists():
                messages.error(request, 'Ese correo ya pertenece a otro usuario registrado.')
                return render(request, 'seguimiento/coordinador/editar_asesor.html', {'form': form, 'docente': docente_perfil})

            docente_user.email = nuevo_email
            if datos.get('nueva_password'):
                docente_user.set_password(datos['nueva_password'])
            docente_user.save()

            docente_perfil.primer_nombre = datos['primer_nombre'].strip()
            docente_perfil.segundo_nombre = datos.get('segundo_nombre', '').strip()
            docente_perfil.apellido_paterno = datos['apellido_paterno'].strip()
            docente_perfil.apellido_materno = datos['apellido_materno'].strip()
            docente_perfil.save()

            if docente_asesor:
                docente_asesor.numero_empleado = datos['numero_empleado'].strip()
                docente_asesor.grado_academico = datos['grado_academico']
                docente_asesor.save()

            messages.success(request, f"Datos de {docente_perfil.primer_nombre} actualizados con éxito.")
            return redirect('coordinador_dashboard')
    else:
        form = EditarAsesorPorCoordinadorForm(initial={
            'email': docente_user.email,
            'primer_nombre': docente_perfil.primer_nombre,
            'segundo_nombre': docente_perfil.segundo_nombre or '',
            'apellido_paterno': docente_perfil.apellido_paterno,
            'apellido_materno': docente_perfil.apellido_materno,
            'numero_empleado': docente_asesor.numero_empleado if docente_asesor else '',
            'grado_academico': docente_asesor.grado_academico if docente_asesor else '',
        })

    return render(request, 'seguimiento/coordinador/editar_asesor.html', {
        'form': form,
        'docente': docente_perfil
    })


@login_required
def coordinador_editar_alumno(request, id_perfil):
    """Edita datos, matrícula o contraseña de un alumno."""
    perfil_coord = getattr(request.user, 'perfil', None)
    if not perfil_coord or perfil_coord.tipo_usuario != 'COORDINADOR':
        return redirect('index')

    alumno_perfil = get_object_or_404(PerfilUsuario, id_usuario=id_perfil, tipo_usuario='ALUMNO')
    alumno_user = alumno_perfil.user
    alumno_datos = getattr(alumno_perfil, 'datos_alumno', None)

    if request.method == 'POST':
        form = EditarAlumnoPorCoordinadorForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            nuevo_email = datos['email'].strip().lower()

            if User.objects.filter(email__iexact=nuevo_email).exclude(pk=alumno_user.pk).exists():
                messages.error(request, 'Ese correo ya pertenece a otro usuario registrado.')
                return render(request, 'seguimiento/coordinador/editar_alumno.html', {'form': form, 'alumno': alumno_perfil})

            alumno_user.email = nuevo_email
            if datos.get('nueva_password'):
                alumno_user.set_password(datos['nueva_password'])
            alumno_user.save()

            alumno_perfil.primer_nombre = datos['primer_nombre'].strip()
            alumno_perfil.segundo_nombre = datos.get('segundo_nombre', '').strip()
            alumno_perfil.apellido_paterno = datos['apellido_paterno'].strip()
            alumno_perfil.apellido_materno = datos['apellido_materno'].strip()
            alumno_perfil.save()

            if alumno_datos:
                alumno_datos.matricula = datos['matricula'].strip()
                alumno_datos.save()

            messages.success(request, f"Datos del alumno {alumno_perfil.primer_nombre} actualizados con éxito.")
            return redirect('coordinador_dashboard')
    else:
        form = EditarAlumnoPorCoordinadorForm(initial={
            'email': alumno_user.email,
            'primer_nombre': alumno_perfil.primer_nombre,
            'segundo_nombre': alumno_perfil.segundo_nombre or '',
            'apellido_paterno': alumno_perfil.apellido_paterno,
            'apellido_materno': alumno_perfil.apellido_materno,
            'matricula': alumno_datos.matricula if alumno_datos else '',
        })

    return render(request, 'seguimiento/coordinador/editar_alumno.html', {
        'form': form,
        'alumno': alumno_perfil
    })


@login_required
def registrar_coordinador(request):
    """Permite registrar un nuevo integrante de coordinación."""
    perfil_admin = getattr(request.user, 'perfil', None)
    if not perfil_admin or perfil_admin.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'Acceso no autorizado.')
        return redirect('index')

    if request.method == 'POST':
        form = RegistroCoordinadorForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            nuevo_user = User.objects.create_user(
                username=datos['username'],
                email=datos['email'],
                password=datos['password'],
                first_name=datos['primer_nombre'],
                last_name=datos['apellido_paterno']
            )

            perfil = PerfilUsuario.objects.create(
                user=nuevo_user,
                primer_nombre=datos['primer_nombre'],
                segundo_nombre=datos['segundo_nombre'],
                apellido_paterno=datos['apellido_paterno'],
                apellido_materno=datos['apellido_materno'],
                tipo_usuario='COORDINADOR',
                cuenta_activa=True
            )

            Coordinador.objects.create(
                perfil=perfil,
                cubiculo_oficina=datos.get('cubiculo_oficina', ''),
                telefono_oficina=datos.get('telefono_oficina', '')
            )
            ConfiguracionUsuario.objects.get_or_create(perfil=perfil)

            messages.success(request, f"Se ha registrado al nuevo Coordinador: {perfil.primer_nombre} {perfil.apellido_paterno}")
            return redirect('coordinador_dashboard')
    else:
        form = RegistroCoordinadorForm()

    return render(request, 'seguimiento/coordinador/registro_coordinador.html', {'form': form})


@login_required
def cambiar_rol_usuario(request, id_perfil):
    """Modifica el rol entre Asesor y Coordinador depurando tablas secundarias."""
    perfil_admin = getattr(request.user, 'perfil', None)
    if not perfil_admin or perfil_admin.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'No tienes permisos de coordinación.')
        return redirect('index')

    perfil_objetivo = get_object_or_404(PerfilUsuario, id_usuario=id_perfil)

    if perfil_objetivo.tipo_usuario == 'ASESOR':
        perfil_objetivo.tipo_usuario = 'COORDINADOR'
        perfil_objetivo.save()

        Coordinador.objects.get_or_create(
            perfil=perfil_objetivo,
            defaults={
                'cubiculo_oficina': 'Edificio FCC 1 - Cubículo 105',
                'telefono_oficina': '2222295500 Ext 7200'
            }
        )
        messages.success(request, f"El docente {perfil_objetivo.primer_nombre} {perfil_objetivo.apellido_paterno} fue promovido a Coordinador.")

    elif perfil_objetivo.tipo_usuario == 'COORDINADOR':
        if perfil_objetivo.user == request.user:
            messages.warning(request, "Por seguridad, no puedes quitarte el rol de coordinador a ti mismo.")
            return redirect('coordinador_dashboard')

        perfil_objetivo.tipo_usuario = 'ASESOR'
        perfil_objetivo.save()
        Coordinador.objects.filter(perfil=perfil_objetivo).delete()

        Asesor.objects.get_or_create(
            perfil=perfil_objetivo,
            defaults={
                'numero_empleado': f"100{perfil_objetivo.id_usuario:04d}",
                'grado_academico': 'Mtro.'
            }
        )
        messages.info(request, f"{perfil_objetivo.primer_nombre} {perfil_objetivo.apellido_paterno} ahora es Asesor y se retiró de la lista de Coordinadores.")

    return redirect('coordinador_dashboard')


# =============================================================================
# ADMINISTRACIÓN DE CONVOCATORIAS OFICIALES
# =============================================================================

@login_required
def coordinador_convocatorias(request):
    """Administra las convocatorias y periodos oficiales."""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'Acceso restringido a la Coordinación.')
        return redirect('index')

    convocatorias = Convocatoria.objects.all()
    hoy = timezone.now().date()

    if request.method == 'POST':
        form = ConvocatoriaForm(request.POST)
        if form.is_valid():
            nueva = form.save(commit=False)
            nueva.creada_por = perfil
            nueva.save()
            messages.success(request, f'La convocatoria "{nueva.titulo}" fue publicada exitosamente.')
            return redirect('coordinador_convocatorias')
    else:
        form = ConvocatoriaForm()

    return render(request, 'seguimiento/coordinador/convocatorias.html', {
        'convocatorias': convocatorias,
        'form': form,
        'hoy': hoy
    })


@login_required
def cambiar_estado_convocatoria(request, id_convocatoria, nuevo_estado):
    """Cambia el estado de una convocatoria (ABIERTA, CERRADA, PROXIMA)."""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'COORDINADOR':
        messages.error(request, 'Acceso no autorizado.')
        return redirect('index')

    conv = get_object_or_404(Convocatoria, id_convocatoria=id_convocatoria)
    if nuevo_estado in ['ABIERTA', 'CERRADA', 'PROXIMA']:
        conv.estado = nuevo_estado
        conv.save()
        messages.info(request, f'El estado de "{conv.titulo}" se cambió a {conv.get_estado_display()}.')

    return redirect('coordinador_convocatorias')