from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    PerfilUsuario,
    ConfiguracionUsuario,
    TelefonoUsuario,
    Alumno,
    Asesor,
    Coordinador,
    Convocatoria,
    ProyectoTesis,
    EntregableVersion,
    MensajeEntrega,
    MinutaAsesoria,
    CompromisoAcuerdo,
    MaterialApoyoMinuta,
    AlertaRezago,
)

# ---------------------------------------------------------
# Formularios anidados (Inlines)
# ---------------------------------------------------------

class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Datos del Perfil (Rol en el Sistema)'
    fk_name = 'user'

# Desregistramos el User original y lo volvemos a registrar con el Perfil incluido
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_rol', 'is_staff')

    @admin.display(description='Rol Asignado')
    def get_rol(self, instance):
        if hasattr(instance, 'perfil'):
            return instance.perfil.get_tipo_usuario_display()
        return 'Sin perfil asignado'


# ---------------------------------------------------------
# Modelos del Sistema
# ---------------------------------------------------------

@admin.register(Coordinador)
class CoordinadorAdmin(admin.ModelAdmin):
    list_display = ('get_nombre', 'cubiculo_oficina', 'telefono_oficina', 'get_correo')
    search_fields = ('perfil__primer_nombre', 'perfil__apellido_paterno', 'cubiculo_oficina')

    @admin.display(description='Coordinador')
    def get_nombre(self, obj):
        return f"{obj.perfil.primer_nombre} {obj.perfil.apellido_paterno}"

    @admin.display(description='Correo Institucional')
    def get_correo(self, obj):
        return obj.perfil.user.email


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('primer_nombre', 'apellido_paterno', 'tipo_usuario', 'estado_registro', 'cuenta_activa', 'fecha_registro')
    list_filter = ('tipo_usuario', 'estado_registro', 'cuenta_activa')
    search_fields = ('primer_nombre', 'apellido_paterno', 'user__username', 'user__email')


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'get_nombre', 'get_correo')
    search_fields = ('matricula', 'perfil__primer_nombre', 'perfil__apellido_paterno')

    @admin.display(description='Alumno')
    def get_nombre(self, obj):
        return f"{obj.perfil.primer_nombre} {obj.perfil.apellido_paterno}"

    @admin.display(description='Correo')
    def get_correo(self, obj):
        return obj.perfil.user.email


@admin.register(Asesor)
class AsesorAdmin(admin.ModelAdmin):
    list_display = ('numero_empleado', 'grado_academico', 'get_nombre', 'area_especialidad')
    search_fields = ('numero_empleado', 'perfil__primer_nombre', 'perfil__apellido_paterno')

    @admin.display(description='Asesor')
    def get_nombre(self, obj):
        return f"{obj.perfil.primer_nombre} {obj.perfil.apellido_paterno}"


@admin.register(Convocatoria)
class ConvocatoriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'periodo', 'fecha_inicio', 'fecha_limite_protocolo', 'fecha_cierre', 'estado', 'activa')
    list_filter = ('estado', 'activa')


@admin.register(ProyectoTesis)
class ProyectoTesisAdmin(admin.ModelAdmin):
    list_display = ('titulo_tesis', 'alumno', 'asesor', 'estado_proyecto', 'dias_inactividad', 'tiene_alerta_rezago')
    list_filter = ('estado_proyecto', 'convocatoria')
    search_fields = ('titulo_tesis', 'linea_investigacion')


@admin.register(EntregableVersion)
class EntregableVersionAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'numero_version', 'fecha_hora_subida')
    readonly_fields = ('fecha_hora_subida',)


@admin.register(MinutaAsesoria)
class MinutaAsesoriaAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'fecha_reunion', 'modalidad', 'firmada_asesor', 'firmada_alumno')
    list_filter = ('modalidad', 'firmada_asesor', 'firmada_alumno')


@admin.register(AlertaRezago)
class AlertaRezagoAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'dias_acumulados', 'fecha_deteccion', 'estado_alerta')