"""
Rate limiting (Sprint 15 - Segurança).

Protege endpoints sensíveis a ataques de força bruta (ex.: login) contra
um volume alto de tentativas vindas do mesmo IP em pouco tempo.

Usa `slowapi` (baseado na lib `limits`), com armazenamento em memória do
próprio processo - suficiente para o Hellux hoje. Se no futuro o app
escalar para múltiplas instâncias/workers de forma que a imprecisão do
armazenamento em memória (cada worker com sua própria contagem) vire um
problema real, o `storage_uri` abaixo pode passar a apontar para um Redis
compartilhado sem precisar mudar quem usa o `limiter`.
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def obter_ip_cliente(request: Request) -> str:
    """
    Em produção, o backend roda atrás do proxy de borda do Fly.io (TLS
    terminado lá - ver `force_https` no fly.toml). Nesse cenário,
    `request.client.host` (usado por `get_remote_address` do slowapi)
    reflete o IP do proxy interno do Fly, não o do usuário real - o que
    faria o rate limit de login aplicar para TODOS os usuários juntos em
    vez de por pessoa (bug encontrado em revisão de segurança: um único
    visitante externo errando a senha 5 vezes travaria o login de todo
    mundo).

    O Fly injeta o IP real do cliente no header `Fly-Client-IP`. Fora do
    Fly (dev local, testes), esse header não existe, então cai para
    `X-Forwarded-For` (primeiro IP da cadeia) e, por fim, para
    `get_remote_address` como último recurso.
    """
    fly_client_ip = request.headers.get("Fly-Client-IP")
    if fly_client_ip:
        return fly_client_ip

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return get_remote_address(request)


limiter = Limiter(key_func=obter_ip_cliente)
