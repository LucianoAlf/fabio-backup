---
name: consultar-prontuario-aluno
description: Use quando o Fábio precisar consultar, resumir ou narrar o histórico/prontuário pedagógico de um aluno da LA Music: “história do aluno”, “o que já estudou”, “prepara minha aula com ele/ela”, continuidade pedagógica, histórico por curso, aulas anteriores, registros do Emusys, registros do Fábio, relatório pedagógico individual ou transição entre professores.
version: 1.0.0
metadata:
  hermes:
    tags: [la-music, fabio, prontuario, aluno, historico-pedagogico, la-report, la-teacher, emusys]
    related_skills: [registro-aula-audio-la-music, briefing-pedagogico-la-music]
---

# Fábio · Prontuário do Aluno

## Objetivo

Ler a vida pedagógica do aluno como uma linha do tempo única, sem misturar fontes nem criar duas verdades.

O histórico antigo continua vindo do Emusys. O registro novo do Fábio fica no campo do Fábio. A unificação acontece **na leitura**, pela view `public.vw_prontuario_aluno`.

## Quando usar

Use esta skill quando o pedido envolver:

- “me conta a história da/do aluno”;
- “o que ela/ele já estudou?”;
- “prepara minha aula com essa/esse aluno”;
- “histórico pedagógico”; 
- “prontuário do aluno”; 
- “continuidade da aula”; 
- “relatório individual”; 
- consulta atravessando aulas antigas do Emusys + registros novos do Fábio.

Esta é uma skill de **leitura**. Ela não substitui a skill `registro-aula-audio-la-music` nem autoriza escrita.

## Fonte canônica de leitura

Use:

```sql
select *
from public.vw_prontuario_aluno
where aluno_id = $1
order by data_aula desc, aula_id desc;
```

A view entrega, por aula/aluno:

- `aluno_id`, `aluno_nome`, `unidade_id`;
- `aula_id`, `data_aula`, `curso_nome`;
- `professor_id`, `professor_nome`;
- `nr_da_aula`;
- `texto` — o registro principal da timeline;
- `origem` — `fabio` ou `emusys`;
- `texto_emusys_paralelo` — quando há registro do Fábio e também anotação Emusys na mesma aula;
- `presenca`.

## Regra central: unificar na leitura, nunca migrar

- `aulas_emusys.anotacoes` pertence ao Emusys/sync.
- `aulas_emusys.anotacoes_fabio` pertence ao Fábio/RPC `registrar_aula_fabio`.
- As duas fontes convivem.
- Não copiar legado do Emusys para `anotacoes_fabio`.
- Não sobrescrever `anotacoes` com texto do Fábio.
- Não tentar “limpar” origem antiga.

A verdade operacional é: **uma timeline, duas procedências explícitas**.

## Identidade: aluno.id não é pessoa

`alunos.id` é linha operacional/matrícula, não pessoa universal.

A mesma pessoa pode ter mais de um `aluno_id` quando faz mais de um curso. Exemplo canônico: Valentina possui três linhas/cursos.

Antes de narrar a “vida inteira” de alguém:

1. resolva quais `alunos.id` pertencem à mesma pessoa;
2. mantenha cursos separados;
3. consulte a view para todos os IDs resolvidos;
4. ordene a timeline por data;
5. sinalize qualquer ambiguidade.

Nunca consolidar por nome de forma cega. Nome + unidade é fallback assistido, não identidade perfeita.

## Como responder

Sempre que resumir histórico:

1. separar por curso quando houver mais de um;
2. manter sequência temporal;
3. declarar a origem quando isso importar: `Emusys`, `Fábio`, ou “registro do Fábio com anotação Emusys paralela”;
4. não inventar evolução que não esteja no texto;
5. diferenciar ausência de registro de ausência de aula;
6. se a cobertura for baixa, dizer isso claramente.

Formato recomendado para briefing pré-aula:

```md
## Prontuário — <Aluno>

### Visão geral
- Cursos encontrados: ...
- Período com registros: ...
- Fontes: Emusys (...), Fábio (...)

### Linha pedagógica recente
- <data> · <curso> · Aula <nr> · <origem>: <síntese fiel>

### Padrões observados
- ... somente com evidência textual

### Para a aula de hoje
- Retomar: ...
- Observar: ...
- Perguntar ao professor se quiser completar: ...
```

## `vw_fabio_aulas_contexto` ≠ `vw_prontuario_aluno`

Não confundir:

| View | Pergunta que responde | Uso |
|---|---|---|
| `vw_fabio_aulas_contexto` | Quem está na aula agora? | roster/contexto da aula para fatiar áudio e registrar aula |
| `vw_prontuario_aluno` | Qual é a história pedagógica do aluno? | leitura histórica, briefing, relatório e continuidade |

O Fábio precisa das duas, mas com papéis diferentes.

## Proibições

- Não escrever direto em `aulas_emusys`.
- Não executar `UPDATE`, `INSERT` ou `DELETE` para montar prontuário.
- Não copiar `anotacoes` para `anotacoes_fabio`.
- Não apagar/ocultar procedência.
- Não fundir cursos diferentes em uma narrativa única sem avisar.
- Não criar diagnóstico, laudo ou rótulo clínico a partir do histórico.
- Não incluir financeiro.

## Validação mínima antes de afirmar

Antes de responder “vida inteira”:

- conferir quantidade de entradas retornadas;
- conferir cursos presentes;
- conferir intervalo de datas;
- conferir distribuição por `origem`;
- se houver múltiplos `aluno_id`, deixar isso explícito internamente e narrar por curso.

Se a view retornar vazio, diga que não há prontuário pedagógico registrado nessa fonte; não invente continuidade.
