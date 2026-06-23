# 📐 PRD — SISTEMA PEDAGÓGICO AGENT-FIRST
## Fábio (agente) + App do Professor | LA Music

> **Versão:** 1.0 · junho/2026
> **Autor:** Alf (Luciano) · Apoio: Claude + Alfredo
> **Natureza:** Sistema pedagógico agent-first — o agente (Fábio) ganha vida primeiro; o app é a casa que vem servi-lo
> **Runtime do agente:** Hermes (a instalar) · VPS LAHQ
> **Documento-irmão:** `fabio-escopo-completo.md` (escopo das 11 frentes)

---

## 1. Visão do Produto

A LA Music está construindo um **sistema pedagógico agent-first**, onde um agente de IA (Fábio) é o coração que captura, organiza e devolve continuidade pedagógica — e um aplicativo (App do Professor) é a casa que serve esse agente.

A filosofia é a mesma da Maria: **o agente nasce primeiro e ganha vida com os dados que já existem; o sistema (app) vem depois, como ferramenta a serviço do agente.** O dashboard/app não é o produto — o Fábio é. O app existe pra potencializar o Fábio e dar interface visual ao professor.

### Princípio agent-first
```
O agente (Fábio) é o cérebro e o trabalhador.
O app (App do Professor) é a casa e a interface.
Primeiro dá vida ao agente, depois constrói a casa.
```

### A simetria com o ecossistema LAHQ
| Agente | Sistema (casa) | Público |
|---|---|---|
| Maria | Super Folha | Financeiro (Rose, Ana) |
| Tom | LA Organizer | Staff/back-office |
| **Fábio** | **App do Professor** | **Professores + Coordenação** |

O App do Professor reaproveita a base do **LA Organizer** (o app de governança e organização do staff onde o Tom mora), adaptado pro contexto pedagógico.

---

## 2. As 3 Camadas do Fábio

| Camada | O que é | Quando |
|---|---|---|
| 🎓 **1. Agente pedagógico** | Jornada do aluno, registro de aula, briefing do professor, relatórios pedagógicos | Fase 1 |
| 📅 **2. Organizador do professor** | Agenda da LA, recitais/eventos, avaliações, pendências, lembretes; futuro: agenda pessoal | Fase 1-3 |
| 📱 **3. App do Professor** | A casa do Fábio. Absorve o app do Emusys, lança conteúdo por áudio, mostra histórico, alunos, tarefas, agenda, alertas | Fase 3+ |

---

## 3. Arquitetura de Dados (fontes de verdade)

### Decisão final: o LA Report é o hub central
**O Fábio NÃO opera diretamente dentro do Emusys.** O endpoint novo do Emusys já traz os dados necessários pro LA Report. Portanto, o LA Report é o hub central e a fonte/destino operacional do Fábio.

O Emusys alimenta o LA Report via endpoint/API. O Fábio trabalha sobre o LA Report e sobre o App do Professor, sem depender do app do Emusys.

```
Emusys ──(endpoint/API)──> LA Report <──(lê/escreve)── FÁBIO
                                │                         │
LA Journey ──(lê: jornada)──────┤                         │
                                │              App do Professor (a casa)
                                └─────────────────────────┘
```

### Os sistemas que o Fábio consome
| Sistema | Papel | Acesso do Fábio |
|---|---|---|
| **LA Report** | Hub central — fonte e destino operacional. Conteúdos de aula, indicadores, health score, histórico | Lê e escreve (MCP) |
| **LA Journey** | Jornada do aluno, checkpoints, marcos, base curada, materiais | Lê (MCP) |
| **App do Professor** | A casa do Fábio (a criar) | Lê e escreve |
| **Emusys** | Apenas fonte: alimenta o LA Report via endpoint/API. O Fábio NÃO opera dentro dele | Indireto (via LA Report) |

> **Visão de futuro:** o App do Professor substitui a experiência atual do app do Emusys para os professores. O Fábio é a inteligência que torna isso possível.

---

## 4. FASES E SPRINTS

### 🔧 FASE 0 — FUNDAÇÃO
*Objetivo: preparar o terreno pro Fábio existir*

#### Sprint 0.1 — Preparar o runtime (Hermes)
- Instalar Hermes na VPS LAHQ como infraestrutura (usuário `fabio` próprio, sem sudo)
- Configurar serviço isolado (porta própria, loopback)
- Autenticar modelo (mesmo Codex/GPT-5.5 dos outros agentes)
- Telegram próprio do Fábio (allowlist inicial)
- **Importante:** aqui só se prepara o runtime. O Fábio NÃO é instalado vivo antes da alma (SOUL/AGENTS/PERMISSOES) — isso é Fase 1
- **Pronto quando:** Hermes rodando como infraestrutura, pronto pra receber a alma do Fábio

