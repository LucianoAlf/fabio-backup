# Arquitetura de Escrita do Fábio — Fase 2 (registro de aula)

> Como o Fábio passou a **ler e escrever** no LA Report com segurança fina (modelo "crachá"),
> substituindo o acesso anterior (MCP oficial do Supabase em `--read-only` via PAT).
> Banco: **LA Report** (Supabase, projeto `ouqwbbermlzqqvtqwlul`).
> Data desta construção: 23–24/06/2026.

---

## 1. O problema que isso resolve

O Fábio precisa de duas coisas no LA Report que o acesso antigo não dava ao mesmo tempo:

1. **Ler** dados pedagógicos (aulas, presenças, alunos) — para briefings, continuidade etc.
2. **Escrever** o registro de aula por áudio (Fase 2) — mas **sem** poder fazer estrago.

O acesso antigo era o MCP oficial do Supabase com `--read-only` + um Personal Access Token (PAT).
Isso é um liga/desliga grosseiro: ou lê tudo travado, ou (sem a flag) escreve com o poder amplo do PAT.
Nenhum dos dois serve para "lê amplo, escreve só na porta certa".

**Decisão (validada com o Alfredo):** escrita do Fábio **somente via RPC dedicada**, nunca por UPDATE livre.
A segurança não fica numa regra de aplicação (contornável), fica no **próprio banco**.

---

## 2. As 4 peças no banco

### 2.1. Coluna `aulas_emusys.anotacoes_fabio` (text)
Onde o Fábio grava o registro de aula. **Separada** da coluna `anotacoes` (território do sync do Emusys).

**Por quê separada:** a Edge Function `sync-presenca-emusys` roda diária (22h BRT) e faz UPSERT em
`aulas_emusys` incluindo `anotacoes` no payload. Se o Fábio gravasse em `anotacoes`, o sync
**sobrescreveria** com o valor do Emusys (provavelmente null) em até 24h. O sync **nunca** toca
`anotacoes_fabio` → zero sobrescrita. As duas colunas convivem; alimentam o LA Report em paralelo.

### 2.2. Tabela `aula_registros_fabio_log` (audit log)
Trilha de auditoria de toda gravação do Fábio: `aula_id`, `professor_id`, `texto_anterior`,
`texto_novo`, `origem` (audio/texto), `modo` (novo/substituir/complementar), `criado_em`.
**RLS habilitado sem políticas públicas** — acesso só via a função (SECURITY DEFINER) e service_role.

### 2.3. RPC `registrar_aula_fabio(...)` — a porta estreita
Assinatura: `registrar_aula_fabio(p_aula_id int, p_texto text, p_origem text='audio', p_professor_id int=null, p_modo text='novo')` retorna `jsonb`.

- **SECURITY DEFINER**: roda com privilégios da função, então o chamador (Fábio) **não precisa** (e não tem) UPDATE na tabela.
- **REVOKE de PUBLIC**: ninguém executa por padrão; só quem recebe GRANT EXECUTE (o crachá).
- **Só toca `anotacoes_fabio`** — nunca `anotacoes`.
- **Validações**: texto não-vazio; origem em {audio,texto}; modo em {novo,substituir,complementar}; aula deve existir.
- **Idempotência**: texto idêntico ao já gravado retorna `sem_mudanca`, não regrava nem polui o log.
- **Modos**: `novo`/`substituir` gravam o texto; `complementar` concatena ao anterior com separador.
- **Audit log**: toda gravação efetiva insere uma linha em `aula_registros_fabio_log`.

### 2.4. Role `fabio_agent` — o crachá
Role dedicado do Postgres = a identidade do Fábio no banco.

- `LOGIN` com senha forte (**a senha vive no `.env`/config do Hermes; não consta deste repo**).
- `BYPASSRLS = true`: visão global (lê todas as unidades/alunos, ignorando RLS) — coerente com o papel administrativo do Fábio. Sem isso, a maioria das ~180 tabelas com RLS retornaria 0 linhas.
- **Leitura ampla**: `GRANT SELECT ON ALL TABLES IN SCHEMA public` + default privileges para tabelas/views futuras (não algemar a evolução).
- **Ação restrita**: `GRANT EXECUTE` apenas na RPC `registrar_aula_fabio`. **Nenhum** UPDATE/INSERT/DELETE direto.
- **Não** é superuser, **não** cria DB, **não** cria role.

**Regra do crachá:** entra para ver onde quiser (ler não destrói), mas só age pelas portas-RPC certas.

> Detalhe benigno conhecido: durante os testes, `GRANT fabio_agent TO postgres` ficou registrado
> (grantor = `supabase_admin`), e o `postgres` do Supabase não consegue revogar algo concedido por
> `supabase_admin`. É inofensivo (postgres já é mais poderoso que o crachá; o inverso não ocorre).
> Limpável pelo painel do Supabase com um role mais alto, se desejado.

