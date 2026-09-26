# Hellux

Sistema Inteligente de Gestão Microbiológica — plataforma web para gestão
da microbiologia hospitalar, do cadastro de pacientes à geração de
indicadores epidemiológicos e apoio à CCIH.

> Este repositório é o ponto de partida oficial do projeto, construído do
> zero seguindo o `Hellux_Documento_Mestre_Detalhado_v2.docx` e o guia
> de identidade visual do projeto. Ele contém a arquitetura completa e o
> primeiro módulo (**Pacientes**) 100% funcional, além do esqueleto pronto
> dos demais módulos para as próximas sprints.

## Stack

- **Frontend:** React + TypeScript + Vite
- **Backend:** FastAPI (arquitetura em camadas: Router → Service → Repository)
- **Banco:** PostgreSQL + SQLAlchemy + Alembic
- **Containerização:** Docker / docker-compose

## Estrutura do projeto

```
hellux/
├── backend/          # API FastAPI
│   ├── app/
│   │   ├── core/         # config, contrato de resposta, exceções
│   │   ├── db/           # conexão com o banco, tipos customizados
│   │   ├── models/       # entidades SQLAlchemy
│   │   ├── schemas/      # validação Pydantic (entrada/saída)
│   │   ├── repositories/ # acesso ao banco
│   │   ├── services/     # regras de negócio
│   │   ├── routers/      # endpoints HTTP
│   │   └── main.py
│   ├── alembic/          # migrações do banco
│   └── tests/            # testes automatizados (pytest)
├── frontend/          # SPA React
│   └── src/
│       ├── components/   # componentes reutilizáveis (Sidebar, Topbar, etc.)
│       ├── layouts/      # layout principal (shell da aplicação)
│       ├── pages/        # páginas de cada módulo
│       ├── services/     # cliente HTTP / chamadas à API
│       ├── styles/       # design tokens da identidade visual
│       └── types/        # tipos TypeScript
├── design/            # guia de identidade visual (fonte oficial das cores/tipografia)
├── docs/              # documentação do projeto (SRS, roadmap, etc.)
├── knowledge/          # base de conhecimento (microrganismos, antimicrobianos...)
├── infrastructure/    # scripts/configs de implantação
└── docker-compose.yml
```

## Como rodar localmente

### Opção 1 — Docker (recomendado)

Pré-requisito: Docker e Docker Compose instalados.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend (Swagger): http://localhost:8000/docs

O `docker-compose` já sobe o PostgreSQL, aplica as migrações do Alembic
automaticamente (`alembic upgrade head`) e inicia o backend e o frontend
com hot-reload.

### Opção 2 — Sem Docker

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Ajuste DATABASE_URL no .env para apontar para o seu PostgreSQL local
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Testes do backend

```bash
cd backend
pytest
```

## Módulos do sistema

| Módulo | Status | Sprint |
|---|---|---|
| Infraestrutura | ✅ Pronta | Sprint 1 |
| Pacientes | ✅ Implementado (CRUD completo) | Sprint 2 |
| Robustez da API (contrato padrão, validações, erros) | ✅ Implementado | Sprint 3 |
| Frontend de Pacientes | ✅ Implementado | Sprint 4 |
| Solicitações | ✅ Implementado (CRUD completo) | Sprint 5 |
| Microbiologia | ✅ Implementado (culturas + catálogo de microrganismos) | Sprint 6 |
| Antibiogramas | ✅ Implementado (catálogo + resultados S/I/R) | Sprint 7 |
| Dashboard | ✅ Implementado (indicadores reais + alertas) | Sprint 8 |
| CCIH | ✅ Implementado (indicadores + perfil de resistência) | Sprint 9 |
| Relatórios | ✅ Implementado (Excel + PDF da CCIH) | Sprint 10 |
| Configurações | ✅ Implementado (usuários, parâmetros, catálogos de microrganismos/antimicrobianos/setores/materiais, auditoria) | Sprint 11 |
| Autenticação (JWT) | ✅ Implementado (login, bootstrap do 1º admin, RBAC por perfil) | Sprint 12 |
| Auditoria | ✅ Implementado (middleware transversal + consulta de logs) | Sprint 13 |
| Painel de Acompanhamento + novo layout visual | ✅ Implementado (culturas por mês/ano, linha colorida por status, filtros por coluna) | Sprint 15 |
| Preparação para produção | ✅ Módulos clínicos travados com autenticação; Docker/infra prontos | Sprint 14 |

## Autenticação e segurança - estado atual

O módulo de Autenticação (JWT) está implementado e funcional:

- `POST /api/usuarios` — cadastra um usuário. **O primeiro usuário criado no
  sistema vira ADMIN automaticamente** (bootstrap). A partir do segundo
  usuário, esse endpoint exige um token de ADMIN.
- `POST /api/auth/login` — recebe `username`/`password` (form, padrão OAuth2)
  e devolve um `access_token` JWT.
- `GET /api/auth/me` — retorna os dados do usuário autenticado.
- `GET/PUT/DELETE /api/usuarios` — restritos a ADMIN.

**✅ Todos os módulos clínicos exigem login** (`Depends(get_current_user)` a
nível de router): Pacientes, Solicitações, Microrganismos, Microbiologia,
Antimicrobianos, Antibiogramas, Dashboard, CCIH e Relatórios. Qualquer
requisição sem um token JWT válido recebe `401 Unauthorized` - inclusive
pelo Swagger (`/docs`, usar o botão "Authorize") ou por `curl`/Postman.

