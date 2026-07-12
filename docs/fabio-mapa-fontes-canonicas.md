# Mapa de Fontes Canônicas do LA Report — para o Fábio (Fase 1, Pedagógico)

> Auditoria cruzada: banco (Supabase MCP) + front-end (repo LAperformanceReport) + docs `.claude/memory/`.
> Data: 23/06/2026. Status: rascunho para validação do Alf + Codex/Windsurf.

---

## 1. PRINCÍPIO (como o Fábio bebe dados)

1. **Fábio consome fontes CANÔNICAS, nunca legadas.** Tabela bruta só quando não há view/RPC canônica.
2. **As regras de negócio NÃO são reescritas na skill do Fábio.** Elas já vivem em `.claude/memory/` do LA Report (mantidas pelo time). A skill do Fábio só aponta QUAL doc/fonte usar.
3. **Regra de ouro herdada do LA Report:** "ler a fonte antes de afirmar". O Fábio nunca afirma como um número é calculado sem abrir a RPC/view/doc.
4. **Escopo do Fábio = PEDAGÓGICO.** Ele não bebe de MRR, faturamento, funil comercial (isso é Maria/Sol). Subconjunto do LA Report.

---

## 2. ESTRATÉGIA DA SKILL DE REGRAS (decisão a validar)

O LA Report já tem a base pronta em `.claude/memory/`:
- `regras-negocio-canonicas.md` — documento MESTRE (validado pelo Alf)
- `metricas.md` — definições de métricas
- `dominio-alunos.md`, `dominio-comercial.md`, `dominio-operacional.md`
- `auditoria-arquitetural-fontes-kpi-2026-06-07.md` — fontes de KPI (junho)
- `emusys-api.md` — API do Emusys

**Proposta (Opção C — híbrida):**
- A skill do Fábio NÃO copia as regras. Ela tem um **mapa pedagógico** (este documento): "pra cada frente, use esta RPC/view canônica".
- Para a regra detalhada, a skill aponta para o doc canônico correspondente.
- Assim: regras vivem num lugar só (LA Report), e o Fábio carrega só o mapa enxuto do que é pedagógico.

---

## 3. MAPA POR FRENTE PEDAGÓGICA

### Frente 1 — Jornada / Perfil do aluno
| Precisa | Fonte canônica | Observação |
|---|---|---|
| Perfil/anamnese | tabela `anamneses` + RPCs `get_anamnese_by_token`, `buscar_anamnese_pendente`, `get_anamnese_publica` | temperamento (CAZUZA/SLASH/FRANK/AMY) vem daqui |
| Dados do aluno | tabela `alunos` | ⚠️ REGRA: `alunos` = MATRÍCULAS, não pessoas (pessoa = nome+unidade_id) |

### Frente 2 — Registro de conteúdo de aula (áudio) ⭐ MVP
| Precisa | Fonte canônica | Observação |
|---|---|---|
| Conteúdo legado da aula | `aulas_emusys.anotacoes` | Escrito/sincronizado pelo Emusys; Fábio não sobrescreve |
| Conteúdo novo do Fábio | `aulas_emusys.anotacoes_fabio` via RPC `registrar_aula_fabio` | Escrito somente pelo Fábio/RPC; não recebe cópia do legado |
| Prontuário unificado do aluno | RPC `fabio_prontuario_aluno` com `professor_id` obrigatório | Porta canônica do Fábio: deduplica, escopa por professor em SQL e declara `origem` |
| Continuidade | `aulas_emusys.nr_da_aula` + RPC `fabio_prontuario_aluno` com `professor_id` obrigatório | número da aula e linha do tempo pedagógica segura |

### Frente 3 — Revisitação / Continuidade
| Precisa | Fonte canônica | Observação |
|---|---|---|
| Histórico/prontuário do aluno | RPC `fabio_prontuario_aluno` com `professor_id` obrigatório | une Emusys + Fábio na leitura, com deduplicação e escopo SQL |

### Frente 7 — Health Score (aluno e professor)
| Precisa | Fonte canônica | Observação |
|---|---|---|
| Health score do aluno | `calcular_health_score_aluno`, `atualizar_health_score`, `config_health_score_aluno`, hist. `alunos_health_score_historico` | 5 fatores ponderados |
| KPIs do professor | RPC `get_kpis_professor_periodo` ✅ (citada como viva no CLAUDE.md) | aceita p_ano+p_mes OU p_data_inicio+p_data_fim |

### Frente 8 — Avaliação / PDI / Professor 360
| Precisa | Fonte canônica | Observação |
|---|---|---|
| Professor 360 | `professor_360_avaliacoes`, `professor_360_ocorrencias`, `professor_360_criterios` + RPCs `editar_ocorrencia`, `reverter_ocorrencia` | gate comportamental ≥80 |
| Metas/PDI | `professor_metas`, `professor_acoes`, `professor_checkpoints` | |

### Frente 9 — Relatório da Coordenação ⭐
| Precisa | Fonte canônica | Observação |
|---|---|---|
| Relatório da coordenação | RPC `get_dados_relatorio_coordenacao` ✅ | **JÁ EXISTE** — a Frente 9 tem a função pronta |
| Carteira do professor | RPC `get_carteira_professores` | exclui banda e trancado |
| Frequência/faltas | RPC `get_faltas_periodo` | |
| Permanência | RPC `get_tempo_permanencia` ✅ (do mapeamento fev) | |