---

## 3. A conexão (como o Fábio fala com o banco)

O MCP oficial do Supabase usa o PAT (privilégios da conta, não um role). Para o crachá entrar em ação,
o Fábio passou a conectar **direto no Postgres como `fabio_agent`** via um MCP Postgres genérico.

- **MCP escolhido**: `crystaldba/postgres-mcp` (Postgres MCP Pro). Motivo: read/write configurável e roda no Python 3.12 que a VPS já tem. (O `bytebase/dbhub` foi descartado por exigir Node >= 22.5; a VPS tem Node 20, e não se mexe no Node global por causa dos outros agentes.)
- **Instalação**: `uv` (em `/home/fabio/.local/bin/uv`) + `uv tool install postgres-mcp` cria o executável em `/home/fabio/.local/bin/postgres-mcp`. Usa Python 3.12. Não toca no ambiente dos outros agentes.
- **Acesso**: `--access-mode=unrestricted` no MCP. A segurança **não** vem do MCP e sim do **crachá** (que já recusa escrita direta). Unrestricted é necessário só para a RPC (escrita) funcionar.
- **Rede**: conexão pelo **pooler** (Supavisor) em `aws-1-sa-east-1.pooler.supabase.com:5432` — IPv4 (a conexão direta do Supabase é IPv6-only e a VPS não tem IPv6). User no pooler: `fabio_agent.ouqwbbermlzqqvtqwlul`. `sslmode=require`.

### Config no Hermes (`~/.hermes/config.yaml`, seção `mcp_servers`)
O bloco `lareport` foi trocado de `@supabase/mcp-server-supabase` (PAT + `--read-only`) para:

    mcp_servers:
      lareport:
        command: "/home/fabio/.local/bin/postgres-mcp"
        args:
          - "--access-mode=unrestricted"
        env:
          DATABASE_URI: "postgresql://fabio_agent.ouqwbbermlzqqvtqwlul:<SENHA_NO_ENV>@aws-1-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
        enabled: true
        timeout: 120
        connect_timeout: 60

> **Bônus de segurança:** com essa troca, o PAT do Supabase **deixou de ser usado pelo Fábio** — ele
> some do caminho. O Fábio entra pelo crachá. (O `.gitignore` deste repo protege `.env`/`config.yaml`/tokens.)

### Como o Fábio roda (para reiniciar)
Serviço **systemd de sistema**: `hermes-gateway.service` (processo `python -m hermes_cli.main gateway run`).
Restart (como root, que é o login padrão do `ssh lahq`): `systemctl restart hermes-gateway.service`.

---

## 4. Testes realizados (todos OK)

**No banco (via SET ROLE / SQL), com a aula real 145188 (revertida ao fim):**
- Gravação nova; isolamento (`anotacoes` do Emusys intocado, só `anotacoes_fabio` mudou).
- Idempotência (texto igual = `sem_mudanca`, não loga).
- Complementar (concatena) e substituir (troca, anterior preservado no log).
- Audit log correto; guarda de erro (aula inexistente = exceção controlada).
- Crachá: lê 31.763 aulas; UPDATE direto = `permission denied` (bloqueado); RPC = funciona.

**Conexão ponta a ponta (psycopg pelo pooler):** conecta como `fabio_agent`, lê, escrita direta bloqueada (`InsufficientPrivilege`).

**Em produção (Telegram, leitura real):** briefing pedagógico completo da turma V_Sá_15 (Violão Barra, prof. Isaque), 5 chamadas `execute_sql` pelo crachá, cruzando `aulas_emusys` + `aluno_presenca` + `alunos`. Guardas da alma respeitadas (não cravou causa do health score crítico; sinalizou para coordenação).

---

## 5. Pendências (próximos passos)

1. **Skill v1.1 de registro de aula por áudio** — instalar no Fábio (`~/.hermes/skills/...`). A leitura está provada; falta ligar a **escrita** (professor manda áudio, Fábio normaliza no formato da tese do Quintela, confirma, grava via RPC).
2. **Piloto com 1 professor** depois da skill instalada.
3. Infra de transcrição já existe e é reutilizável: Edge Function `transcrever-audio` (UAZAPI `/message/download` com `transcribe:true`).

---

## 6. Princípio que ficou

A exigência do Alfredo — "escrita só via RPC, nunca permissão aberta" — está cumprida na camada mais
sólida possível: **o banco recusa qualquer escrita do Fábio fora da porta certa**. Não é regra de
aplicação (contornável por bug ou alucinação); é permissão de role no Postgres.