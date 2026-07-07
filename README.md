# fabio-backup

Repositório de backup do **Fábio** — agente pedagógico da LA Music.

Fábio roda em **Hermes** (Nous Research) na VPS LAHQ, opera via Telegram/WhatsApp, e é o coração do sistema pedagógico agent-first da LA Music.

## Equação de valor

> **Cuidado + Evolução**

Cuidado com cada indivíduo (o aluno na sua jornada, o professor na sua rotina). Evolução como o norte de tudo.

## Estrutura deste repositório

| Arquivo | O que é |
|---|---|
| `SOUL.md` | A alma do Fábio — identidade, valores, tom |
| `AGENTS.md` | Comportamento operacional, frentes, fases |
| `PERMISSOES.md` | Permissões, guardrails e fronteiras |
| `skills/` | Skills oficiais e versionadas do Fábio |
| `docs/` | PRD, escopo e mapa de fontes canônicas do LA Report |

## Skills

- **briefing-pedagogico-la-music** — produz briefing pedagógico de turma/professor/aluno a partir dos dados do LA Report (`aulas_emusys.anotacoes`), lendo a evolução, não uma lista crua de aulas.
- **registro-aula-audio-la-music** — normaliza registros de aula por áudio/texto na Alma v1.1 do Fábio, separando tronco comum da turma e fatias nominais por aluno sem inventar campos.

## Notas de segurança

Este repositório NÃO contém segredos. Credenciais (`.env`, tokens, `auth.json`), sessões e logs ficam apenas na VPS e estão bloqueados pelo `.gitignore`.

## Bússola

> Tecnologia como ponte, não como camada fria.
