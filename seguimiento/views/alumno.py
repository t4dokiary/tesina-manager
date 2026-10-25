from datetime import date
from multiprocessing import Value
from django.db.models import Q, Case, When
from django.db.models.fields import IntegerField
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse

from seguimiento.models import (
    PerfilUsuario,
    Alumno,
    ConfiguracionUsuario,
    TelefonoUsuario,
    Convocatoria,
    ProyectoTesis,
    EntregableVersion,
    MinutaAsesoria,
    CompromisoAcuerdo,
)
from seguimiento.forms import RegistroAlumnoForm
from .generales import redirigir_por_rol


def registrar_alumno(request):
    """
    Registro público de tesistas de posgrado (CU01).
    Crea en una sola transacción atómica el usuario, perfil, matrícula y teléfono.
    """
    if request.user.is_authenticated:
        return redirigir_por_rol(request.user)

    if request.method == 'POST':
        form = RegistroAlumnoForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            try:
                with transaction.atomic():
                    # 1. Usuario base de autenticación de Django
                    user = User.objects.create_user(
                        username=datos['username'],
                        email=datos['email'],
                        password=datos['password'],
                        first_name=datos['primer_nombre'],
                        last_name=datos['apellido_paterno']
                    )

                    # 2. Perfil con rol ALUMNO y activo por defecto
                    perfil = PerfilUsuario.objects.create(
                        user=user,
                        primer_nombre=datos['primer_nombre'],
                        segundo_nombre=datos.get('segundo_nombre', ''),
                        apellido_paterno=datos['apellido_paterno'],
                        apellido_materno=datos['apellido_materno'],
                        tipo_usuario='ALUMNO',
                        estado_registro='ACTIVO',
                        cuenta_activa=True
                    )

                    # 3. Expediente escolar con matrícula única
                    Alumno.objects.create(
                        perfil=perfil,
                        matricula=datos['matricula']
                    )

                    # 4. Ajustes visuales y teléfono opcional
                    ConfiguracionUsuario.objects.get_or_create(perfil=perfil, defaults={'tema': 'SYSTEM'})
                    if datos.get('telefono'):
                        TelefonoUsuario.objects.create(
                            perfil=perfil,
                            numero_telefono=datos['telefono']
                        )

                messages.success(request, '¡Registro exitoso! Ya puedes iniciar sesión con tus credenciales.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Ocurrió un error al procesar tu registro: {e}')
    else:
        form = RegistroAlumnoForm()

    return render(request, 'seguimiento/registro_alumno.html', {'form': form})


@login_required
def alumno_dashboard(request):
    """
    Panel principal: Ficha del Protocolo y Sección de Tareas Pendientes.
    Solo muestra tareas pendientes (excluye las cumplidas).
    """
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'ALUMNO':
        messages.error(request, 'Acceso restringido a estudiantes.')
        return redirect('index')

    proyecto = ProyectoTesis.objects.filter(alumno=perfil).select_related('asesor', 'convocatoria').first()
    hoy = timezone.now().date()
    convocatoria = Convocatoria.objects.filter(estado='ABIERTA').first()
    convocatoria_vigente = convocatoria and (convocatoria.fecha_limite_protocolo >= hoy)

    asesores_activos = PerfilUsuario.objects.filter(
        tipo_usuario='ASESOR',
        cuenta_activa=True
    ).exclude(estado_registro='PENDIENTE').select_related('datos_asesor')

    puede_editar_protocolo = False
    mensaje_convocatoria = None

    if not proyecto:
        if convocatoria_vigente:
            puede_editar_protocolo = True
        else:
            mensaje_convocatoria = "No hay convocatoria abierta para subir protocolos."
    elif proyecto.estado_proyecto in ['PENDIENTE', 'PROPUESTA', 'RECHAZADO', 'OBSERVACIONES']:
        if convocatoria_vigente:
            puede_editar_protocolo = True
        else:
            mensaje_convocatoria = "El periodo de convocatoria ha vencido. Contacta a Coordinación."
    else:
        puede_editar_protocolo = False

    # FILTRO: Solo compromisos que NO estén cumplidos
    tareas_pendientes = []
    if proyecto:
        pendientes_qs = CompromisoAcuerdo.objects.filter(
            minuta__proyecto=proyecto,
            responsable='ALUMNO'
        ).exclude(
            Q(estado='CUMPLIDO') | Q(estado_cumplido=True)
        )
        # Ordenar en Python: primero las vencidas (fecha_limite < hoy), luego las próximas
        tareas_pendientes = sorted(
            list(pendientes_qs),
            key=lambda t: (0 if t.fecha_limite < hoy else 1, t.fecha_limite)
        )

    context = {
        'perfil': perfil,
        'proyecto': proyecto,
        'convocatoria': convocatoria,
        'puede_editar_protocolo': puede_editar_protocolo,
        'mensaje_convocatoria': mensaje_convocatoria,
        'asesores_activos': asesores_activos,
        'tareas_pendientes': tareas_pendientes,
        'hoy': hoy,
    }
    return render(request, 'seguimiento/alumno/dashboard.html', context)

