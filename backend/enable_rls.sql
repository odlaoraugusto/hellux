-- ============================================================
-- ATENÇÃO (Fase 1 - fundação multi-tenant): este arquivo é anterior à
-- introdução de tenant_id/RLS "de verdade" (isolamento por tenant, ver
-- alembic/versions/0014_multi_tenant_exame.py). Ele continua aqui só
-- pelo propósito histórico original descrito abaixo (bloquear a API
-- REST automática do Supabase) - NÃO reflete mais o schema atual (não
-- cobre tenants/exames/tipos_cultura, e as tabelas antigas de
-- solicitacoes/culturas/antibiogramas que ele lista já não existem mais).
-- Não rodar isso como substituto da migration 0014.
-- ============================================================
--
-- Hellux — Habilita Row Level Security em todas as tabelas
--
-- O backend conecta direto no Postgres via SQLAlchemy (não usa o
-- Supabase Auth nem o client-side), então RLS aqui não serve pra
-- controlar quem acessa via app — serve pra FECHAR a API REST
-- pública do Supabase (PostgREST), que fica aberta por padrão pra
-- qualquer tabela sem RLS usando a chave "anon" (pública).
--
-- Sem nenhuma policy criada, RLS ligado = a API REST nega tudo
-- por padrão pros roles anon/authenticated. A conexão direta do
-- backend (role postgres/superuser) não é afetada.
--
-- Rode isso no SQL Editor do painel do Supabase do projeto hellux.
-- ============================================================

alter table pacientes enable row level security;
alter table usuarios enable row level security;
alter table culturas enable row level security;
alter table cultura_microrganismos enable row level security;
alter table microrganismos enable row level security;
alter table antibiogramas enable row level security;
alter table antibiograma_resultados enable row level security;
alter table antimicrobianos enable row level security;
alter table materiais enable row level security;
alter table setores enable row level security;
alter table solicitacoes enable row level security;
alter table parametros_sistema enable row level security;
alter table logs_auditoria enable row level security;
