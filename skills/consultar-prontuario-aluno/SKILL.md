---
name: consultar-prontuario-aluno
description: Ler e narrar a vida pedagógica de um aluno da LA Music — o que ele já estudou, como evoluiu, o que foi registrado sobre ele ao longo do tempo. Usar SEMPRE que a tarefa envolver histórico do aluno, prontuário, "o que ele já viu", evolução, relatório de vida na escola, resumo pedagógico, preparação de aula com base no passado, passagem de bastão entre professores, ou qualquer pergunta que comece com "me conta sobre o aluno X". NÃO usar para registrar uma aula nova (isso é o fluxo normal do Fábio) nem para dados financeiros (proibidos).
---

# Consultar o prontuário do aluno

## O que é o prontuário

A vida pedagógica de um aluno da LA Music é contada por **duas fontes que convivem**:

| Fonte | Quem escreve | O que é |
|---|---|---|
| `aulas_emusys.anotacoes` | o professor, digitando **no Emusys** | o registro histórico (18k+ aulas desde sempre) |
| `aulas_emusys.anotacoes_fabio` | **você (Fábio)**, via `registrar_aula_fabio` | o registro novo, gerado do áudio do professor |

**Elas não competem — elas se somam.** A escola está em transição: os professores estão migrando
do Emusys para o app, um a um. Um aluno pode ter 3 anos de anotações do Emusys e, a partir de
julho/2026, anotações suas. **As duas são o prontuário dele.**

**Nunca trate a anotação do Emusys como "legado descartável".** Ela é o passado real do aluno —
o que ele estudou, o que o professor observou, como ele evoluiu. Um relatório de vida que ignore
isso está mentindo por omissão.

## Onde ler: `vw_prontuario_aluno`

Esta é a **fonte canônica de leitura** do prontuário. Ela unifica as duas origens numa linha do
tempo só, sem copiar nada.

```sql
select data_aula, curso_nome, professor_nome, texto, origem, presenca
from public.vw_prontuario_aluno
where aluno_id = any($1)      -- TODAS as linhas da pessoa (ver "Identidade" abaixo)
order by data_aula desc;
```

Colunas que importam:
- `texto` — a anotação (já resolve a preferência: Fábio quando existe, Emusys quando não)
- `origem` — `'fabio'` ou `'emusys'`. **Sempre saiba de onde veio o que você está lendo.**
- `texto_emusys_paralelo` — quando as DUAS existem na mesma aula, guarda a do Emusys também.
- `curso_nome`, `professor_nome`, `data_aula`, `nr_da_aula`, `presenca`

## Identidade: o aluno não é uma linha

**`alunos.id` é uma linha de matrícula, não uma pessoa.** A mesma criança com 3 cursos tem
**3 linhas** em `alunos`.

Exemplo real: a Valentina tem `697` (Canto), `1542` e `1099` (Teclado, Power Kids). São a mesma
menina.

Para montar o prontuário **da pessoa**, junte todas as linhas dela:

```sql
-- a chave REAL da pessoa: (unidade_id, emusys_student_id). Nunca por nome (homônimo).
select array_agg(a2.id)
from public.alunos a2
where a2.emusys_student_id = (select emusys_student_id from public.alunos where id = $1)
  and a2.unidade_id        = (select unidade_id        from public.alunos where id = $1);
```

Se o aluno não tiver `emusys_student_id` (≈3% dos casos), aí sim cai no nome + unidade — e
**avise que a consolidação foi por nome** (pode unir homônimos).

## Regras de ouro

1. **Nunca invente.** Se não há anotação, diga "sem registro nessa aula". Não preencha buraco com
   inferência. O buraco é informação — significa que o professor não registrou.

2. **Sempre diga a origem.** "Segundo o registro do professor no Emusys (mar/2026)..." é diferente
   de "No relatório que gerei da aula de segunda...". O usuário precisa saber a procedência.

3. **Separe os cursos.** Um aluno com Canto e Teclado tem duas histórias pedagógicas, com
   professores diferentes. Não misture o progresso vocal com o progresso no teclado.

4. **Respeite o escopo de quem pergunta.** Se um PROFESSOR pergunta sobre um aluno, ele só pode
   ver o(s) curso(s) **dele** com aquele aluno + a menção de que o aluno faz outros cursos
   (sem conteúdo). A coordenação vê tudo. Na dúvida, restrinja.

5. **Zero financeiro.** Nunca. Não existe no prontuário e não pode aparecer.

6. **Nada de anamnese em resposta casual.** É dado sensível (saúde, família, desenvolvimento).
   Só em tela autorizada.

## Escrita: você só escreve numa coluna

Você escreve **exclusivamente** via `registrar_aula_fabio`, e **só** na `anotacoes_fabio`.

**Você NUNCA toca a `anotacoes` do Emusys.** Aquilo é do professor. Existe uma trigger no banco
(`trg_proteger_anotacoes_fabio`) protegendo o seu lado — e o sync do Emusys foi auditado pra não
tocar o seu. As duas fontes são invioláveis uma pra outra.

## Playbook: "me conta a história do aluno X"

1. Resolver a pessoa → todas as linhas de `alunos` dela (chave segura).
2. Ler `vw_prontuario_aluno` pra todas essas linhas, ordenado por data.
3. Agrupar **por curso** (Canto é uma história, Teclado é outra).
4. Narrar a evolução: o que aparece cedo, o que aparece depois, o que se repete (dificuldade
   persistente), o que sumiu (superado).
5. Marcar os **buracos**: períodos sem registro. Diga quantas aulas ficaram sem anotação.
6. Fechar com o estado atual: em que aula da jornada está, presença recente.

## Playbook: "prepara minha aula com o aluno X"

1. Ler as **últimas 3-5 entradas** do prontuário (só o curso do professor que perguntou).
2. Extrair: o que foi trabalhado, o próximo passo que ficou marcado, o dever de casa.
3. Entregar curto: "Na última aula (25/mai) vocês trabalharam projeção vocal. Ficou marcado
   iniciar respiração. O dever era treinar a escala de dó."
4. Se não houver registro recente, diga: "Sem registro desde X. Não sei o que vocês fizeram."

## O que NÃO fazer

- ❌ Copiar anotação do Emusys pra dentro da `anotacoes_fabio` ("migrar o histórico").
  Isso cria duas verdades. A unificação é na LEITURA (a view), não na escrita.
- ❌ Consolidar aluno por nome quando existe `emusys_student_id`.
- ❌ Reduzir dois cursos a um contador ou a uma história só.
- ❌ Apresentar o que você (IA) inferiu como se fosse registro do professor.
- ❌ Tratar cobertura zero como "o aluno não evoluiu". Ausência de registro ≠ ausência de aula.

## Estado atual (jul/2026)

- 18.729 aulas com anotação do Emusys.
- As primeiras anotações do Fábio começam a nascer com o professor-piloto (Matheus, prof 25).
- Espere `origem: 'emusys'` na esmagadora maioria por enquanto. Isso é o normal, não um erro.
