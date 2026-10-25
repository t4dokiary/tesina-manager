from .generales import (
    calcular_tiempo_restante,
    index,
    iniciar_sesion,
    cerrar_sesion,
    redirigir_por_rol,
    editar_mi_perfil,
)

from .coordinador import (
    coordinador_dashboard,
    activar_asesor,
    rechazar_asesor,
    coordinador_editar_asesor,
    coordinador_editar_alumno,
    registrar_coordinador,
    cambiar_rol_usuario,
    coordinador_convocatorias,
    cambiar_estado_convocatoria,
    coordinador_validar_protocolos,
    resolver_protocolo,
    coordinador_alertas,
    finalizar_proyecto_tesis,
    coordinador_ver_expediente,
)

from .alumno import (
    registrar_alumno,
    alumno_dashboard,
    alumno_subir_protocolo,
    alumno_entregas,
    alumno_acuerdos,
    enviar_mensaje_entrega,
    firmar_minuta_alumno,
)

from .asesor import (
    registrar_asesor,
    asesor_dashboard,
    asesor_revision,
    asesor_minuta,
    alternar_cumplimiento_acuerdo,
    reprogramar_minuta
)