Ficam abertos, por design: `GET /api/health` (usado pelo healthcheck do
Docker) e `POST /api/auth/login` (obviamente, precisa ser acessível antes
do login). `POST /api/usuarios` também fica aberto **apenas enquanto não
existir nenhum usuário no sistema** (bootstrap do primeiro ADMIN).

Os testes automatizados usam a fixture `authenticated_client` (ver
`tests/conftest.py`) para os módulos clínicos, e há uma bateria dedicada
em `tests/test_autenticacao_modulos_clinicos.py` confirmando que cada
endpoint protegido responde `401` sem token e funciona normalmente com um
token válido.

### Como usar o login pela primeira vez

```bash
# 1. Cria o primeiro usuário (vira ADMIN automaticamente)
curl -X POST http://localhost:8000/api/usuarios \
  -H "Content-Type: application/json" \
  -d '{"nome": "Seu Nome", "email": "voce@hospital.com", "senha": "senha-forte-aqui", "perfil": "ADMIN"}'

# 2. Faz login
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=voce@hospital.com&password=senha-forte-aqui"

# 3. Usa o token nas próximas requisições
curl http://localhost:8000/api/pacientes \
  -H "Authorization: Bearer <access_token retornado no passo 2>"
```

No frontend, acesse `http://localhost:5173/login` com o mesmo e-mail/senha
- o token é anexado automaticamente em toda requisição a partir daí.

## Preparação para Produção (Sprint 14)

Itens já resolvidos:

- ✅ Dockerfiles de produção separados (`Dockerfile.prod` no backend e no
  frontend) - sem hot-reload, sem bind-mounts de código, backend rodando
  como usuário não-root, frontend servido como estático via Nginx.
- ✅ `docker-compose.prod.yml` dedicado (não reutiliza o de desenvolvimento).
- ✅ Backend recusa iniciar com `ENVIRONMENT=production` se `SECRET_KEY`
  ainda estiver com o valor padrão do repositório.
- ✅ Headers de segurança HTTP (`X-Frame-Options`, `X-Content-Type-Options`,
  `Referrer-Policy`, `Permissions-Policy`) em toda resposta.
- ✅ Healthchecks configurados para banco, backend e frontend.
- ✅ `.dockerignore` em backend e frontend (evita vazar `.env`/`.git` para
  dentro da imagem).

Checklist antes de ir para produção com dados reais de pacientes:

1. ~~Fechar os endpoints clínicos com autenticação.~~ ✅ Feito - todos os
   módulos clínicos exigem login (ver seção "Autenticação e segurança"
   acima). Considere também restringir ações específicas por perfil (ex.:
   só ADMIN/BIOMEDICO libera cultura) usando `Depends(require_perfil(...))`
   se fizer sentido para o fluxo do laboratório.
2. Gere uma `SECRET_KEY` forte e única (`openssl rand -hex 32`) e uma senha
   forte para `POSTGRES_PASSWORD` - nunca reutilize os valores de exemplo.
3. Ajuste `CORS_ORIGINS` para o(s) domínio(s) reais do frontend em produção.
4. Configure backups automáticos do PostgreSQL (o volume Docker sozinho não
   é backup).
5. Sirva o backend atrás de HTTPS (reverse proxy como Nginx/Traefik com
   Let's Encrypt, ou terminação TLS no balanceador, conforme o ambiente).
6. Revise `ACCESS_TOKEN_EXPIRE_MINUTES` conforme a política de sessão
   desejada pelo hospital.
7. Rode `pytest` (backend) e valide manualmente o fluxo completo no
   ambiente de destino antes do primeiro uso real.

## Como implementar um novo módulo

Todo módulo novo segue exatamente o padrão usado em **Pacientes** — copie
esse fluxo:

1. **Model** (`backend/app/models/<entidade>.py`) — define a tabela.
2. Registrar o model em `backend/app/models/__init__.py`.
3. **Migração** — gerar com `alembic revision --autogenerate -m "cria tabela X"`
   (ou escrever manualmente, como em `alembic/versions/0001_create_pacientes.py`).
4. **Schema** (`backend/app/schemas/<entidade>.py`) — validação de entrada/saída.
5. **Repository** (`backend/app/repositories/<entidade>_repository.py`) — herda de `BaseRepository`.
6. **Service** (`backend/app/services/<entidade>_service.py`) — regras de negócio.
7. **Router** (`backend/app/routers/<entidade>_router.py`) — endpoints HTTP, sempre retornando `success_response`/`error_response`.
8. Registrar o router em `backend/app/main.py`.
9. **Frontend:** tipos em `src/types/`, service em `src/services/`, páginas em `src/pages/`, rota em `src/App.tsx`.
10. **Testes** em `backend/tests/test_<modulo>.py`.

## Identidade visual

Todas as cores e a tipografia (Poppins) usadas no frontend vêm do guia
oficial de identidade visual — ver `design/IDENTIDADE_VISUAL.md` e
`frontend/src/styles/tokens.css`. Nunca usar cores "hardcoded" fora
desses arquivos.

## Documentação de referência

- `docs/Hellux_Documento_Mestre_Detalhado_v2.docx` — documento mestre de planejamento.
- `design/IDENTIDADE_VISUAL.md` — identidade visual oficial.

## Licença / propriedade do código

Conforme decisão registrada nas conversas de planejamento do projeto, o
código-fonte permanece de propriedade do autor. Não incluir este
repositório em entregas de "sistema compilado" para terceiros sem
avaliar antes o modelo de licenciamento adequado.