@login_required
def alumno_subir_protocolo(request):
    """Permite al alumno registrar o actualizar su protocolo antes del dictamen formal."""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'ALUMNO':
        messages.error(request, 'Acceso restringido a estudiantes.')
        return redirect('index')

    hoy = timezone.now().date()
    convocatoria = Convocatoria.objects.filter(estado='ABIERTA').first()

    if not convocatoria or hoy > convocatoria.fecha_limite_protocolo:
        messages.error(request, 'La fecha límite de la convocatoria ha expirado o no hay convocatoria activa.')
        return redirect('alumno_dashboard')

    if request.method == 'POST':
        titulo = request.POST.get('titulo_tesis', '').strip()
        linea = request.POST.get('linea_investigacion', '').strip()
        asesor_id = request.POST.get('asesor_id')
        archivo_pdf = request.FILES.get('archivo_protocolo')

        proyecto = ProyectoTesis.objects.filter(alumno=perfil).first()

        # Si ya fue aprobado, se bloquea la alteración del documento inicial
        if proyecto and proyecto.estado_proyecto in ['APROBADO', 'EN_DESARROLLO', 'CONCLUIDO']:
            messages.error(request, 'El protocolo ya fue aprobado formalmente y no puede ser alterado.')
            return redirect('alumno_dashboard')

        if not proyecto and not archivo_pdf:
            messages.error(request, 'Debes adjuntar el documento de protocolo en formato PDF.')
            return redirect('alumno_dashboard')

        if archivo_pdf and not archivo_pdf.name.lower().endswith('.pdf'):
            messages.error(request, 'El documento debe ser exclusivamente formato PDF.')
            return redirect('alumno_dashboard')

        asesor_obj = get_object_or_404(PerfilUsuario, id_usuario=asesor_id, tipo_usuario='ASESOR') if asesor_id else None

        if proyecto:
            proyecto.titulo_tesis = titulo
            proyecto.linea_investigacion = linea
            if asesor_obj:
                proyecto.asesor = asesor_obj
            if archivo_pdf:
                proyecto.archivo_protocolo = archivo_pdf
            proyecto.convocatoria = convocatoria
            proyecto.estado_proyecto = 'PENDIENTE'
            proyecto.save()
            messages.success(request, 'Tu propuesta de protocolo fue actualizada exitosamente y enviada a revisión.')
        else:
            ProyectoTesis.objects.create(
                alumno=perfil,
                asesor=asesor_obj,
                convocatoria=convocatoria,
                titulo_tesis=titulo,
                linea_investigacion=linea,
                archivo_protocolo=archivo_pdf,
                estado_proyecto='PENDIENTE',
                fecha_ultimo_avance=hoy
            )
            messages.success(request, 'Protocolo entregado con éxito. En espera de visto bueno de la Coordinación.')

    return redirect('alumno_dashboard')


from seguimiento.models import MensajeEntrega # Asegúrate de importarlo

