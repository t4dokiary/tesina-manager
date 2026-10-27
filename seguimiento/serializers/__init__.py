from .usuarios import PerfilUsuarioSerializer, AlumnoSerializer
from .convocatorias import ConvocatoriaSerializer
from .proyectos import ProyectoTesisSerializer
from .entregables import EntregableVersionSerializer
from .minutas import MinutaSerializer, CompromisoSerializer
from .alertas import AlertaRezagoSerializer

__all__ = [
    'PerfilUsuarioSerializer',
    'AlumnoSerializer',
    'ConvocatoriaSerializer',
    'ProyectoTesisSerializer',
    'EntregableVersionSerializer',
    'MinutaSerializer',
    'CompromisoSerializer',
    'AlertaRezagoSerializer',
]