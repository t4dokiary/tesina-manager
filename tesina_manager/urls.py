"""
URL configuration for tesina_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from seguimiento import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panel de administración de Django
    path('admin/', admin.site.urls),

    # Página principal / Landing
    path('', views.index, name='index'),

    # =========================================================================
    # AUTENTICACIÓN, REGISTRO Y PERFIL (CU01)
    # =========================================================================
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('registro/', views.registrar_alumno, name='registro_alumno'),
    path('registro-asesor/', views.registrar_asesor, name='registro_asesor'),
    path('mi-perfil/', views.editar_mi_perfil, name='mi_perfil'),

    # =========================================================================
    # ROL: ALUMNO (CU02, CU03)
    # =========================================================================
    path('alumno/dashboard/', views.alumno_dashboard, name='alumno_dashboard'),
    path('alumno/subir-protocolo/', views.alumno_subir_protocolo, name='subir_protocolo'),  # <-- RUTA FALTANTE
    path('alumno/subir-pdf/', views.alumno_entregas, name='alumno_entregas'),
    path('alumno/mis-acuerdos/', views.alumno_acuerdos, name='alumno_acuerdos'),

    # =========================================================================
    # ROL: ASESOR DOCENTE (CU02, CU03, CU04)
    # =========================================================================
    path('asesor/dashboard/', views.asesor_dashboard, name='asesor_dashboard'),
    path('asesor/revision/<int:proyecto_id>/', views.asesor_revision, name='asesor_revision'),
    path('asesor/minuta/<int:proyecto_id>/', views.asesor_minuta, name='asesor_minuta'),
    path('asesor/acuerdo/<int:id_acuerdo>/alternar/', views.alternar_cumplimiento_acuerdo, name='alternar_cumplimiento_acuerdo'),

    # =========================================================================
    # ROL: COORDINACIÓN DE POSGRADO (CU01, CU02, CU03, CU04)
    # =========================================================================
    path('coordinador/dashboard/', views.coordinador_dashboard, name='coordinador_dashboard'),
    
    # Gestión y validación de usuarios/asesores
    path('coordinador/activar-asesor/<int:id_perfil>/', views.activar_asesor, name='activar_asesor'),
    path('coordinador/rechazar-asesor/<int:id_perfil>/', views.rechazar_asesor, name='rechazar_asesor'),
    path('coordinador/editar-asesor/<int:id_perfil>/', views.coordinador_editar_asesor, name='coordinador_editar_asesor'),
    path('coordinador/editar-alumno/<int:id_perfil>/', views.coordinador_editar_alumno, name='coordinador_editar_alumno'),
    path('coordinador/nuevo-coordinador/', views.registrar_coordinador, name='registrar_coordinador'),
    path('coordinador/cambiar-rol/<int:id_perfil>/', views.cambiar_rol_usuario, name='cambiar_rol_usuario'),
    path('coordinador/alumno/<int:id_perfil>/expediente/', views.coordinador_ver_expediente, name='coordinador_ver_expediente'),

    # Convocatorias oficiales
    path('coordinador/convocatorias/', views.coordinador_convocatorias, name='coordinador_convocatorias'),
    path('coordinador/convocatorias/<int:id_convocatoria>/estado/<str:nuevo_estado>/', views.cambiar_estado_convocatoria, name='cambiar_estado_convocatoria'),

    # Protocolos y seguimiento de proyectos
    path('coordinador/validar-protocolos/', views.coordinador_validar_protocolos, name='coordinador_validar_protocolos'),
    path('coordinador/resolver-protocolo/<int:id_proyecto>/<str:accion>/', views.resolver_protocolo, name='resolver_protocolo'),
    path('coordinador/proyecto/<int:id_proyecto>/concluir/', views.finalizar_proyecto_tesis, name='finalizar_proyecto_tesis'),

    # Monitoreo preventivo de rezago (>30 días)
    path('coordinador/alertas/', views.coordinador_alertas, name='coordinador_alertas'),
    
    path('entregable/<int:id_entregable>/mensaje/', views.enviar_mensaje_entrega, name='enviar_mensaje_entrega'),
    
    path('asesor/acuerdo/<int:id_acuerdo>/alternar/', views.alternar_cumplimiento_acuerdo, name='alternar_cumplimiento_acuerdo'),
    path('asesor/minuta/<int:id_minuta>/reprogramar/', views.reprogramar_minuta, name='reprogramar_minuta'),
    path('alumno/minuta/<int:id_minuta>/firmar/', views.firmar_minuta_alumno, name='firmar_minuta_alumno'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)