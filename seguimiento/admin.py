from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html

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
    MinutaAsesoria,
    CompromisoAcuerdo,
    AlertaRezago,
)

# ==============================================================================
# PERSONALIZACIÓN DEL ENTORNO INSTITUCIONAL
# ==============================================================================
admin.site.site_header = "Plataforma de Seguimiento de Tesinas de Posgrado"
admin.site.site_title = "Administración - TesisManager"
admin.site.index_title = "Panel de Control y Supervisión Académica"


# ==============================================================================
# FORMULARIOS ANIDADOS (INLINES)
# ==============================================================================

class TelefonoUsuarioInline(admin.TabularInline):
    model = TelefonoUsuario
    extra = 1
    verbose_name = "Teléfono de Contacto"
    verbose_name_plural = "Teléfonos de Contacto"


class ConfiguracionUsuarioInline(admin.StackedInline):
    model = ConfiguracionUsuario
    can_delete = False
    max_num = 1
    verbose_name = "Preferencia y Notificaciones"
    verbose_name_plural = "Preferencias del Usuario"


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name = "Perfil Académico"
    verbose_name_plural = "Datos del Perfil Institucional"
    fk_name = "user"


class CompromisoAcuerdoInline(admin.TabularInline):
    model = CompromisoAcuerdo
    extra = 1
    fields = ('numero_acuerdo', 'descripcion_tarea', 'responsable', 'fecha_limite', 'estado')
    ordering = ('numero_acuerdo',)
    verbose_name = "Acuerdo de Asesoría"
    verbose_name_plural = "Acuerdos y Compromisos Acordados"


# ==============================================================================
# INTEGRACIÓN DEL USUARIO BASE CON SU PERFIL
# ==============================================================================

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ('username', 'email', 'get_nombre_completo', 'get_rol_badge', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'perfil__tipo_usuario')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'perfil__primer_nombre', 'perfil__apellido_paterno')
    list_select_related = ('perfil',)

    @admin.display(description='Nombre Completo')
    def get_nombre_completo(self, obj):
        if hasattr(obj, 'perfil'):
            return f"{obj.perfil.primer_nombre} {obj.perfil.apellido_paterno}"
        return obj.get_full_name() or "Sin nombre registrado"

    @admin.display(description='Rol Asignado')
    def get_rol_badge(self, obj):
        if not hasattr(obj, 'perfil'):
            return format_html('<span style="color: #6c757d;">Sin perfil</span>')
        colores = {
            'ALUMNO': '#0d6efd',
            'ASESOR': '#198754',
            'COORDINADOR': '#6f42c1',
        }
        color = colores.get(obj.perfil.tipo_usuario, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.perfil.get_tipo_usuario_display()
        )


# ==============================================================================
# MODELOS DE PERFILES Y ROLES DE POSGRADO
# ==============================================================================

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('primer_nombre', 'apellido_paterno', 'tipo_usuario', 'estado_registro', 'cuenta_activa', 'fecha_registro')
    list_filter = ('tipo_usuario', 'estado_registro', 'cuenta_activa')
    search_fields = ('primer_nombre', 'apellido_paterno', 'apellido_materno', 'user__username', 'user__email')
    inlines = [TelefonoUsuarioInline, ConfiguracionUsuarioInline]
    list_select_related = ('user',)


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'get_nombre_completo', 'get_correo', 'get_estado_cuenta')
    search_fields = ('matricula', 'perfil__primer_nombre', 'perfil__apellido_paterno', 'perfil__user__email')
    list_select_related = ('perfil', 'perfil__user')

    @admin.display(description='Alumno (Tesista)')
    def get_nombre_completo(self, obj):
        return f"{obj.perfil.primer_nombre} {obj.perfil.apellido_paterno} {obj.perfil.apellido_materno}"

    @admin.display(description='Correo Institucional')
    def get_correo(self, obj):
        return obj.perfil.user.email

    @admin.display(description='Estado de Cuenta', boolean=True)
    def get_estado_cuenta(self, obj):
        return obj.perfil.cuenta_activa


@admin.register(Asesor)
class AsesorAdmin(admin.ModelAdmin):
    list_display = ('numero_empleado', 'grado_academico', 'get_nombre_completo', 'area_especialidad', 'get_estado_cuenta')
    list_filter = ('grado_academico',)
    search_fields = ('numero_empleado', 'perfil__primer_nombre', 'perfil__apellido_paterno', 'area_especialidad')
    list_select_related = ('perfil', 'perfil__user')

    @admin.display(description='Director / Asesor Docente')
    def get_nombre_completo(self, obj):
        return f"{obj.grado_academico} {obj.perfil.primer_nombre} {obj.perfil.apellido_paterno}"

    @admin.display(description='Activo', boolean=True)
    def get_estado_cuenta(self, obj):
        return obj.perfil.cuenta_activa


@admin.register(Coordinador)
class CoordinadorAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'cubiculo_oficina', 'telefono_oficina', 'get_correo')
    search_fields = ('perfil__primer_nombre', 'perfil__apellido_paterno', 'cubiculo_oficina')
    list_select_related = ('perfil', 'perfil__user')

    @admin.display(description='Coordinador de Posgrado')
    def get_nombre_completo(self, obj):
        return f"{obj.perfil.primer_nombre} {obj.perfil.apellido_paterno}"

    @admin.display(description='Correo Oficial')
    def get_correo(self, obj):
        return obj.perfil.user.email


# ==============================================================================
# CONVOCATORIAS Y PROCESO DE TESIS
# ==============================================================================

