---
name: briefing-pedagogico-la-music
description: Use when Alf or the LA Music team asks for a pedagogical briefing of a class, teacher, student group, or lesson journey from LA Report data. Produces a human, strategic reading of evolution instead of a raw lesson list.
version: 1.0.0
author: Fábio / Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [la-music, pedagogy, briefing, la-report, teachers, students]
    related_skills: []
---

# Briefing Pedagógico LA Music

## Overview

This skill guides Fábio when producing pedagogical briefings for LA Music from LA Report / Supabase data.

The goal is not to summarize rows. The goal is to read what the data says about the **student journey**, the **teacher's method**, and the **continuity of learning**.

Core posture:

> Tecnologia como ponte, não como camada fria.

The briefing must support the teacher and coordination with **cuidado + evolução**: useful, precise, humane, and never policing.

## When to Use

Use this skill when the user asks for:

- A briefing of a class/turma before a lesson.
- A pedagogical reading of lesson records from `aulas_emusys.anotacoes`.
- A synthesis of repertoire evolution, teacher routine, student progress, and next steps.
- A coordination-oriented summary of a teacher, turma, course, or pedagogical journey.
- Identification of attention points such as attendance, health score, missing anamnese, repeated difficulty, or weak individualization in lesson notes.

Do not use this for purely financial, commercial, or staff-scheduling questions unless they directly affect pedagogical continuity.

## Data Sources and Discovery

### Primary lesson source

Use `public.aulas_emusys`, especially:

- `data_aula`
- `data_hora_inicio`
- `turma_nome`
- `curso_nome`
- `professor_nome`
- `professor_id`
- `cancelada`
- `nr_da_aula`
- `qtd_alunos`
- `anotacoes`

Typical query shape:

```sql
select
  id,
  emusys_id,
  data_aula,
  data_hora_inicio,
  turma_nome,
  curso_nome,
  professor_nome,
  professor_id,
  cancelada,
  nr_da_aula,
  qtd_alunos,
  anotacoes
from public.aulas_emusys
where professor_nome ilike '%<professor>%'
  and turma_nome = '<turma>'
  and data_aula >= date '<inicio>'
  and data_aula < date '<fim_exclusivo>'
order by data_aula, data_hora_inicio;
```

When a class has multiple rows with identical `anotacoes` on the same date, group by date + annotation text so the same lesson is not counted as multiple pedagogical events:

```sql
select
  data_aula,
  min(data_hora_inicio) as data_hora_inicio,
  count(*) as registros_aulas,
  array_agg(id order by id) as aula_ids,
  max(qtd_alunos) as qtd_alunos_registro,
  anotacoes
from public.aulas_emusys
where professor_nome ilike '%<professor>%'
  and turma_nome = '<turma>'
  and curso_nome ilike '%<curso_opcional>%'
  and data_aula >= date '<inicio>'
  and data_aula < date '<fim_exclusivo>'
  and cancelada = false
  and anotacoes is not null
  and btrim(anotacoes) <> ''
group by data_aula, anotacoes
order by data_aula;
```

### Student and attendance source

Use `public.aluno_presenca` joined with `public.alunos` when the briefing asks who the students are, or when frequency/health/anamnese matters.

Typical query shape:

```sql
select
  ap.data_aula,
  ap.horario_aula,
  ap.turma_nome,
  ap.curso_nome,
  ap.status,
  ap.aula_emusys_id,
  ap.aluno_id,
  a.nome as aluno_nome,
  a.idade_atual,
  a.status as aluno_status,
  a.percentual_presenca,
  a.health_score,
  a.health_score_numerico,
  a.anamnese_preenchida,
  a.temperamento_codinome
from public.aluno_presenca ap
left join public.alunos a on a.id = ap.aluno_id
where ap.professor_id = <professor_id>
  and ap.turma_nome = '<turma>'
  and ap.curso_nome ilike '%<curso>%'
  and ap.data_aula >= date '<inicio>'
  and ap.data_aula < date '<fim_exclusivo>'
order by ap.data_aula, aluno_nome;
```

