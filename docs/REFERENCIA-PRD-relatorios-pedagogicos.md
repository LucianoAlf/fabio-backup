# Referência — PRD Sistema de Relatórios Pedagógicos LA Music (Kids + School)

> **Status:** documento de referência (versão anterior, construída pelo Alf).
> **Como se encaixa na arquitetura do Fábio:** este PRD é a **base da futura skill de RELATÓRIO do aluno** (avaliação periódica), NÃO da skill de áudio (registro de aula).

---

## NOTA DE CONTEXTO — leitura obrigatória antes de usar

Este PRD foi desenhado como um **sistema separado** (mini-SaaS: login, dashboard, formulário que o professor preenche na tela). Na arquitetura agent-first do Fábio, a **casa muda**, mas o **miolo pedagógico é ouro e se aproveita**.

### O que MUDA (arquitetura)
- ❌ Sistema separado com login/dashboard próprio → ✅ Fábio no WhatsApp + LA Report
- ❌ Professor preenche formulário na tela → ✅ Professor manda áudio, Fábio normaliza
- ❌ Banco/stack próprios (Lovable/Supabase novo) → ✅ LA Report é o hub

### O que se APROVEITA (ouro pedagógico)
- ✅ **Faixas etárias e cursos:**
  - LA Music Kids → Musicalização (6m-2a), Preparatória (3-5a), Iniciação (6-11a)
  - LA Music School → 12+
- ✅ **Sistema de critérios:** Sim / Às vezes / Em Construção + observação livre
- ✅ **Estados do relatório:** Rascunho → Pendente → Aprovado → Rejeitado
- ✅ **Regra de histórico:** não substitui, acrescenta (linha do tempo do aluno)
- ✅ **Fluxo:** professor preenche → coordenação aprova → vira leitura

### Distinção das duas skills (não misturar)
| | Skill de ÁUDIO (registro de aula) | Skill de RELATÓRIO (avaliação) |
|---|---|---|
| O que captura | O que rolou em CADA aula | Avaliação periódica do aluno |
| Frequência | Toda aula | Bimestre / semestre |
| Origem | Áudio do professor → normaliza → grava | Lê os registros de aula + aplica template |
| Base | Modelo dos coordenadores (aguardando) | **Este PRD** |
| Relação | É a FONTE | É o CONSUMIDOR (lê a fonte) |

---

## PRD ORIGINAL (preservado)

### 1. Objetivo
Sistema interno para que professores preencham relatórios pedagógicos digitais de seus alunos, organizados por curso, idade e unidade. Praticidade para professores, controle e visibilidade total para a coordenação/admin, relatórios finais padronizados para impressão e arquivamento.

### 2. Perfis de Usuário
**Professor:** acessa apenas seus alunos; preenche relatórios; salva rascunho; finaliza no prazo; recebe alertas via WhatsApp.
**Admin/Coordenação:** gerencia cadastros (manual ou CSV/XML); cria/edita modelos por curso e faixa; vê todos os relatórios; exporta em lote PDF; recebe alertas de prazos; dashboards.

### 3. Modelos de Relatório
- Cada curso/faixa etária tem perguntas diferentes.
- Admin cria/edita modelos sem dev.
- Perguntas com opções: **Sim / Às vezes / Em Construção**.
- Campo aberto para observações.
- Separação: **LA Music Kids (6 meses a 11 anos)** vs **LA Music School (12+)**.
  - Kids subdividido: Musicalização (6m-2a), Preparatória (3-5a), Iniciação (6-11a).

### 4. Estados do Relatório
1. **Rascunho** — professor pode editar
2. **Pendente Aprovação** — enviado para coordenação
3. **Aprovado** — finalizado, liberado para impressão (bloqueado para edição)
4. **Rejeitado** — retorna ao professor com comentários

### 5. Regras de Negócio
- Professor só vê seus alunos vinculados.
- Coordenação tem visão global.
- Relatório editável só até a data limite → depois leitura.
- Histórico: **não substitui, só acrescenta** (linha do tempo).
- Separação clara Kids vs School para filtros e relatórios.

### 6. Funcionalidades de apoio (referência)
- Dashboard: % concluídos vs pendentes, professores atrasados, filtros por unidade/curso/faixa/professor/aluno.
- Notificações WhatsApp: lembrete de prazo (professor), lista de pendentes (coordenação), alertas inteligentes ("Professor X tem 5 relatórios pendentes").
- Exportação: PDF A4 paisagem com logo, quadro Sim/Às vezes/Em Construção, espaço para assinatura; lote por turma/professor/unidade; Excel consolidado.
- Auditoria: log de ações, versionamento, backup.

### 7. Faixas e templates (o coração pedagógico)
- **Kids – Musicalização (6 meses – 2 anos)**
- **Kids – Preparatória (3-5 anos)**
- **Kids – Iniciação (6-11 anos)**
- **School (12+)**
- Campos condicionais (aparecem conforme respostas) — sugestão.
- Templates inteligentes: sugestões por idade do aluno, tempo de curso, relatórios anteriores — sugestão.

### 8. Roadmap original (referência)
- Fase 1 MVP: login, cadastro CSV/XML, preenchimento, export PDF simples, dashboard básico.
- Fase 2: editor de modelos, gráficos, notificações WhatsApp, export em lote com design LA.
- Fase 3: relatórios comparativos (linha do tempo), KPIs cruzados, alertas preditivos.

---

## PRÓXIMO PASSO (quando chegar a skill de relatório)
Quando o Fábio for construir a skill de relatório do aluno, esta referência fornece os templates de critérios por faixa etária. A skill vai: ler os registros de aula do período (fonte: skill de áudio) → aplicar o template da faixa → gerar a avaliação Sim/Às vezes/Em Construção → coordenação aprova.
