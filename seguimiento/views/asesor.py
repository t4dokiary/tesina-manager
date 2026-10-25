from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from seguimiento.models import (
    MaterialApoyoMinuta,
    PerfilUsuario,
    Asesor,
    ConfiguracionUsuario,
    TelefonoUsuario,
    ProyectoTesis,
    MinutaAsesoria,
    CompromisoAcuerdo,
    EntregableVersion,
)
from seguimiento.forms import RegistroAsesorForm
from .generales import redirigir_por_rol


def registrar_asesor(request):
    """Registro público para directores de tesis con validación obligatoria."""
    if request.user.is_authenticated:
        return redirigir_por_rol(request.user)

    if request.method == 'POST':
        form = RegistroAsesorForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            try:
                with transaction.atomic():
                    # 1. Crear usuario base de Django
                    user = User.objects.create_user(
                        username=datos['username'],
                        email=datos['email'],
                        password=datos['password'],
                        first_name=datos['primer_nombre'],
                        last_name=datos['apellido_paterno']
                    )

                    # 2. Perfil con cuenta inactiva por seguridad
                    perfil = PerfilUsuario.objects.create(
                        user=user,
                        primer_nombre=datos['primer_nombre'],
                        segundo_nombre=datos.get('segundo_nombre', ''),
                        apellido_paterno=datos['apellido_paterno'],
                        apellido_materno=datos['apellido_materno'],
                        tipo_usuario='ASESOR',
                        cuenta_activa=False,          # Inactivo hasta que lo apruebe Coordinación
                        estado_registro='PENDIENTE'
                    )

                    # 3. Crear registro específico del Asesor
                    Asesor.objects.create(
                        perfil=perfil,
                        numero_empleado=datos['numero_empleado'],
                        grado_academico=datos['grado_academico']
                    )

                    if datos.get('telefono'):
                        TelefonoUsuario.objects.create(perfil=perfil, numero_telefono=datos['telefono'])

                messages.success(
                    request,
                    "Tu solicitud ha sido enviada. La Coordinación de Posgrado validará tu cuenta antes de que puedas iniciar sesión."
                )
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Error al procesar el registro: {e}")
        else:
            messages.error(request, "Por favor corrige los errores señalados en el formulario.")
    else:
        form = RegistroAsesorForm()

    return render(request, 'seguimiento/registro_asesor.html', {'form': form})


@login_required
def asesor_dashboard(request):
    """Panel principal del asesor: tesistas a cargo, semáforo de inactividad y métricas."""
    perfil = request.user.perfil
    if perfil.tipo_usuario != 'ASESOR':
        messages.error(request, "Acceso no autorizado.")
        return redirect('index')

    # Se agregan prefetch_related para cargar minutas, acuerdos y borradores de cada alumno
    proyectos = ProyectoTesis.objects.filter(
        asesor=perfil
    ).select_related('alumno', 'alumno__datos_alumno').prefetch_related(
        'minutas__acuerdos',
        'minutas__materiales',
        'entregables'
    )

    # Métricas de entregas pendientes de revisión
    entregas_pendientes = EntregableVersion.objects.filter(
        proyecto__in=proyectos,
        retroalimentacion_asesor__isnull=True
    ).count()

    # Cálculo dinámico del semáforo de inactividad (> 30 días) (CU04)
    hoy = timezone.now().date()
    alumnos_rezago = 0
    for p in proyectos:
        # Se obtiene el cálculo de días sin reescribir la propiedad del modelo
        if hasattr(p, 'dias_inactividad'):
            dias = p.dias_inactividad  # Utiliza la propiedad ya calculada por el modelo
        elif p.fecha_ultimo_avance:
            dias = (hoy - p.fecha_ultimo_avance).days
        else:
            dias = 0

        # Conteo de alumnos en rezago preventivo
        if dias >= 30:
            alumnos_rezago += 1

    context = {
        'proyectos': proyectos,
        'entregas_pendientes': entregas_pendientes,
        'alumnos_rezago': alumnos_rezago,
        'hoy': hoy,  # Requerido para comparar fechas de vencimiento en las tareas del modal
    }
    return render(request, 'seguimiento/asesor/dashboard.html', context)

