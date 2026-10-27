import os
from datetime import date
from django.core.exceptions import ValidationError


def validar_solo_pdf(archivo):
    """Regla obligatoria: Solo archivos PDF."""
    extension = os.path.splitext(archivo.name)[1].lower()
    if extension != '.pdf':
        raise ValidationError('Solo se permiten archivos en formato PDF.')


def ruta_protocolo_alumno(instance, filename):
    """Organiza los protocolos iniciales por año/mes/matrícula."""
    matricula = instance.alumno.datos_alumno.matricula
    fecha_hoy = date.today()
    return f"protocolos/{fecha_hoy.year}/{fecha_hoy.month:02d}/{matricula}/{filename}"


def ruta_entregable_alumno(instance, filename):
    """Almacena versiones inmutables de los borradores en PDF."""
    matricula = instance.proyecto.alumno.datos_alumno.matricula
    fecha_hoy = date.today()
    return f"entregables/{fecha_hoy.year}/{fecha_hoy.month:02d}/{matricula}/v{instance.numero_version}_{filename}"