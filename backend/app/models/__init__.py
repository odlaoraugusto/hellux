"""
Registro central de todos os models do Hellux.

Importar todos os models aqui garante que o Alembic (autogenerate) e o
SQLAlchemy metadata os enxerguem corretamente.

À medida que novos módulos forem implementados, seus models devem ser
importados neste arquivo.
"""
from app.models.tenant import Tenant  # noqa: F401
from app.models.paciente import Paciente  # noqa: F401
from app.models.microrganismo import Microrganismo  # noqa: F401
from app.models.antimicrobiano import Antimicrobiano  # noqa: F401
from app.models.usuario import Usuario  # noqa: F401
from app.models.parametro_sistema import ParametroSistema  # noqa: F401
from app.models.log_auditoria import LogAuditoria  # noqa: F401
from app.models.setor import Setor  # noqa: F401
from app.models.material import Material  # noqa: F401
from app.models.tipo_cultura import TipoCultura  # noqa: F401
from app.models.exame import Exame, ExameAntibiograma, ExameIsolado  # noqa: F401

__all__ = [
    "Tenant",
    "Paciente",
    "Microrganismo",
    "Antimicrobiano",
    "Usuario",
    "ParametroSistema",
    "LogAuditoria",
    "Setor",
    "Material",
    "TipoCultura",
    "Exame",
    "ExameIsolado",
    "ExameAntibiograma",
]