@login_required
def alternar_cumplimiento_acuerdo(request, id_acuerdo):
    """
    Permite al Asesor marcar un acuerdo como Cumplido o Pendiente.
    """
    perfil = request.user.perfil
    if perfil.tipo_usuario != 'ASESOR':
        messages.error(request, "Acceso exclusivo para Asesores Docentes.")
        return redirect('index')

    acuerdo = get_object_or_404(CompromisoAcuerdo, id_acuerdo=id_acuerdo, minuta__proyecto__asesor=perfil)
    
    # Alternar el estado booleano
    if hasattr(acuerdo, 'estado_cumplido'):
        acuerdo.estado_cumplido = not acuerdo.estado_cumplido
        estado_nuevo = "cumplida" if acuerdo.estado_cumplido else "marcada como pendiente"
    elif hasattr(acuerdo, 'estado'):
        acuerdo.estado = 'CUMPLIDO' if acuerdo.estado != 'CUMPLIDO' else 'PENDIENTE'
        estado_nuevo = "cumplida" if acuerdo.estado == 'CUMPLIDO' else "marcada como pendiente"
    
    acuerdo.save()
    messages.success(request, f"La tarea '{acuerdo.descripcion_tarea}' fue {estado_nuevo}.")

    # Retornar a la página de donde vino (la vista del proyecto o el dashboard)
    return redirect(request.META.get('HTTP_REFERER', 'asesor_dashboard'))

from seguimiento.models import MensajeEntrega # Asegúrate de importarlo

@login_required
def asesor_revision(request, proyecto_id):
    """Bandeja de versiones, retroalimentación tipo chat y subida de PDF corregido (CU02)."""
    perfil = request.user.perfil
    if perfil.tipo_usuario != 'ASESOR':
        messages.error(request, "Acceso no autorizado.")
        return redirect('index')

    proyecto = get_object_or_404(ProyectoTesis, id_proyecto=proyecto_id, asesor=perfil)

    if request.method == 'POST':
        entregable_id = request.POST.get('entregable_id')
        retroalimentacion = request.POST.get('retroalimentacion', '').strip()
        pdf_correccion = request.FILES.get('archivo_correccion')

        entregable = get_object_or_404(EntregableVersion, id_entregable=entregable_id, proyecto=proyecto)

        # Si adjunta un PDF corregido
        if pdf_correccion:
            if not pdf_correccion.name.lower().endswith('.pdf'):
                messages.error(request, "El archivo de corrección debe ser en formato PDF.")
                return redirect('asesor_revision', proyecto_id=proyecto.id_proyecto)
            entregable.archivo_correccion_asesor = pdf_correccion

        # Si envía un mensaje al hilo/chat
        if retroalimentacion:
            MensajeEntrega.objects.create(
                entregable=entregable,
                emisor=perfil,
                mensaje=retroalimentacion
            )
            entregable.retroalimentacion_asesor = retroalimentacion

        entregable.save()

        # Al retroalimentar se actualiza la fecha de último avance
        proyecto.fecha_ultimo_avance = timezone.now().date()
        proyecto.save(update_fields=['fecha_ultimo_avance'])

        messages.success(request, f"Observaciones registradas para la versión v{entregable.numero_version}.")
        return redirect('asesor_revision', proyecto_id=proyecto.id_proyecto)

    entregables = EntregableVersion.objects.filter(proyecto=proyecto).prefetch_related('mensajes__emisor').order_by('-numero_version')

    context = {
        'proyecto': proyecto,
        'entregables': entregables,
    }
    return render(request, 'seguimiento/asesor/revision_borradores.html', context)

