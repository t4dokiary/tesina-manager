"""
URL configuration for tesina_manager project.
Estructurado por Casos de Uso (CU01 a CU04) y Roles de Usuario.
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from seguimiento import views

urlpatterns = [
    # =========================================================================
    # ADMINISTRACIÓN GENERAL Y LANDING
    # =========================================================================
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),

    # =========================================================================
    # CU01: AUTENTICACIÓN, REGISTRO Y PERFIL
    # =========================================================================
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('registro/', views.registrar_alumno, name='registro_alumno'),
    path('registro-asesor/', views.registrar_asesor, name='registro_asesor'),
    path('mi-perfil/', views.editar_mi_perfil, name='mi_perfil'),

    # =========================================================================
    # CU02 & CU03: ROL ALUMNO
    # =========================================================================
    path('alumno/dashboard/', views.alumno_dashboard, name='alumno_dashboard'),
    path('alumno/subir-protocolo/', views.alumno_subir_protocolo, name='subir_protocolo'),
    path('alumno/subir-pdf/', views.alumno_entregas, name='alumno_entregas'),
    path('alumno/mis-acuerdos/', views.alumno_acuerdos, name='alumno_acuerdos'),
    path('alumno/minuta/<int:id_minuta>/firmar/', views.firmar_minuta_alumno, name='firmar_minuta_alumno'),

    # =========================================================================
    # CU02, CU03 & CU04: ROL ASESOR DOCENTE
    # =========================================================================
    path('asesor/dashboard/', views.asesor_dashboard, name='asesor_dashboard'),
    path('asesor/revision/<int:proyecto_id>/', views.asesor_revision, name='asesor_revision'),
    path('asesor/minuta/<int:proyecto_id>/', views.asesor_minuta, name='asesor_minuta'),
    path('asesor/minuta/<int:id_minuta>/reprogramar/', views.reprogramar_minuta, name='reprogramar_minuta'),
    path('asesor/acuerdo/<int:id_acuerdo>/alternar/', views.alternar_cumplimiento_acuerdo, name='alternar_cumplimiento_acuerdo'),

    # =========================================================================
    # CU01 A CU04: ROL COORDINACIÓN DE POSGRADO
    # =========================================================================
    path('coordinador/dashboard/', views.coordinador_dashboard, name='coordinador_dashboard'),

    # Gestión de usuarios y cuentas
    path('coordinador/activar-asesor/<int:id_perfil>/', views.activar_asesor, name='activar_asesor'),
    path('coordinador/rechazar-asesor/<int:id_perfil>/', views.rechazar_asesor, name='rechazar_asesor'),
    path('coordinador/editar-asesor/<int:id_perfil>/', views.coordinador_editar_asesor, name='coordinador_editar_asesor'),
    path('coordinador/editar-alumno/<int:id_perfil>/', views.coordinador_editar_alumno, name='coordinador_editar_alumno'),
    path('coordinador/nuevo-coordinador/', views.registrar_coordinador, name='registrar_coordinador'),
    path('coordinador/cambiar-rol/<int:id_perfil>/', views.cambiar_rol_usuario, name='cambiar_rol_usuario'),

    # Expediente y dictamen de proyectos
    path('coordinador/alumno/<int:id_perfil>/expediente/', views.coordinador_ver_expediente, name='coordinador_ver_expediente'),
    path('coordinador/validar-protocolos/', views.coordinador_validar_protocolos, name='coordinador_validar_protocolos'),
    path('coordinador/resolver-protocolo/<int:id_proyecto>/<str:accion>/', views.resolver_protocolo, name='resolver_protocolo'),
    path('coordinador/proyecto/<int:id_proyecto>/concluir/', views.finalizar_proyecto_tesis, name='finalizar_proyecto_tesis'),

    # Convocatorias oficiales
    path('coordinador/convocatorias/', views.coordinador_convocatorias, name='coordinador_convocatorias'),
    path('coordinador/convocatorias/<int:id_convocatoria>/estado/<str:nuevo_estado>/', views.cambiar_estado_convocatoria, name='cambiar_estado_convocatoria'),

    # Monitoreo preventivo (>30 días)
    path('coordinador/alertas/', views.coordinador_alertas, name='coordinador_alertas'),

    # =========================================================================
    # COMUNICACIÓN Y RETROALIMENTACIÓN DE ENTREGAS
    # =========================================================================
    path('entregable/<int:id_entregable>/mensaje/', views.enviar_mensaje_entrega, name='enviar_mensaje_entrega'),
]

# Servir archivos PDF y multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)