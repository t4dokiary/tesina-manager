import os
import django
from datetime import date, timedelta
from django.utils import timezone
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tesina_manager.settings')
django.setup()

from django.contrib.auth.models import User
from seguimiento.models import (
    PerfilUsuario, Alumno, Asesor, Coordinador,
    Convocatoria, ProyectoTesis, EntregableVersion,
    MinutaAsesoria, CompromisoAcuerdo
)

def crear_usuario_rol(username, email, password, nombre, paterno, tipo_rol):
    user, _ = User.objects.get_or_create(username=username, email=email)
    user.set_password(password)
    user.first_name = nombre
    user.last_name = paterno
    user.save()

    perfil, _ = PerfilUsuario.objects.get_or_create(
        user=user,
        defaults={
            'primer_nombre': nombre,
            'apellido_paterno': paterno,
            'apellido_materno': 'BUAP',
            'tipo_usuario': tipo_rol,
            'estado_registro': 'ACTIVO'
        }
    )
    return perfil

def poblar():
    print("--- 1. Creando Usuarios y Perfiles ---")
    
    # 1. Coordinador
    perfil_coord = crear_usuario_rol('coordinador', 'coord@correo.buap.mx', 'admin123', 'Juan', 'Pérez', 'COORDINADOR')
    Coordinador.objects.get_or_create(
        perfil=perfil_coord,
        defaults={'cubiculo_oficina': 'Cubículo FCC-102', 'telefono_oficina': '2221234567'}
    )

    # 2. Asesor Docente
    perfil_asesor = crear_usuario_rol('asesor_carlos', 'carlos@correo.buap.mx', 'asesor123', 'Carlos', 'Hernández', 'ASESOR')
    Asesor.objects.get_or_create(
        perfil=perfil_asesor,
        defaults={'numero_empleado': 'EMP-8921', 'grado_academico': 'Dr.', 'area_especialidad': 'Ingeniería de Software'}
    )

    # 3. Alumno A (Activo / Al corriente)
    perfil_alumno1 = crear_usuario_rol('alumno_luis', 'luis@correo.buap.mx', 'alumno123', 'Luis', 'Martínez', 'ALUMNO')
    alumno1, _ = Alumno.objects.get_or_create(perfil=perfil_alumno1, defaults={'matricula': '202100123'})

    # 4. Alumno B (En riesgo de rezago > 30 días)
    perfil_alumno2 = crear_usuario_rol('alumno_ana', 'ana@correo.buap.mx', 'alumno123', 'Ana', 'Gómez', 'ALUMNO')
    alumno2, _ = Alumno.objects.get_or_create(perfil=perfil_alumno2, defaults={'matricula': '202100456'})

    print("--- 2. Creando Convocatoria Oficial ---")
    convocatoria, _ = Convocatoria.objects.get_or_create(
        periodo='2026-S2',
        defaults={
            'titulo': 'Convocatoria Titulación Otoño 2026',
            'descripcion': 'Periodo semestral oficial para registro de proyectos de posgrado.',
            'fecha_inicio': date.today() - timedelta(days=60),
            'fecha_limite_protocolo': date.today() + timedelta(days=30),
            'fecha_cierre': date.today() + timedelta(days=90),
            'activa': True,
            'estado': 'ABIERTA',
            'creada_por': perfil_coord
        }
    )

    print("--- 3. Creando Proyectos de Tesis ---")
    pdf_ficticio = ContentFile(b"%PDF-1.4\n%Fake PDF for Testing CU02\n%%EOF", name="protocolo_muestra.pdf")

    # Proyecto 1: Activo y al corriente
    proy1, _ = ProyectoTesis.objects.get_or_create(
        alumno=perfil_alumno1,
        defaults={
            'asesor': perfil_asesor,
            'coordinador': perfil_coord,
            'convocatoria': convocatoria,
            'titulo_tesis': 'Plataforma Web de Seguimiento y Control de Tesis en Posgrado',
            'linea_investigacion': 'Sistemas Distribuidos y Web',
            'estado_proyecto': 'APROBADO',
            'archivo_protocolo': pdf_ficticio,
            'fecha_ultimo_avance': date.today() - timedelta(days=5)
        }
    )

    # Proyecto 2: En Rezago (> 30 días sin actividad)
    proy2, _ = ProyectoTesis.objects.get_or_create(
        alumno=perfil_alumno2,
        defaults={
            'asesor': perfil_asesor,
            'coordinador': perfil_coord,
            'convocatoria': convocatoria,
            'titulo_tesis': 'Análisis Comparativo de Algoritmos Criptográficos Ligeros',
            'linea_investigacion': 'Ciberseguridad',
            'estado_proyecto': 'APROBADO',
            'archivo_protocolo': pdf_ficticio,
            'fecha_ultimo_avance': date.today() - timedelta(days=38) # Provoca alerta CU04
        }
    )

    print("--- 4. Creando Entregables de Borrador en PDF (CU02) ---")
    pdf_borrador = ContentFile(b"%PDF-1.4\n%Borrador v1 de Capitulo 1\n%%EOF", name="borrador_cap1.pdf")
    EntregableVersion.objects.get_or_create(
        proyecto=proy1,
        numero_version=1,
        defaults={
            'ruta_archivo_pdf': pdf_borrador,
            'comentario_alumno': 'Se entrega el borrador del Capítulo 1 para revisión.',
            'retroalimentacion_asesor': 'Excelente estructuración. Profundizar en la justificación metodológica.'
        }
    )

    print("--- 5. Creando Minutas de Asesoría y Acuerdos (CU03) ---")
    minuta, _ = MinutaAsesoria.objects.get_or_create(
        proyecto=proy1,
        fecha_reunion=date.today() - timedelta(days=5),
        defaults={
            'modalidad': 'PRESENCIAL',
            'resumen_temas': 'Revisión general de avances del marco teórico y diseño de base de datos.'
        }
    )

    CompromisoAcuerdo.objects.get_or_create(
        minuta=minuta,
        numero_acuerdo=1,
        defaults={
            'descripcion_tarea': 'Redactar el estado del arte con al menos 10 fuentes indexadas.',
            'responsable': 'ALUMNO',
            'fecha_limite': date.today() + timedelta(days=10),
            'estado': 'PENDIENTE'
        }
    )

    print("\n Base de datos poblada exitosamente.")
    print("--------------------------------------------------")
    print("Credenciales generadas para pruebas:")
    print("  * Coordinador : usuario='coordinador'    | pass='admin123'")
    print("  * Asesor      : usuario='asesor_carlos'  | pass='asesor123'")
    print("  * Alumno (OK) : usuario='alumno_luis'    | pass='alumno123'")
    print("  * Alumno (Rez): usuario='alumno_ana'     | pass='alumno123'")
    print("--------------------------------------------------")

if __name__ == '__main__':
    poblar()