#### Sprint 0.2 — Conexão dos MCPs
- Plugar MCP do LA Report (leitura + escrita) — hub central
- Plugar MCP do LA Journey (leitura)
- Confirmar que o endpoint do Emusys está alimentando o LA Report corretamente
- **Pronto quando:** Fábio consulta dados reais do LA Report e LA Journey, com o Emusys alimentando o LA Report via endpoint

#### Sprint 0.3 — Normalização das regras de negócio
- Documentar as regras de negócio dos 3 sistemas (base pras skills)
- Ex: o que é "aluno ativo", "aluno pagante", health score do professor, marcos da jornada
- Padronizar vocabulário pedagógico (igual fizemos no LA Report: alunos pagantes ≠ count bruto)
- **Pronto quando:** documento de regras de negócio pedagógicas validado, pronto pra virar skills

---

### 🎓 FASE 1 — O AGENTE GANHA VIDA
*Objetivo: Fábio consome dados e já serve o professor com o que existe hoje*

#### Sprint 1.1 — Alma do Fábio
- Escrever SOUL.md (personalidade, Cuidado + Evolução, tom)
- Escrever AGENTS.md (11 frentes, 3 camadas, regras operacionais)
- Escrever PERMISSOES.md (o que faz, o que escala, guardrails)
- Instalar no Hermes
- Smoke test de identidade e guardrails
- **Pronto quando:** Fábio sabe quem é, responde no tom certo, respeita guardrails (não diagnostica, não expõe inclusão, não rotula professor)

#### Sprint 1.2 — Primeiras skills (consultas que já dão valor)
- Skill: dia da aula / alunos do dia
- Skill: aluno faltando (frequência)
- Skill: briefing diário do professor
- Skill: histórico/jornada do aluno (do que já existe no LA Report + LA Journey)
- **Pronto quando:** Fábio entrega briefing real pra um professor-piloto

#### Sprint 1.3 — Relatório da coordenação
- Skill: relatório mensal pedagógico automatizado (o que hoje é feito na mão)
- Health score pedagógico do professor
- **Pronto quando:** Fábio gera o relatório da coordenação que o Quintela/Juliana fazem na mão

---

### 🎤 FASE 2 — REGISTRO POR ÁUDIO (o MVP que o Quintela cravou)
*Objetivo: o recurso mais valioso — professor registra aula por voz*

#### Sprint 2.1 — Captura e transcrição
- Receber áudio do professor via WhatsApp (UAZAPI)
- Transcrição do áudio (igual o Tom já entende áudios)
- **Pronto quando:** Fábio transcreve corretamente o áudio do professor

#### Sprint 2.2 — Normalização
- Transformar a transcrição crua no padrão de relatório da LA Music
- Identificar: música/repertório ensinado, tarefa de casa, técnica trabalhada
- **Pronto quando:** a normalização preserva o sentido e segue o padrão

#### Sprint 2.3 — Confirmação e gravação
- Professor confirma/edita quando houver ambiguidade
- Grava no LA Report, que centraliza e espelha os dados necessários vindos do endpoint do Emusys
- Áudio + transcrição como evidência/auditoria
- **Pronto quando:** o ciclo completo funciona (áudio → normaliza → confirma → grava no LA Report)

#### Sprint 2.4 — Revisitação
- Skill: briefing pré-aula com o histórico ("na última aula com Fulano você deu X")
- Acompanhamento da tarefa de casa
- **Pronto quando:** antes da aula, o Fábio lembra o professor do que foi dado

---

### 🤝 FASE 3 — INTEGRAÇÃO ENTRE AGENTES
*Objetivo: o Fábio conversa com os outros agentes*

#### Sprint 3.1 — Handoff da experimental (Mila → Fábio → professor)
- Receber da Mila o interesse do aluno (gosto musical, se já tocou, instrumento, objetivo)
- Entregar briefing rico pro professor antes da experimental
- Sinalização sensível do núcleo de inclusão (com privacidade)
- **Pronto quando:** o professor recebe contexto antes da experimental (resolve a dor da Barra)

#### Sprint 3.2 — Ponte com Sucesso (Fábio → Lia/Sol)
- Escalar risco pedagógico que vira risco de evasão pra Lia/Sol com contexto
- **Pronto quando:** o Fábio escala corretamente sem assumir o atendimento

---

### 📱 FASE 4+ — O APP DO PROFESSOR (a casa do Fábio)
*Objetivo: dar interface visual ao professor, reaproveitando o LA Organizer*

