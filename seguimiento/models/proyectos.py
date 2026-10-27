from datetime import date
from django.db import models
from .utils import validar_solo_pdf, ruta_protocolo_alumno
from .usuarios import PerfilUsuario
from .convocatorias import Convocatoria


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
    
    archivo_protocolo = models.FileField(upload_to=ruta_protocolo_alumno, validators=[validar_solo_pdf], null=True, blank=True)
    
    estado_proyecto = models.CharField(max_length=30, choices=ESTADOS, default='PENDIENTE')
    observaciones_coordinador = models.TextField(blank=True, null=True)
    fecha_dictamen_coordinador = models.DateField(null=True, blank=True)

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