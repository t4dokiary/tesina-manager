from django.db import models
from .proyectos import ProyectoTesis


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