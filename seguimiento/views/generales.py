import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from seguimiento.models import ConfiguracionUsuario, Convocatoria, TelefonoUsuario
from seguimiento.forms import LoginForm, MiPerfilForm


# =============================================================================
# UTILIDADES GENERALES DE TIEMPO
# =============================================================================

def calcular_tiempo_restante(convocatoria):
    """
    Calcula el tiempo restante hasta las 23:59:59 del día límite oficial:
    - Si dias > 0: unidad 'DIAS'
    - Si dias == 0 y horas > 0: unidad 'HORAS'
    - Si dias == 0 y horas == 0: unidad 'MINUTOS' (mínimo 1)
    """
    if not convocatoria or not convocatoria.fecha_limite_protocolo:
        return {'periodo_vencido': True, 'unidad': None, 'valor': 0}

    ahora = timezone.now()
    limite_exacto = timezone.make_aware(
        datetime.datetime.combine(
            convocatoria.fecha_limite_protocolo,
            datetime.time(23, 59, 59)
        ),
        timezone.get_current_timezone()
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


# =============================================================================
# PORTADA / LANDING DEL SISTEMA
# =============================================================================

def index(request):
    """
    Portada del sistema:
    Muestra la convocatoria SOLO si su estado es 'ABIERTA', está activa y dentro de fechas.
    Reutiliza el cálculo unificado de calcular_tiempo_restante sin duplicidad de código.
    """
    # Consulta la convocatoria abierta más reciente
    convocatoria_abierta = Convocatoria.objects.filter(estado='ABIERTA').first()
    tiempo = calcular_tiempo_restante(convocatoria_abierta)

    # Si expiró o no existe, el banner no se despliega
    mostrar_banner = bool(convocatoria_abierta and not tiempo['periodo_vencido'])

    dias_restantes = tiempo['valor'] if tiempo['unidad'] == 'DIAS' else None
    horas_restantes = tiempo['valor'] if tiempo['unidad'] == 'HORAS' else None
    minutos_restantes = tiempo['valor'] if tiempo['unidad'] == 'MINUTOS' else None
    es_ultimo_dia = tiempo['unidad'] in ['HORAS', 'MINUTOS']

    return render(request, 'seguimiento/index.html', {
        'convocatoria': convocatoria_abierta if mostrar_banner else None,
        'tiempo': tiempo,
        'dias_restantes': dias_restantes,
        'horas_restantes': horas_restantes,
        'minutos_restantes': minutos_restantes,
        'es_ultimo_dia': es_ultimo_dia,
        'periodo_vencido': tiempo['periodo_vencido'],
        'mostrar_banner': mostrar_banner,
    })


# =============================================================================
# CONTROL DE ACCESO (CU01)
# =============================================================================

def redirigir_por_rol(user):
    """Redirige automáticamente según el tipo de usuario institucional[cite: 4, 6]."""
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


def iniciar_sesion(request):
    """CU01: Iniciar sesión y redirección por rol con soporte de correo institucional[cite: 4, 6]."""
    if request.user.is_authenticated:
        return redirigir_por_rol(request.user)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            identificador = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']

            # Intento 1: Autenticación con nombre de usuario estándar
            user = authenticate(request, username=identificador, password=password)

            # Intento 2: Autenticación mediante correo institucional si se ingresó un email
            if not user and '@' in identificador:
                usuario_obj = User.objects.filter(email__iexact=identificador).first()
                if usuario_obj:
                    user = authenticate(request, username=usuario_obj.username, password=password)

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
    """Cierra la sesión del usuario y redirige a la portada[cite: 4, 6]."""
    logout(request)
    return redirect('index')


# =============================================================================
# GESTIÓN DE PERFIL PROPIO Y PREFERENCIAS
# =============================================================================

@login_required
def editar_mi_perfil(request):
    """Permite al usuario autenticado actualizar sus datos personales, tema y contraseña."""
    usuario = request.user
    perfil = getattr(usuario, 'perfil', None)
    config, _ = ConfiguracionUsuario.objects.get_or_create(perfil=perfil)
    telefono_obj = perfil.telefonos.first() if perfil else None

    if request.method == 'POST':
        form = MiPerfilForm(request.POST)
        if form.is_valid():
            datos = form.cleaned_data
            nuevo_email = datos['email'].strip().lower()

            # Validación de colisión de email con otros usuarios
            if User.objects.filter(email__iexact=nuevo_email).exclude(pk=usuario.pk).exists():
                messages.error(request, 'El correo institucional ingresado ya pertenece a otro usuario registrado.')
                return render(request, 'seguimiento/mi_perfil.html', {'form': form, 'perfil': perfil})

            # 1. Credenciales y correo
            usuario.email = nuevo_email
            if datos.get('nueva_password'):
                usuario.set_password(datos['nueva_password'])
                update_session_auth_hash(request, usuario)
            usuario.save()

            # 2. Datos personales y telefónicos
            if perfil:
                perfil.primer_nombre = datos['primer_nombre'].strip()
                perfil.segundo_nombre = datos.get('segundo_nombre', '').strip()
                perfil.apellido_paterno = datos['apellido_paterno'].strip()
                perfil.apellido_materno = datos['apellido_materno'].strip()
                perfil.save()

                numero_tel = datos.get('telefono', '').strip()
                if numero_tel:
                    if telefono_obj:
                        telefono_obj.numero_telefono = numero_tel
                        telefono_obj.save()
                    else:
                        TelefonoUsuario.objects.create(perfil=perfil, numero_telefono=numero_tel)

            # 3. Preferencia de interfaz (tema visual)
            if 'tema' in datos:
                config.tema = datos['tema']
                config.save()

            messages.success(request, 'Tus datos de perfil y preferencias se actualizaron correctamente.')
            return redirect('mi_perfil')
    else:
        form = MiPerfilForm(initial={
            'email': usuario.email,
            'primer_nombre': perfil.primer_nombre if perfil else usuario.first_name,
            'segundo_nombre': perfil.segundo_nombre if perfil else '',
            'apellido_paterno': perfil.apellido_paterno if perfil else usuario.last_name,
            'apellido_materno': perfil.apellido_materno if perfil else '',
            'telefono': telefono_obj.numero_telefono if telefono_obj else '',
            'tema': config.tema if config else 'LIGHT',
        })

    return render(request, 'seguimiento/mi_perfil.html', {'form': form, 'perfil': perfil})