@login_required
def asesor_minuta(request, proyecto_id):
    """
    CU03: Registro flexible según necesidad del Asesor:
    1. Minuta y Tarea conjunta.
    2. Solo Sesión/Cita de reunión.
    3. Solo Tarea/Compromiso calendarizado.
    """
    perfil = request.user.perfil
    if perfil.tipo_usuario != 'ASESOR':
        messages.error(request, "Acceso restringido a asesores.")
        return redirect('index')

    proyecto = get_object_or_404(ProyectoTesis, id_proyecto=proyecto_id, asesor=perfil)
    versiones = EntregableVersion.objects.filter(proyecto=proyecto).order_by('-numero_version')
    ultima_version = versiones.first()

    cubiculo_defecto = ""
    if hasattr(perfil, 'datos_asesor') and hasattr(perfil.datos_asesor, 'cubiculo'):
        cubiculo_defecto = perfil.datos_asesor.cubiculo

    if request.method == 'POST':
        tipo_registro = request.POST.get('tipo_registro', 'COMPLETO') # 'COMPLETO', 'SOLO_REUNION', 'SOLO_TAREA'

        fecha = request.POST.get('fecha_reunion')
        hora = request.POST.get('hora_reunion') or None
        modalidad = request.POST.get('modalidad', 'PRESENCIAL')
        lugar = request.POST.get('lugar_reunion', '').strip()
        version_id = request.POST.get('version_revisada') or None
        resumen = request.POST.get('resumen_temas', '').strip()

        tarea = request.POST.get('descripcion_tarea', '').strip()
        responsable = request.POST.get('responsable', 'ALUMNO')
        fecha_limite = request.POST.get('fecha_limite')

        version_obj = EntregableVersion.objects.filter(id_entregable=version_id).first() if version_id else None

        # CASO 1 Y 2: Incluye Reunión / Minuta
        minuta = None
        if tipo_registro in ['COMPLETO', 'SOLO_REUNION']:
            if not fecha or not resumen:
                messages.error(request, 'La fecha y el resumen de temas son obligatorios para formalizar la minuta.')
                return redirect('asesor_minuta', proyecto_id=proyecto.id_proyecto)

            minuta = MinutaAsesoria.objects.create(
                proyecto=proyecto,
                version_revisada=version_obj,
                fecha_reunion=fecha,
                hora_reunion=hora,
                modalidad=modalidad,
                lugar_reunion=lugar or ("Cubículo Asesor" if modalidad == 'PRESENCIAL' else "Enlace Virtual"),
                resumen_temas=resumen,
                firmada_asesor=True
            )

            # Subida de PDFs de apoyo asignados a esta minuta
            archivos_apoyo = request.FILES.getlist('archivos_apoyo')
            titulos_apoyo = request.POST.getlist('titulos_apoyo')
            for idx, pdf in enumerate(archivos_apoyo):
                if pdf.name.lower().endswith('.pdf'):
                    nombre = titulos_apoyo[idx].strip() if idx < len(titulos_apoyo) and titulos_apoyo[idx].strip() else pdf.name
                    MaterialApoyoMinuta.objects.create(minuta=minuta, titulo=nombre, archivo_pdf=pdf)

        # CASO 3: Solo Tarea (si no hay minuta creada, creamos una de asignación administrativa)
        if tipo_registro in ['COMPLETO', 'SOLO_TAREA'] and tarea and fecha_limite:
            if not minuta:
                minuta = MinutaAsesoria.objects.create(
                    proyecto=proyecto,
                    version_revisada=version_obj,
                    fecha_reunion=timezone.now().date(),
                    modalidad='PRESENCIAL',
                    lugar_reunion="Asignación directa de tareas",
                    resumen_temas=f"Asignación de compromiso: {tarea}",
                    firmada_asesor=True,
                    firmada_alumno=True # No requiere firma de visita física si fue solo tarea asignada
                )

            CompromisoAcuerdo.objects.create(
                minuta=minuta,
                numero_acuerdo=minuta.acuerdos.count() + 1,
                descripcion_tarea=tarea,
                responsable=responsable,
                fecha_limite=fecha_limite,
                estado='PENDIENTE',
                estado_cumplido=False
            )

        # Reiniciar contador de inactividad
        proyecto.fecha_ultimo_avance = timezone.now().date()
        proyecto.save(update_fields=['fecha_ultimo_avance'])

        messages.success(request, 'Registro procesado y notificado exitosamente al alumno.')
        return redirect('asesor_dashboard')

    return render(request, 'seguimiento/asesor/crear_minuta.html', {
        'proyecto': proyecto,
        'versiones': versiones,
        'ultima_version': ultima_version,
        'cubiculo_defecto': cubiculo_defecto,
        'hoy': timezone.now().date(),
    })

@login_required
def reprogramar_minuta(request, id_minuta):
    """Permite al asesor cambiar la fecha o lugar/enlace de la asesoría pactada."""
    perfil = request.user.perfil
    if perfil.tipo_usuario != 'ASESOR':
        messages.error(request, "Acceso no autorizado.")
        return redirect('index')

    minuta = get_object_or_404(MinutaAsesoria, id_minuta=id_minuta, proyecto__asesor=perfil)

    if request.method == 'POST':
        nueva_fecha = request.POST.get('nueva_fecha')
        nueva_hora = request.POST.get('nueva_hora') or None
        nuevo_lugar = request.POST.get('nuevo_lugar', '').strip()

        if nueva_fecha:
            minuta.fecha_reunion = nueva_fecha
            minuta.hora_reunion = nueva_hora
            if nuevo_lugar:
                minuta.lugar_reunion = nuevo_lugar
            # Se reinicia la firma del alumno ya que cambió la fecha
            minuta.firmada_alumno = False
            minuta.fecha_firma_alumno = None
            minuta.save()
            messages.success(request, "Cita de asesoría reprogramada con éxito.")

    return redirect(request.META.get('HTTP_REFERER', 'asesor_dashboard'))