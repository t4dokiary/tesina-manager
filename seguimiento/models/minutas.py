from django.db import models
from .utils import validar_solo_pdf
from .proyectos import ProyectoTesis
from .entregables import EntregableVersion


class MinutaAsesoria(models.Model):
    """Formalización digital de sesiones y acuerdos (CU03)."""
    MODALIDADES = [
        ('PRESENCIAL', 'Presencial (Cubículo / Facultad)'),
        ('VIRTUAL', 'Virtual (Teams / Google Meet)'),
    ]

    id_minuta = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(ProyectoTesis, on_delete=models.CASCADE, related_name='minutas')
    version_revisada = models.ForeignKey(
        EntregableVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='minutas_asociadas'
    )
    fecha_reunion = models.DateField()
    hora_reunion = models.TimeField(null=True, blank=True)
    modalidad = models.CharField(max_length=20, choices=MODALIDADES, default='PRESENCIAL')
    
    lugar_reunion = models.TextField(
        blank=True, 
        null=True, 
        help_text="Ej. Cubículo 105 FCC o Enlace de Teams / Google Meet"
    )
    resumen_temas = models.TextField(help_text="Resumen de temas tratados y retroalimentación")
    
    firmada_asesor = models.BooleanField(default=True)
    fecha_firma_asesor = models.DateTimeField(auto_now_add=True)
    firmada_alumno = models.BooleanField(default=False)
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
    archivo_pdf = models.FileField(upload_to='materiales_asesoria/', validators=[validar_solo_pdf])
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'material_apoyo_minuta'

    def __str__(self):
        return self.titulo