import os
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# ==============================================================================
# VALIDACIONES Y GENERADORES DE RUTA (CU02)
# ==============================================================================

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


# ==============================================================================
# 1. IDENTIDAD, PERFILES Y AJUSTES
# ==============================================================================

class PerfilUsuario(models.Model):
    ROLES = [
        ('ALUMNO', 'Alumno'),
        ('ASESOR', 'Asesor'),
        ('COORDINADOR', 'Coordinador'),
    ]

    ESTADOS_REGISTRO = [
        ('PENDIENTE', 'Pendiente de Validación'),
        ('ACTIVO', 'Activo / Aprobado'),
        ('INACTIVO', 'Inactivo / Suspendido'),
    ]

    id_usuario = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    primer_nombre = models.CharField(max_length=50)
    segundo_nombre = models.CharField(max_length=50, blank=True, null=True)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    tipo_usuario = models.CharField(max_length=20, choices=ROLES)
    estado_registro = models.CharField(max_length=20, choices=ESTADOS_REGISTRO, default='ACTIVO')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    cuenta_activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return f"{self.primer_nombre} {self.apellido_paterno} ({self.tipo_usuario})"


class ConfiguracionUsuario(models.Model):
    TEMAS_CHOICES = [
        ('SYSTEM', 'Predeterminado del sistema'),
        ('LIGHT', 'Tema Claro'),
        ('DARK', 'Tema Oscuro'),
    ]

    id_configuracion = models.AutoField(primary_key=True)
    perfil = models.OneToOneField(
        PerfilUsuario, 
        on_delete=models.CASCADE, 
        related_name='configuracion'
    )
    tema = models.CharField(max_length=10, choices=TEMAS_CHOICES, default='SYSTEM')
    notif_inicio_sesion = models.BooleanField(default=True)
    notif_comentarios = models.BooleanField(default=True)
    notif_minutas = models.BooleanField(default=True)

    class Meta:
        db_table = 'configuracion_usuario'

    def __str__(self):
        return f"Configuración de {self.perfil.primer_nombre}"


@receiver(post_save, sender=PerfilUsuario)
def crear_configuracion_automatica(sender, instance, created, **kwargs):
    if created:
        ConfiguracionUsuario.objects.create(perfil=instance)


class TelefonoUsuario(models.Model):
    id_telefono = models.AutoField(primary_key=True)
    perfil = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE, related_name='telefonos')
    numero_telefono = models.CharField(max_length=20)

    class Meta:
        db_table = 'telefono_usuario'

    def __str__(self):
        return self.numero_telefono


class Alumno(models.Model):
    id_alumno = models.AutoField(primary_key=True)
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='datos_alumno')
    matricula = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = 'alumno'

    def __str__(self):
        return f"{self.perfil.primer_nombre} {self.perfil.apellido_paterno} ({self.matricula})"


class Asesor(models.Model):
    id_asesor = models.AutoField(primary_key=True)
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='datos_asesor')
    numero_empleado = models.CharField(max_length=20, unique=True)
    grado_academico = models.CharField(max_length=50)
    area_especialidad = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'asesor'

    def __str__(self):
        return f"{self.grado_academico} {self.perfil.primer_nombre} {self.perfil.apellido_paterno}"


class Coordinador(models.Model):
    id_coordinador = models.AutoField(primary_key=True)
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='datos_coordinador')
    cubiculo_oficina = models.CharField(max_length=50, blank=True, null=True)
    telefono_oficina = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'coordinador'

    def __str__(self):
        return f"Coordinador: {self.perfil.primer_nombre} {self.perfil.apellido_paterno}"


# ==============================================================================
# 2. CONVOCATORIAS OFICIALES
# ==============================================================================