Summarize attendance by student:

```sql
with pres as (
  select
    ap.data_aula,
    ap.status,
    ap.aluno_id,
    a.nome as aluno_nome,
    a.percentual_presenca,
    a.health_score,
    a.health_score_numerico,
    a.anamnese_preenchida
  from public.aluno_presenca ap
  left join public.alunos a on a.id = ap.aluno_id
  where ap.professor_id = <professor_id>
    and ap.turma_nome = '<turma>'
    and ap.curso_nome ilike '%<curso>%'
    and ap.data_aula >= date '<inicio>'
    and ap.data_aula < date '<fim_exclusivo>'
)
select
  aluno_id,
  aluno_nome,
  percentual_presenca,
  health_score,
  health_score_numerico,
  anamnese_preenchida,
  count(*) as registros,
  count(*) filter (where status = 'presente') as presencas,
  count(*) filter (where status = 'ausente') as ausencias,
  string_agg(to_char(data_aula, 'DD/MM') || ':' || status, ', ' order by data_aula) as linha_presenca
from pres
group by aluno_id, aluno_nome, percentual_presenca, health_score, health_score_numerico, anamnese_preenchida
order by aluno_nome, aluno_id;
```

## Briefing Workflow

1. **Confirm the requested scope from the user's prompt.**
   - Teacher name.
   - Turma code/name.
   - Course/instrument if ambiguous.
   - Date range.
   - Required briefing sections.
   Completion criterion: every filter used in SQL can be traced to either the user's request or a clearly labeled assumption.

2. **Inspect schema only when needed.**
   - If table fields are unknown, query `information_schema.columns`.
   - Do not rely on memory for current schema.
   Completion criterion: you know the fields needed for lesson notes and student/attendance context.

3. **Fetch lesson records in chronological order.**
   - Use `aulas_emusys.anotacoes` as the pedagogical source of truth for what was worked.
   - Filter by professor, turma, date range, and course when needed.
   - Exclude cancelled lessons unless the user asks about cancellations.
   Completion criterion: all relevant lessons in the period are available, sorted by `data_aula`.

4. **Deduplicate repeated lesson rows.**
   - If the same date has multiple rows with identical notes, treat as one pedagogical lesson and mention that the raw table had multiple records.
   Completion criterion: the analysis does not over-count duplicated lesson text.

5. **Fetch student and attendance context.**
   - Join `aluno_presenca` with `alunos`.
   - Use professor_id from `aulas_emusys` when possible.
   - Look for duplicate student names, missing anamnese, health scores, and frequency patterns.
   Completion criterion: the briefing can name students and flag attendance/cadastro issues without guessing.

6. **Extract the pedagogical storyline.**
   Read across weeks and identify:
   - Repertoire worked.
   - Technical purpose behind each repertoire.
   - Method/routine that repeats.
   - Evolution from base work to applied repertoire.
   - Recurring difficulties or current bottleneck.
   Completion criterion: the output explains what the sequence of lessons *means*, not just what happened each date.

7. **Write as support + régua.**
   - Tone: partnership with teacher, clarity for coordination.
   - Avoid accusatory language.
   - Use evidence: "os registros mostram...", "aparece com frequência...".
   - Separate data issues from pedagogical issues.
   Completion criterion: the briefing can be shared with coordination or teacher without sounding like surveillance.

8. **End with source transparency.**
   - Name tables and filters.
   - Mention joins and grouping/deduplication.
   - Mention limitations, especially missing anamnese or generic notes.
   Completion criterion: Alf understands how the answer was produced.

## Recommended Output Structure

Use this structure unless the user asks otherwise:

