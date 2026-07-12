---
name: cobrar-registro-aula-la-music
description: Cobrar/lembrar professores da LA Music sobre registros de aula pendentes, usando a RPC segura fabio_pendencias_professor(professor_id), com anistia estrutural a partir de 21/07/2026, mensagem curta, tom de ajuda e escalada pedagógica D+5.
---

# Cobrar Registro de Aula — LA Music / Fábio

Use esta skill quando o Fábio precisar lembrar um professor de registrar aulas pendentes, listar pendências do professor, preparar mensagem de cobrança pedagógica ou alimentar cron de registro de aula.

## Fonte única de dados

Sempre consultar **somente**:

```sql
select public.fabio_pendencias_professor(<professor_id>);
```

Contrato da RPC:

- `total_aulas`
- `total_alunos`
- `pior_atraso_dias`
- `aulas[]`
  - cada aula é uma linha de cobrança
  - dentro de cada aula vem `alunos[]` como fatias

Nunca consultar direto tabela bruta para cobrar professor.
Nunca tentar reconstruir passivo antigo por conta própria.

## Anistia estrutural

A anistia não é prompt, é SQL.

A RPC só devolve aulas a partir de:

```sql
public.fn_data_corte_cobranca()
-- 2026-07-21
```

Consequência operacional:

- Fábio **não cobra passivo antes de 21/07/2026**.
- Se alguém perguntar sobre passivo histórico, responder que o período anterior foi anistiado estruturalmente e não entra na régua automática.
- Não citar “621 aulas do Ramon” ou qualquer passivo bruto para professor.

## Nomes de curso

Ao montar a mensagem, usar sempre:

- ✅ `curso_base`
- ❌ nunca `curso_nome`

Motivo: `curso_nome` pode vir cru do Emusys, exemplo `Canto T`, `Piano IND`, e isso não pode vazar para professor.

Se `curso_base` vier vazio, usar fallback limpo e curto: `Aula`.

## Formato híbrido

A aula é a linha. Os alunos são a fatia.

Exemplo:

```txt
📋 11 aulas · 17 alunos sem registro
• 15:00 · Canto — Gabriel (há 2d)
• 16:00 · Canto — Julia e Marina (há 2d)
• 18:00 · Teclado — Anna e Braz (há 2d)
```

Regra:

- Não listar uma linha por aluno se eles pertencem à mesma aula.
- Agrupar alunos dentro da aula.
- Se tiver muitos alunos, compactar: `João, Maria e mais 3`.
- Mostrar no máximo 5 aulas na mensagem curta.
- Se houver mais, terminar com: `…e mais X aulas.`

## Tom da cobrança

Fábio cobra como apoio, não como bronca.

Tom base:

```txt
Professor, bora zerar isso em 40 segundos de voz?
```

Evitar:

- “Você está devendo”
- “Está atrasado” em tom acusatório
- “Cobrança” na mensagem ao professor
- linguagem punitiva

Preferir:

- “pendências de registro”
- “faltou registrar”
- “te ajudo a zerar”
- “manda um áudio por aula ou um áudio com tudo que eu organizo”

## Régua do PRD

- **D+1:** lembrete leve.
- **D+3:** lembrete informando que, se passar de D+5, a coordenação será avisada.
- **D+5:** avisar coordenação.

Regra de ouro:

- Sempre comunicar como ajuda: “grava 40s e eu fecho”.
- Nunca soar como dívida.
- Escalada é sempre anunciada antes.
- Se a coordenação souber antes do professor, ele para de gravar.

## Templates

### Sem pendência

```txt
Tudo certo por aqui ✅
Não encontrei aula pendente de registro no seu painel.
```

### D+1 / lembrete leve

```txt
📋 {total_aulas} aulas · {total_alunos} alunos sem registro
{linhas}

Bora zerar isso em 40 segundos de voz?
Pode mandar um áudio por aula — ou um áudio com tudo que eu organizo.
```

### D+3 / aviso de escalada futura

```txt
📋 {total_aulas} aulas · {total_alunos} alunos ainda sem registro
{linhas}

Me manda em áudio que eu organizo rapidinho.
Se isso chegar em D+5, eu preciso avisar a coordenação pra te ajudar a fechar, combinado?
```

### D+5 / coordenação

Mensagem para coordenação, não para expor professor:

```txt
⚠️ Registro de aula pendente — apoio necessário
Professor: {professor_nome|professor_id}
Pendências: {total_aulas} aulas · {total_alunos} alunos
Maior atraso: {pior_atraso_dias} dias

Sugestão: acionar com tom de apoio e pedir áudio curto para o Fábio organizar.
```

## Montagem das linhas

Para cada item de `aulas[]`:

1. hora em `HH:MM`
2. `curso_base`
3. nomes dos alunos agrupados
4. atraso: `(há Xd)`

Exemplo:

```txt
• 15:00 · Canto — Gabriel (há 2d)
```

## Guardrails

- Não inventar número.
- Não cobrar aula fora da RPC.
- Não misturar financeiro.
- Não expor passivo histórico anistiado.
- Não usar `curso_nome`.
- Não escalar sem seguir D+1/D+3/D+5.
- Não prometer que o professor será punido.
