import os
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class ValidadorPDFEstricto:
    """
    Validador integral para archivos PDF (CU02).
    Inspecciona:
      1. Extensión declarada (.pdf)
      2. Tamaño no nulo y límite superior en megabytes
      3. Cabecera binaria / Magic Bytes (%PDF-)
      4. Marcador de cierre de archivo (%%EOF)
    """

    def __init__(self, max_mb=15):
        self.max_mb = max_mb

    def __call__(self, archivo):
        # 1. Validar nombre y extensión
        if not archivo.name:
            raise ValidationError('El documento no posee un nombre de archivo válido.')

        ext = os.path.splitext(archivo.name)[1].lower()
        if ext != '.pdf':
            raise ValidationError('Solo se admiten documentos en formato PDF (.pdf).')

        # 2. Validar tamaño (no vacío y dentro del límite)
        tamano = getattr(archivo, 'size', 0)
        if tamano == 0:
            raise ValidationError('El archivo seleccionado está vacío (0 bytes).')

        max_bytes = self.max_mb * 1024 * 1024
        if tamano > max_bytes:
            raise ValidationError(
                f'El archivo excede el tamaño máximo permitido de {self.max_mb} MB.'
            )

        # 3. Validación de integridad binaria con preservación del puntero
        posicion_inicial = archivo.tell()
        try:
            archivo.seek(0)
            cabecera = archivo.read(5)

            # Magic bytes oficiales: %PDF-
            if cabecera != b'%PDF-':
                raise ValidationError(
                    'El archivo no tiene una estructura PDF válida o está corrupto.'
                )

            # 4. Validar firma de terminación (últimos 1024 bytes deben contener %%EOF)
            bytes_a_leer = min(tamano, 1024)
            archivo.seek(tamano - bytes_a_leer)
            cola = archivo.read(bytes_a_leer)
            if b'%%EOF' not in cola:
                raise ValidationError(
                    'El documento PDF parece estar incompleto o truncado.'
                )

        finally:
            # Restaurar siempre el puntero para que Django almacene el archivo correctamente
            archivo.seek(posicion_inicial)

    def __eq__(self, other):
        return isinstance(other, ValidadorPDFEstricto) and self.max_mb == other.max_mb


# Instancia directa lista para usar como función en models.py y forms.py
validar_archivo_pdf_estricto = ValidadorPDFEstricto(max_mb=15)