@admin.register(Convocatoria)
class ConvocatoriaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'periodo', 'fecha_inicio', 'fecha_limite_protocolo', 'fecha_cierre', 'get_estado_badge', 'activa')
    list_filter = ('estado', 'activa')
    search_fields = ('titulo', 'periodo')
    ordering = ('-fecha_creacion',)

    @admin.display(description='Estado')
    def get_estado_badge(self, obj):
        colores = {
            'ABIERTA': '#198754',
            'CERRADA': '#dc3545',
            'PROXIMA': '#ffc107; color: black',
        }
        color = colores.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )


@admin.register(ProyectoTesis)
class ProyectoTesisAdmin(admin.ModelAdmin):
    list_display = (
        'titulo_tesis',
        'get_tesista',
        'get_asesor',
        'get_estado_badge',
        'dias_inactividad',
        'get_semaforo_rezago',
    )
    list_filter = ('estado_proyecto', 'convocatoria')
    search_fields = (
        'titulo_tesis',
        'linea_investigacion',
        'alumno__primer_nombre',
        'alumno__apellido_paterno',
        'asesor__primer_nombre',
        'asesor__apellido_paterno',
    )
    readonly_fields = ('fecha_inicio', 'dias_inactividad', 'tiene_alerta_rezago')
    list_select_related = ('alumno', 'asesor', 'convocatoria')

    fieldsets = (
        ('Información General del Proyecto', {
            'fields': ('titulo_tesis', 'linea_investigacion', 'convocatoria', 'archivo_protocolo')
        }),
        ('Comité y Participantes', {
            'fields': ('alumno', 'asesor', 'coordinador')
        }),
        ('Resolución y Dictamen Oficial', {
            'fields': ('estado_proyecto', 'observaciones_coordinador', 'fecha_dictamen_coordinador')
        }),
        ('Métricas de Monitoreo Preventivo', {
            'fields': ('fecha_inicio', 'fecha_ultimo_avance', 'dias_inactividad', 'tiene_alerta_rezago')
        }),
    )

    @admin.display(description='Alumno Tesista')
    def get_tesista(self, obj):
        return f"{obj.alumno.primer_nombre} {obj.alumno.apellido_paterno}"

    @admin.display(description='Director / Asesor')
    def get_asesor(self, obj):
        if obj.asesor:
            return f"{obj.asesor.primer_nombre} {obj.asesor.apellido_paterno}"
        return format_html('<span style="color: #dc3545;">Sin asignar</span>')

    @admin.display(description='Estado del Proyecto')
    def get_estado_badge(self, obj):
        estilos = {
            'PENDIENTE': 'background-color: #ffc107; color: #000;',
            'APROBADO': 'background-color: #0d6efd; color: #fff;',
            'RECHAZADO': 'background-color: #dc3545; color: #fff;',
            'CONCLUIDO': 'background-color: #198754; color: #fff;',
        }
        estilo = estilos.get(obj.estado_proyecto, 'background-color: #6c757d; color: #fff;')
        return format_html(
            '<span style="{} padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            estilo,
            obj.get_estado_proyecto_display()
        )

    @admin.display(description='Semáforo Rezago')
    def get_semaforo_rezago(self, obj):
        if obj.tiene_alerta_rezago:
            return format_html('<span style="color: #dc3545; font-weight: bold;">🔴 Alerta (>30 días)</span>')
        return format_html('<span style="color: #198754; font-weight: bold;">🟢 Al día</span>')


# ==============================================================================
# ENTREGABLES, MINUTAS Y ALERTAS DE REZAGO
# ==============================================================================

@admin.register(EntregableVersion)
class EntregableVersionAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'numero_version', 'fecha_hora_subida', 'get_archivo_enlace')
    list_filter = ('numero_version', 'fecha_hora_subida')
    search_fields = ('proyecto__titulo_tesis', 'comentario_alumno')
    readonly_fields = ('numero_version', 'fecha_hora_subida')
    list_select_related = ('proyecto',)

    @admin.display(description='PDF del Borrador')
    def get_archivo_enlace(self, obj):
        if obj.ruta_archivo_pdf:
            return format_html('<a href="{}" target="_blank">📄 Abrir PDF (v{})</a>', obj.ruta_archivo_pdf.url, obj.numero_version)
        return "Sin archivo"


@admin.register(MinutaAsesoria)
class MinutaAsesoriaAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'fecha_reunion', 'modalidad', 'fecha_registro')
    list_filter = ('modalidad', 'fecha_reunion')
    search_fields = ('proyecto__titulo_tesis', 'resumen_temas')
    ordering = ('-fecha_reunion',)
    inlines = [CompromisoAcuerdoInline]
    list_select_related = ('proyecto',)


@admin.register(CompromisoAcuerdo)
class CompromisoAcuerdoAdmin(admin.ModelAdmin):
    list_display = ('minuta', 'numero_acuerdo', 'responsable', 'fecha_limite', 'get_estado_acuerdo')
    list_filter = ('responsable', 'estado', 'fecha_limite')
    search_fields = ('descripcion_tarea', 'minuta__proyecto__titulo_tesis')
    list_select_related = ('minuta', 'minuta__proyecto')

    @admin.display(description='Estado')
    def get_estado_acuerdo(self, obj):
        colores = {
            'CUMPLIDO': '#198754',
            'PENDIENTE': '#ffc107; color: #000',
            'CANCELADO': '#6c757d',
        }
        color = colores.get(obj.estado, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_estado_display()
        )


@admin.register(AlertaRezago)
class AlertaRezagoAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'dias_acumulados', 'fecha_deteccion', 'get_estado_alerta')
    list_filter = ('estado_alerta', 'fecha_deteccion')
    search_fields = ('proyecto__titulo_tesis',)
    list_select_related = ('proyecto',)

    @admin.display(description='Estado de Alerta')
    def get_estado_alerta(self, obj):
        color = '#dc3545' if obj.estado_alerta == 'Pendiente' else '#198754'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.estado_alerta
        )