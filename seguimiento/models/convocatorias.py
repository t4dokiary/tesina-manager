from datetime import date
from django.db import models
from .usuarios import PerfilUsuario


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