class Convocatoria(models.Model):
    """Periodos oficiales para entrega de protocolos y trámites de titulación."""
    ESTADOS = [
        ('ABIERTA', 'Abierta / En Curso'),
        ('CERRADA', 'Cerrada / Finalizada'),
        ('PROXIMA', 'Próxima a Iniciar'),
    ]

    id_convocatoria = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=150, help_text="Ej. Convocatoria Titulación Otoño 2026")
    periodo = models.CharField(max_length=50, help_text="Ej. 2026-S2")
    descripcion = models.TextField(blank=True, help_text="Detalles, requisitos o indicaciones generales.")
    fecha_inicio = models.DateField()
    fecha_limite_protocolo = models.DateField(help_text="Fecha máxima para registrar protocolo de tesis")
    fecha_cierre = models.DateField(help_text="Fecha de fin del periodo")
    activa = models.BooleanField(default=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ABIERTA')
    creada_por = models.ForeignKey(PerfilUsuario, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'convocatoria'
        ordering = ['-fecha_creacion']

    @property
    def esta_vigente(self):
        hoy = date.today()
        return self.activa and (self.fecha_inicio <= hoy <= self.fecha_cierre)

    def __str__(self):
        return f"{self.titulo} ({self.periodo})"


# ==============================================================================
# 3. EXPEDIENTE DE PROYECTO DE TESIS
# ==============================================================================

class ProyectoTesis(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente de Aprobación'),
        ('APROBADO', 'Protocolo Aprobado / En desarrollo'),
        ('RECHAZADO', 'Rechazado con Observaciones'),
        ('CONCLUIDO', 'Concluido'),
    ]

    id_proyecto = models.AutoField(primary_key=True)
    alumno = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='proyecto_alumno')
    asesor = models.ForeignKey(PerfilUsuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='proyectos_dirigidos')
    coordinador = models.ForeignKey(PerfilUsuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='proyectos_supervisados')
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='proyectos')
    
    titulo_tesis = models.CharField(max_length=255)
    linea_investigacion = models.CharField(max_length=255)
    
    # Archivo del protocolo inicial
    archivo_protocolo = models.FileField(upload_to=ruta_protocolo_alumno, validators=[validar_solo_pdf], null=True, blank=True)
    
    # Dictamen de Coordinación
    estado_proyecto = models.CharField(max_length=30, choices=ESTADOS, default='PENDIENTE')
    observaciones_coordinador = models.TextField(blank=True, null=True)
    fecha_dictamen_coordinador = models.DateField(null=True, blank=True)

    # Fechas de control y semáforo de inactividad
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_ultimo_avance = models.DateField(default=date.today)

    class Meta:
        db_table = 'proyecto_tesis'

    @property
    def dias_inactividad(self):
        if not self.fecha_ultimo_avance:
            return 0
        return (date.today() - self.fecha_ultimo_avance).days

    @property
    def tiene_alerta_rezago(self):
        return self.dias_inactividad > 30

    def __str__(self):
        return f"{self.titulo_tesis} ({self.get_estado_proyecto_display()})"


# ==============================================================================
# 4. ENTREGABLES INMUTABLES DE BORRADORES (CU02)
# ==============================================================================

class EntregableVersion(models.Model):
    id_entregable = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(ProyectoTesis, on_delete=models.CASCADE, related_name='entregables')
    numero_version = models.PositiveIntegerField()
    ruta_archivo_pdf = models.FileField(upload_to='entregables_tesis/')
    comentario_alumno = models.TextField(blank=True, null=True)
    fecha_hora_subida = models.DateTimeField(auto_now_add=True)
    
    # Campo para que el asesor devuelva el PDF con marcas/notas
    archivo_correccion_asesor = models.FileField(
        upload_to='correcciones_asesor/',
        blank=True,
        null=True
    )
    retroalimentacion_asesor = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'entregable_version'
        unique_together = ('proyecto', 'numero_version')

    def __str__(self):
        return f"{self.proyecto.titulo_tesis} - v{self.numero_version}"


class MensajeEntrega(models.Model):
    """Mensajes de discusión / retroalimentación tipo chat sobre un borrador específico."""
    id_mensaje = models.AutoField(primary_key=True)
    entregable = models.ForeignKey(EntregableVersion, on_delete=models.CASCADE, related_name='mensajes')
    emisor = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE)
    mensaje = models.TextField()
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mensaje_entrega'
        ordering = ['fecha_hora']

    def __str__(self):
        return f"Msg de {self.emisor} en v{self.entregable.numero_version}"