### Frente 10 — Gestão Pedagógica / Turmas
| Precisa | Fonte canônica | Observação |
|---|---|---|
| Análise de turmas | RPC `rpc_analise_turmas` | |
| Turmas | `vw_turmas_implicitas` (usada pelo front ✅) | snapshot atual |

---

## 4. REGRAS CRÍTICAS QUE O FÁBIO DEVE INTERNALIZAR
(extraídas do `regras-negocio-canonicas.md` — as que tocam o pedagógico)

- **`alunos` = matrículas, não pessoas.** 2 cursos = 2 linhas (1 principal `is_segundo_curso=false` + N `true`). Nome + unidade é fallback assistido, não identidade definitiva; para prontuário, resolver todos os `alunos.id` da pessoa e separar por curso.
- **`is_projeto_banda = true`** exclui o curso de: médias de turma, carteira do professor, score do professor. (Não usar filtro por nome tipo `ILIKE '%banda%'` — é legado frágil.)
- **Carteira do professor:** alunos `ativo` do `professor_atual_id`. Inclui segundo curso; exclui banda e `trancado`.
- **Score do professor (evasões):** só conta `motivos_saida.conta_score_professor = true`. Motivo NULL sem match = não conta. Exclui banda.
- **Taxa de conversão do professor (P7, validada Alf):** `matriculas_pos_experimental / experimentais_realizadas`. Só experimental realizada por aquele professor entra. Fonte: `lead_experimentais` (desde 2026-06-20).
- **Classificação (P10, validada Alf):** LAMK (Kids) = idade ≤ 11; EMLA (School) = idade ≥ 12.
- **Evasão** = cancelamentos + não-renovações. Aviso prévio e trancamento NÃO são evasão.

---

## 5. LISTA NEGRA — FONTES LEGADAS (o Fábio NÃO usa)

- `vw_kpis_retencao_mensal` — lê `evasoes_v2` desatualizada
- `vw_alertas_inteligentes` — usa `evasoes_legacy`
- `vw_evasoes_motivos`, `vw_evasoes_resumo` — usam `evasoes_legacy`
- `vw_professores_performance_atual` — usa `evasoes_legacy`
- Qualquer RPC com sufixo `_legacy_*` (ex: `get_dados_relatorio_gerencial_legacy_p01g`)
- Tabelas `*_backup_*` (ex: `evasoes_v2_backup`, `leads_diarios_backup`)
- Filtros por nome de curso (`ILIKE '%banda%'`, `'%canto coral%'`) — usar flags `is_projeto_banda` / `is_coral`

---

## 6. PENDÊNCIAS — CONFIRMAR COM CODEX/WINDSURF

1. **Views com `CURRENT_DATE`** (16 identificadas no mapeamento de fev): só funcionam pro mês atual, não pra histórico. Quais o Fábio pode usar e quais foram aposentadas?
2. **`vw_kpis_professor_completo` vs RPC `get_kpis_professor_periodo`:** a view usa CURRENT_DATE (só mês atual); a RPC é a viva. Confirmar que o Fábio usa SEMPRE a RPC.
3. **Taxa de renovação:** `aviso_previo` entra no denominador? (pendência ❓ aberta no doc canônico)
4. **`get_dados_relatorio_coordenacao`:** validar o que ela retorna hoje e se cobre o que o Fábio precisa pra Frente 9.
5. **RPCs canônicas novas** (`get_kpis_alunos_canonicos`, etc.) não estão no mapeamento de fev (são pós-sanitização). Confirmar quais substituem as views antigas.

---

## 7. PRÓXIMOS PASSOS SUGERIDOS

1. Alf + Codex validam este mapa (corrigir o que está como ❓).
2. Fechar a lista definitiva de RPCs/views canônicas pedagógicas.
3. Escrever a skill de regras do Fábio (mapa enxuto + ponteiros pros docs canônicos).
4. Só então construir as skills operacionais (briefing, áudio, revisitação, relatório coordenação).


---

## 8. Atualização — Prontuário do Aluno (12/07/2026)

Decisão arquitetural: não migrar o legado do Emusys para o campo do Fábio. A unificação acontece na leitura.

- `aulas_emusys.anotacoes`: fonte histórica/legada escrita pelo Emusys/sync.
- `aulas_emusys.anotacoes_fabio`: fonte nova escrita somente pela RPC `registrar_aula_fabio`.
- `public.vw_prontuario_aluno`: view interna/bruta da timeline; não é a porta do Fábio porque pode duplicar e não escopa por professor.
- `public.fabio_prontuario_aluno(p_aluno_id, p_professor_id, p_limite)`: RPC canônica do Fábio; deduplica por data+curso canônico, resolve pessoa por `(unidade_id, emusys_student_id)` e exige escopo por professor em SQL. A visão de coordenação usa `coord_prontuario_aluno`, sem grant para `fabio_agent`.
- Skill operacional: `skills/consultar-prontuario-aluno/SKILL.md`.

Regra: Fábio lê o prontuário pela RPC, declara procedência e nunca copia `anotacoes` para `anotacoes_fabio`.