#### Sprint 4.1 — Base do app (reaproveitar LA Organizer)
- Adaptar a base do LA Organizer (governança/organização) pro contexto pedagógico
- Estrutura: login do professor, home, navegação
- **Pronto quando:** professor acessa o app e vê seus dados

#### Sprint 4.2 — Agenda do professor (LA)
- Agenda de aulas, recitais, eventos, avaliações, reuniões
- Lembretes de pendências (preencher registros)
- **Pronto quando:** o professor vê e gerencia a agenda da LA no app

#### Sprint 4.3 — Lançamento por áudio no app
- Interface de gravação/envio de áudio dentro do app (não só WhatsApp)
- Visualização do conteúdo normalizado antes de confirmar
- **Pronto quando:** o professor lança aula por áudio direto no app

#### Sprint 4.4 — Histórico e jornada visual
- Visualização do histórico de cada aluno
- Jornada, marcos, tarefas, alertas
- Gamificação visual (metas, conquistas)
- **Pronto quando:** o professor vê a jornada de cada aluno visualmente

#### Sprint 4.5+ — Camada pessoal (futuro)
- Agenda pessoal/profissional do professor (fora da LA)
- Cuidado pessoal mais amplo
- Apoio direto ao aluno (Fase 2 do escopo — lembrete de estudo, exercícios)

---

## 5. MVP — o que entrega valor primeiro

> O MVP é o Fábio já plugado e funcionando, servindo o professor com prioridades. O **registro por áudio é o coração do MVP** — o Quintela cravou como o recurso matador ("não pode não ter isso").

**MVP = Fase 0 + Alma (1.1) + Áudio (2.1–2.4) + Briefing/Revisitação**

```
✅ Hermes preparado + LA Report/LA Journey plugados + regras normalizadas
✅ Fábio com alma (SOUL/AGENTS/PERMISSOES)
✅ Registro de aula por áudio → normaliza → confirma → grava (O CORAÇÃO)
✅ Revisitação: briefing pré-aula com o histórico
✅ Briefing diário do professor (alunos do dia, quem faltou)
```

**Vem logo depois do MVP (não no coração, mas cedo):**
```
○ Relatório da coordenação automatizado
○ Aluno faltando / alertas pedagógicos
```

Nesse ponto o Fábio já vive, já consome dados reais e já entrega o recurso matador (áudio) — tudo via WhatsApp, antes mesmo do app existir. O relatório da coordenação é importante, mas o áudio é o que faz o professor "dar mortal pra trás" (palavras do Quintela).

---

## 6. Dependências e Riscos

| Item | Status | Risco |
|---|---|---|
| Hermes preparado (runtime) | A fazer (Fase 0) | Novo runtime, primeira vez |
| MCP LA Report (escrita) | A confirmar | Precisa permitir escrita |
| MCP LA Journey | A confirmar | — |
| Endpoint Emusys → LA Report | A confirmar | Endpoint alimentando o LA Report corretamente |
| Transcrição de áudio | A definir ferramenta | Qualidade da transcrição PT-BR |
| Integração com Mila | Depende da Mila | Mila precisa capturar bem o interesse |
| Base do LA Organizer | Existe (Tom usa) | Adaptar pro pedagógico |

---

## 7. Guardrails do Sistema (inegociáveis)

- O Fábio não diagnostica aluno/criança
- Não expõe diagnóstico/laudo do núcleo de inclusão (sinaliza necessidade de cuidado, com privacidade)
- Não rotula professor; não decide advertência/desligamento
- Não grava conteúdo definitivo sem confirmação do professor quando há ambiguidade
- Normalização preserva o sentido do que o professor falou
- Não trata de financeiro (Maria) nem assume relacionamento/retenção (Sol/Lia)
- Health Score é régua com evidência, conduzida com a coordenação — não punição automática

---

## 8. Ordem de Execução (resumo)

```
1. Fechar escopo (✅ feito — fabio-escopo-completo.md)
2. Este PRD (✅ você está lendo)
3. FASE 0: Hermes + MCPs + regras de negócio
4. FASE 1: alma do Fábio + primeiras skills (agente ganha vida)
5. FASE 2: registro por áudio (MVP completo)
6. FASE 3: integração entre agentes (Mila, Lia/Sol)
7. FASE 4+: App do Professor (a casa)
```

> **Princípio que guia tudo:** o Fábio ganha vida primeiro com o que já existe. O app vem servir o Fábio depois. Nada de construir casa antes de ter morador.

---

*LA Music — PRD do Sistema Pedagógico Agent-First*
*"Fábio: Cuidado + Evolução. O agente que captura, organiza e devolve continuidade pedagógica."*