@login_required
def alumno_entregas(request):
    """
    CU02: Repositorio e historial inmutable de borradores de tesis en PDF.
    Solo se permite si el proyecto está APROBADO o EN_DESARROLLO.
    """
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'ALUMNO':
        messages.error(request, 'Acceso restringido a estudiantes.')
        return redirect('index')

    proyecto = ProyectoTesis.objects.filter(alumno=perfil).first()

    if not proyecto or proyecto.estado_proyecto not in ['APROBADO', 'EN_DESARROLLO', 'CONCLUIDO']:
        messages.warning(
            request, 
            'Para subir versiones de borrador, tu protocolo de investigación debe estar aprobado formalmente.'
        )
        return redirect('alumno_dashboard')

    if request.method == 'POST':
        archivo_pdf = request.FILES.get('ruta_archivo_pdf') or request.FILES.get('archivo_pdf')
        comentario = request.POST.get('comentario_alumno', '').strip()

        if not archivo_pdf:
            messages.error(request, 'Debes adjuntar un archivo en formato PDF.')
            return redirect('alumno_entregas')

        if not archivo_pdf.name.lower().endswith('.pdf'):
            messages.error(request, 'Regla CU02: Únicamente se admiten documentos en formato PDF.')
            return redirect('alumno_entregas')

        # Consecutivo inmutable (v1, v2...)
        ultimo = EntregableVersion.objects.filter(proyecto=proyecto).order_by('-numero_version').first()
        nueva_version = (ultimo.numero_version + 1) if ultimo else 1

        entregable = EntregableVersion.objects.create(
            proyecto=proyecto,
            numero_version=nueva_version,
            ruta_archivo_pdf=archivo_pdf,
            comentario_alumno=comentario
        )

        # Crear primer mensaje en el hilo si hubo comentario
        if comentario:
            MensajeEntrega.objects.create(
                entregable=entregable,
                emisor=perfil,
                mensaje=comentario
            )

        proyecto.fecha_ultimo_avance = timezone.now().date()
        proyecto.save(update_fields=['fecha_ultimo_avance'])

        messages.success(request, f'¡Versión {nueva_version} entregada con éxito! Tu Asesor ha sido notificado.')
        return redirect('alumno_entregas')

    # Historial de entregables con sus mensajes de discusión
    entregas = EntregableVersion.objects.filter(proyecto=proyecto).prefetch_related('mensajes__emisor').order_by('-numero_version')

    return render(request, 'seguimiento/alumno/entregas.html', {
        'proyecto': proyecto,
        'entregas': entregas,
    })


@login_required
def enviar_mensaje_entrega(request, id_entregable):
    """Envía un mensaje al hilo de discusión/chat de una versión de borrador (vía AJAX o POST)."""
    perfil = getattr(request.user, 'perfil', None)
    entregable = get_object_or_404(EntregableVersion, id_entregable=id_entregable)

    # Validar que quien responda sea el alumno o el asesor del proyecto
    if perfil != entregable.proyecto.alumno and perfil != entregable.proyecto.asesor:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/x-www-form-urlencoded':
            return JsonResponse({'status': 'error', 'message': 'No tienes permiso para interactuar.'}, status=403)
        messages.error(request, 'No tienes permiso para interactuar en esta entrega.')
        return redirect('index')

    if request.method == 'POST':
        texto = request.POST.get('mensaje', '').strip()
        if texto:
            nuevo_msg = MensajeEntrega.objects.create(
                entregable=entregable,
                emisor=perfil,
                mensaje=texto
            )
            # Actualizar último avance para el semáforo de inactividad
            if perfil.tipo_usuario == 'ALUMNO':
                entregable.proyecto.fecha_ultimo_avance = timezone.now().date()
                entregable.proyecto.save(update_fields=['fecha_ultimo_avance'])

            # Si es petición AJAX, devolver JSON para no recargar la página
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'ok',
                    'mensaje': nuevo_msg.mensaje,
                    'emisor_nombre': f"{perfil.primer_nombre} ({perfil.tipo_usuario.title()})",
                    'tipo_usuario': perfil.tipo_usuario,
                    'fecha_hora': nuevo_msg.fecha_hora.strftime("%d/%m/%Y %H:%M")
                })

    return redirect(request.META.get('HTTP_REFERER', 'alumno_dashboard'))


