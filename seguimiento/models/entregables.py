from django.db import models
from .utils import validar_solo_pdf
from .usuarios import PerfilUsuario
from .proyectos import ProyectoTesis


class EntregableVersion(models.Model):
    id_entregable = models.AutoField(primary_key=True)
    proyecto = models.ForeignKey(ProyectoTesis, on_delete=models.CASCADE, related_name='entregables')
    numero_version = models.PositiveIntegerField()
    ruta_archivo_pdf = models.FileField(upload_to='entregables_tesis/', validators=[validar_solo_pdf])
    comentario_alumno = models.TextField(blank=True, null=True)
    fecha_hora_subida = models.DateTimeField(auto_now_add=True)
    
    archivo_correccion_asesor = models.FileField(
        upload_to='correcciones_asesor/',
        blank=True,
        null=True,
        validators=[validar_solo_pdf]
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