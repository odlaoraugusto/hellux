"""
Registro central de todos os models do Hellux.

Importar todos os models aqui garante que o Alembic (autogenerate) e o
SQLAlchemy metadata os enxerguem corretamente.

À medida que novos módulos forem implementados (Solicitações,
Microbiologia, Antibiogramas, CCIH, etc.), seus models devem ser
importados neste arquivo.
"""
from app.models.paciente import Paciente  # noqa: F401
from app.models.solicitacao import Solicitacao  # noqa: F401
from app.models.microrganismo import Microrganismo  # noqa: F401
from app.models.cultura import Cultura, CulturaMicrorganismo  # noqa: F401
from app.models.antimicrobiano import Antimicrobiano  # noqa: F401
from app.models.antibiograma import Antibiograma, AntibiogramaResultado  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.parametro_sistema import ParametroSistema  # noqa: F401
from app.models.log_auditoria import LogAuditoria  # noqa: F401
from app.models.setor import Setor  # noqa: F401
from app.models.material import Material  # noqa: F401

__all__ = [
    "Paciente",
    "Solicitacao",
    "Microrganismo",
    "Cultura",
    "CulturaMicrorganismo",
    "Antimicrobiano",
    "Antibiograma",
    "AntibiogramaResultado",
    "Usuario",
    "ParametroSistema",
    "LogAuditoria",
    "Setor",
    "Material",
]
