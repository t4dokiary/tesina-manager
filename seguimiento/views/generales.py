import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from seguimiento.models import ConfiguracionUsuario, Convocatoria, TelefonoUsuario
from seguimiento.forms import LoginForm, MiPerfilForm


def calcular_tiempo_restante(convocatoria):
    """Calcula el tiempo restante hasta las 23:59:59 del día límite."""
    if not convocatoria:
        return {'periodo_vencido': True, 'unidad': None, 'valor': 0}

    ahora = timezone.now()
    limite_exacto = timezone.make_aware(
        datetime.datetime.combine(
            convocatoria.fecha_limite_protocolo,
            datetime.time(23, 59, 59)
        )
    )
    diferencia = limite_exacto - ahora

    if diferencia.total_seconds() <= 0:
        return {'periodo_vencido': True, 'unidad': None, 'valor': 0}

    segundos = int(diferencia.total_seconds())
    dias = segundos // 86400
    horas = (segundos % 86400) // 3600
    minutos = (segundos % 3600) // 60

    if dias > 0:
        return {'periodo_vencido': False, 'unidad': 'DIAS', 'valor': dias}
    elif horas > 0:
        return {'periodo_vencido': False, 'unidad': 'HORAS', 'valor': horas}
    else:
        return {'periodo_vencido': False, 'unidad': 'MINUTOS', 'valor': max(1, minutos)}


def index(request):
    """
    Portada del sistema:
    Muestra la convocatoria SOLO si su estado es 'ABIERTA', está activa y dentro de fechas.
    Si está CERRADA, se pasa como None para ocultar cualquier banner.
    """
    ahora = timezone.now()
    hoy = ahora.date()

    # Buscamos la convocatoria que esté ABIERTA
    convocatoria_abierta = Convocatoria.objects.filter(estado='ABIERTA').first()

    dias_restantes = None
    horas_restantes = None
    es_ultimo_dia = False
    mostrar_banner = False

    if convocatoria_abierta:
        # Límite al final del día establecido
        limite_exacto = timezone.make_aware(
            datetime.datetime.combine(
                convocatoria_abierta.fecha_limite_protocolo,
                datetime.time(23, 59, 59)
            )
        )
        diferencia = limite_exacto - ahora

        # Si ya pasó la fecha límite, la consideramos expirada y NO se muestra
        if diferencia.total_seconds() > 0:
            mostrar_banner = True
            segundos_totales = int(diferencia.total_seconds())
            dias = segundos_totales // 86400
            horas = (segundos_totales % 86400) // 3600

            if dias == 0:
                es_ultimo_dia = True
                horas_restantes = max(1, horas)
            else:
                dias_restantes = dias
        else:
            # Si ya expiró el tiempo, se oculta
            convocatoria_abierta = None
            mostrar_banner = False

    return render(request, 'seguimiento/index.html', {
        'convocatoria': convocatoria_abierta if mostrar_banner else None,
        'dias_restantes': dias_restantes,
        'horas_restantes': horas_restantes,
        'es_ultimo_dia': es_ultimo_dia,
        'mostrar_banner': mostrar_banner,
    })


def iniciar_sesion(request):
    """CU01: Iniciar sesión y redirección por rol."""
    if request.user.is_authenticated:
        return redirigir_por_rol(request.user)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            identificador = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=identificador, password=password)
            if not user:
                try:
                    usuario_obj = User.objects.get(email=identificador)
                    user = authenticate(request, username=usuario_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if user is not None:
                perfil = getattr(user, 'perfil', None)
                if perfil and not perfil.cuenta_activa:
                    messages.error(request, 'Tu cuenta está inactiva o pendiente de validación por la coordinación.')
                    return render(request, 'seguimiento/login.html', {'form': form})

                login(request, user)
                return redirigir_por_rol(user)
            else:
                messages.error(request, 'Usuario/correo o contraseña incorrectos.')
    else:
        form = LoginForm()

    return render(request, 'seguimiento/login.html', {'form': form})


def cerrar_sesion(request):
    """Cierra la sesión y vuelve a la portada."""
    logout(request)
    return redirect('index')


def redirigir_por_rol(user):
    """Redirige automáticamente según el tipo de usuario."""
    perfil = getattr(user, 'perfil', None)
    if not perfil:
        return redirect('/admin/')

    if perfil.tipo_usuario == 'ALUMNO':
        return redirect('alumno_dashboard')
    elif perfil.tipo_usuario == 'ASESOR':
        return redirect('asesor_dashboard')
    elif perfil.tipo_usuario == 'COORDINADOR':
        return redirect('coordinador_dashboard')
    return redirect('index')

@login_required
def editar_mi_perfil(request):
    """Configuración personal, tema y credenciales con validación doble."""
    perfil = getattr(request.user, 'perfil', None)
    usuario = request.user
    config, _ = ConfiguracionUsuario.objects.get_or_create(perfil=perfil)
    telefono_obj = perfil.telefonos.first() if perfil else None

    if request.method == 'POST':
        form = MiPerfilForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data

            # 1. Cambiar contraseña si se especificó
            if datos.get('nueva_password'):
                usuario.set_password(datos['nueva_password'])
                update_session_auth_hash(request, usuario)  # Evita que se cierre la sesión
            
            usuario.email = datos['email']
            usuario.save()

            # 2. Datos personales
            if perfil:
                perfil.primer_nombre = datos['primer_nombre']
                perfil.segundo_nombre = datos['segundo_nombre']
                perfil.apellido_paterno = datos['apellido_paterno']
                perfil.apellido_materno = datos['apellido_materno']
                perfil.save()

                if datos.get('telefono'):
                    if telefono_obj:
                        telefono_obj.numero_telefono = datos['telefono']
                        telefono_obj.save()
                    else:
                        TelefonoUsuario.objects.create(perfil=perfil, numero_telefono=datos['telefono'])

            # 3. Guardar Tema
            config.tema = datos['tema']
            config.save()

            messages.success(request, 'Configuración y perfil actualizados correctamente.')
            return redirect('mi_perfil')
    else:
        form = MiPerfilForm(initial={
            'primer_nombre': perfil.primer_nombre if perfil else usuario.first_name,
            'segundo_nombre': perfil.segundo_nombre if perfil else '',
            'apellido_paterno': perfil.apellido_paterno if perfil else usuario.last_name,
            'apellido_materno': perfil.apellido_materno if perfil else '',
            'email': usuario.email,
            'telefono': telefono_obj.numero_telefono if telefono_obj else '',
            'tema': config.tema,
        })

    return render(request, 'seguimiento/mi_perfil.html', {'form': form, 'perfil': perfil})