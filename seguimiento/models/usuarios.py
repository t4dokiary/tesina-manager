from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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