# ==============================================================================
# 5. MINUTAS Y COMPROMISOS DE ASESORÍA (CU03)
# ==============================================================================

class MinutaAsesoria(models.Model):
    """Formalización digital de sesiones y acuerdos (CU03)."""
    MODALIDADES = [
        ('PRESENCIAL', 'Presencial (Cubículo / Facultad)'),
        ('VIRTUAL', 'Virtual (Teams / Google Meet)'),
    ]

    id_minuta = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey('ProyectoTesis', on_delete=models.CASCADE, related_name='minutas')
    # Vinculación opcional con la versión que se revisó en esa sesión
    version_revisada = models.ForeignKey(
        'EntregableVersion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='minutas_asociadas'
    )
    fecha_reunion = models.DateField()
    hora_reunion = models.TimeField(null=True, blank=True)
    modalidad = models.CharField(max_length=20, choices=MODALIDADES, default='PRESENCIAL')
    
    # Ubicación o Enlace
    lugar_reunion = models.TextField(
        blank=True, 
        null=True, 
        help_text="Ej. Cubículo 105 FCC o Enlace de Teams / Google Meet"
    )
    resumen_temas = models.TextField(help_text="Resumen de temas tratados y retroalimentación")
    
    # Doble firma / Validación de cumplimiento de visita
    firmada_asesor = models.BooleanField(default=True) # El asesor firma al crearla
    fecha_firma_asesor = models.DateTimeField(auto_now_add=True)
    firmada_alumno = models.BooleanField(default=False) # El alumno firma de conformidad
    fecha_firma_alumno = models.DateTimeField(null=True, blank=True)
    
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'minutas_asesoria'
        ordering = ['-fecha_reunion']

    def __str__(self):
        return f"Minuta {self.fecha_reunion} — {self.proyecto.titulo_tesis}"


class CompromisoAcuerdo(models.Model):
    """Tareas calendarizadas que se desprenden de una minuta."""
    RESPONSABLES = [
        ('ALUMNO', 'Alumno (Tesista)'),
        ('ASESOR', 'Asesor (Director)'),
    ]
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CUMPLIDO', 'Cumplido'),
    ]

    id_acuerdo = models.AutoField(primary_key=True)
    minuta = models.ForeignKey(MinutaAsesoria, on_delete=models.CASCADE, related_name='acuerdos')
    numero_acuerdo = models.PositiveIntegerField(default=1)
    descripcion_tarea = models.TextField()
    responsable = models.CharField(max_length=10, choices=RESPONSABLES, default='ALUMNO')
    fecha_limite = models.DateField()
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    estado_cumplido = models.BooleanField(default=False)
    fecha_cumplimiento = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'compromiso_acuerdo'
        ordering = ['fecha_limite']

    def __str__(self):
        return f"Tarea: {self.descripcion_tarea[:35]} ({self.estado})"

class MaterialApoyoMinuta(models.Model):
    """Archivos PDF de ejemplo, bibliografía o guías recomendadas por el Asesor."""
    id_material = models.AutoField(primary_key=True)
    minuta = models.ForeignKey(MinutaAsesoria, on_delete=models.CASCADE, related_name='materiales')
    titulo = models.CharField(max_length=150, help_text="Ej. Artículo IEEE de referencia / Plantilla Cap. 3")
    archivo_pdf = models.FileField(upload_to='materiales_asesoria/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'material_apoyo_minuta'

    def __str__(self):
        return self.titulo

# ==============================================================================
# 6. MONITOREO Y ALERTAS DE REZAGO (CU04)
# ==============================================================================

class AlertaRezago(models.Model):
    id_alerta = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(ProyectoTesis, on_delete=models.CASCADE, related_name='alertas')
    fecha_deteccion = models.DateField(auto_now_add=True)
    dias_acumulados = models.PositiveIntegerField()
    estado_alerta = models.CharField(max_length=50, default='Pendiente')

    class Meta:
        db_table = 'alerta_rezago'
        ordering = ['-fecha_deteccion']

    def __str__(self):
        return f"Alerta {self.proyecto.titulo_tesis} ({self.dias_acumulados} días)"