```markdown
## Briefing pedagógico — <Curso/Turma>

**Professor:** <nome>
**Turma:** <turma>
**Curso:** <curso>
**Período analisado:** <datas>
**Aulas analisadas:** <datas>

## 1. Quem são os alunos da turma
<Table or bullets with names, age, attendance, health/anamnese when relevant>

## 2. O que a evolução do repertório conta sobre a turma
<Narrative synthesis of repertoire progression and learning stage>

## 3. Rotina e método do professor
<Repeated patterns, strengths, approach>

## 4. Pontos de atenção
<Frequency, difficulty, health score, missing anamnese, duplicated records, weak individualization>

## 5. Sugestão para a próxima aula
<Practical lesson preparation in blocks>

## 6. Resumo executivo para coordenação
<Short, strategic summary>

## De onde tirei os dados
<Tables, filters, joins, grouping, limitations>
```

## Pedagogical Reading Prompts

When reading `anotacoes`, ask:

- What repertoire repeats across weeks?
- Did the repertoire progress from method/base to applied or motivational music?
- What technique is being developed through each piece?
- What technical words recur: posture, afinação, arcadas, segundo dedo, mudança de corda, pulso, andamento, leitura, sincronização?
- What is the current bottleneck?
- Does the teacher use a stable opening routine?
- Does the register mention students individually or only the turma?
- Are tasks for the week specific enough?
- Is there a gap between student objectives/anamnese and the chosen repertoire?

## Attention Points to Flag Carefully

Flag these with care and evidence:

- **Duplicate student records:** same name with different IDs or attendance histories.
- **Missing anamnese:** limits individualization; state that the briefing is weaker without student goals/interests.
- **Health Score in atenção:** do not assume cause; suggest understanding whether it is pedagogical, relational, administrative, or historical.
- **Good attendance but low health:** signal as a cross-functional check, not a teacher failure.
- **Repeated generic notes:** suggest adding one individual line per student.
- **Technique repeated across weeks:** treat as likely current bottleneck, not necessarily lack of progress.
- **Special needs/inclusion:** never expose diagnoses or clinical detail; say only that the student needs a coordinated care note if such data appears.

## Language Patterns

Prefer:

- "Os registros indicam..."
- "A turma parece estar..."
- "Vale olhar com cuidado..."
- "Como apoio ao professor, eu sugeriria..."
- "Não dá para concluir o motivo só por esses dados..."
- "Isso é um ponto de continuidade pedagógica, não de cobrança."

Avoid:

- "O professor falhou..."
- "O aluno é problemático..."
- "A turma está atrasada..." without evidence.
- Diagnoses or labels for children.
- Treating Health Score as a verdict.

## Example Insight Patterns

### Repertoire progression

If lessons move from Suzuki basics to a recognizable song:

> A turma está construindo uma ponte entre base técnica e repertório afetivo. Isso tende a aumentar motivação, mas exige cuidado para não avançar no repertório antes de estabilizar fundamentos.

### Repeated technical focus

If the same technique appears repeatedly:

> O ponto técnico do momento parece ser <técnica>. Eu manteria isso como foco da próxima aula, isolando pequenos trechos antes de tocar a música inteira.

### Weak individual notes

If notes are collective only:

> O registro é bom para continuidade de conteúdo, mas ainda pouco individual. Para virar acompanhamento pedagógico completo, vale pedir uma linha por aluno: ponto forte e ponto a reforçar.

### Missing anamnese

If anamnese is false/missing:

> Sem anamnese, falta a camada do sonho, gosto musical e objetivo do aluno. O professor consegue seguir pelo repertório, mas a personalização fica limitada.

## Verification Checklist

Before finalizing, verify:

- [ ] The SQL filters match teacher, turma, course, and date range requested.
- [ ] Lesson notes were sorted chronologically.
- [ ] Duplicate raw rows were not over-counted as separate lessons.
- [ ] Students were identified from attendance/student tables when requested.
- [ ] Attendance/health/anamnese claims are grounded in query results.
- [ ] The output is a pedagogical narrative, not a raw list of dates.
- [ ] Suggestions are practical for the next lesson.
- [ ] Tone is supportive and humane.
- [ ] Source path is documented at the end.
