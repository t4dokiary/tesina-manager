import os
from django.core.exceptions import ValidationError

def validar_archivo_pdf_estricto(archivo):
    """
    Inspecciona la extensión, el tamaño y los Magic Bytes (cabecera binaria)
    para evitar archivos maliciosos renombrados como .pdf.
    """
    # 1. Validar extensión
    ext = os.path.splitext(archivo.name)[1].lower()
    if ext != '.pdf':
        raise ValidationError('Solo se admiten documentos con extensión .pdf.')

    # 2. Validar tamaño (máximo 15 MB)
    max_mb = 15
    if archivo.size > max_mb * 1024 * 1024:
        raise ValidationError(f'El archivo excede el tamaño máximo permitido de {max_mb} MB.')

    # 3. Validar cabecera binaria (%PDF-)
    posicion_original = archivo.tell()
    archivo.seek(0)
    cabecera = archivo.read(5)
    archivo.seek(posicion_original)

    if cabecera != b'%PDF-':
        raise ValidationError('El archivo no tiene una estructura PDF válida o está corrupto.')