@login_required
def alumno_acuerdos(request):
    """
    CU03: Consulta ejecutiva de minutas y acuerdos/tareas.
    Jerarquía de acuerdos:
    1) Tareas pendientes VENCIDAS (prioridad máxima arriba)
    2) Tareas pendientes en plazo
    3) Tareas CUMPLIDAS (al final)
    """
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.tipo_usuario != 'ALUMNO':
        messages.error(request, 'Acceso restringido a estudiantes.')
        return redirect('index')

    proyecto = ProyectoTesis.objects.filter(alumno=perfil).first()

    if not proyecto or proyecto.estado_proyecto not in ['APROBADO', 'EN_DESARROLLO', 'CONCLUIDO']:
        messages.warning(
            request, 
            'Para consultar tus acuerdos, tu protocolo de investigación debe estar aprobado formalmente.'
        )
        return redirect('alumno_dashboard')

    hoy = timezone.now().date()

    # Minutas ordenadas de la más reciente a la más antigua
    minutas = MinutaAsesoria.objects.filter(
        proyecto=proyecto
    ).select_related('version_revisada').prefetch_related('acuerdos', 'materiales').order_by('-fecha_reunion')

    # Obtenemos todos los acuerdos asociados a este proyecto
    acuerdos_list = list(
        CompromisoAcuerdo.objects.filter(
            minuta__proyecto=proyecto
        ).select_related('minuta', 'minuta__version_revisada')
    )

    # Función de ordenamiento seguro en Python (sin colisiones con librerías del sistema)
    def prioridad_acuerdo(ac):
        es_cumplida = (ac.estado == 'CUMPLIDO' or ac.estado_cumplido)
        if es_cumplida:
            return (2, ac.fecha_limite)
        if ac.fecha_limite < hoy:
            return (0, ac.fecha_limite)  # Prioridad 0: Vencida arriba
        return (1, ac.fecha_limite)      # Prioridad 1: Pendiente en fecha

    todos_los_acuerdos = sorted(acuerdos_list, key=prioridad_acuerdo)

    # Versiones entregadas para conectar los modales de chat
    entregas = EntregableVersion.objects.filter(
        proyecto=proyecto
    ).prefetch_related('mensajes__emisor').order_by('-numero_version')

    # Métricas
    total_tareas = len(todos_los_acuerdos)
    tareas_cumplidas = sum(1 for ac in todos_los_acuerdos if ac.estado == 'CUMPLIDO' or ac.estado_cumplido)
    tareas_pendientes_count = total_tareas - tareas_cumplidas
    porcentaje_cumplimiento = int((tareas_cumplidas / total_tareas * 100)) if total_tareas > 0 else 100

    context = {
        'proyecto': proyecto,
        'minutas': minutas,
        'todos_los_acuerdos': todos_los_acuerdos,
        'entregas': entregas,
        'total_tareas': total_tareas,
        'tareas_cumplidas': tareas_cumplidas,
        'tareas_pendientes': tareas_pendientes_count,
        'porcentaje_cumplimiento': porcentaje_cumplimiento,
        'hoy': hoy,
    }
    return render(request, 'seguimiento/alumno/acuerdos.html', context)

@login_required
def firmar_minuta_alumno(request, id_minuta):
    """El alumno firma electrónicamente que asistió a la asesoría presencial o virtual."""
    perfil = getattr(request.user, 'perfil', None)
    minuta = get_object_or_404(MinutaAsesoria, id_minuta=id_minuta, proyecto__alumno=perfil)

    if request.method == 'POST':
        if not minuta.firmada_alumno:
            minuta.firmada_alumno = True
            minuta.fecha_firma_alumno = timezone.now()
            minuta.save()
            messages.success(request, f"Has firmado de conformidad la minuta de la reunión del {minuta.fecha_reunion.strftime('%d/%m/%Y')}.")

    return redirect('alumno_acuerdos')