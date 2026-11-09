# Pessoa 4 — Primeiro commit: procedures, função e triggers

## Entrega

| Objeto | Tipo | Comportamento |
|---|---|---|
| Verificar_atividades | Procedure (corrigida em sql/03) | Sem parâmetro. Atualiza toda a tabela atividades_recentes com CURRENT_DATE(), sem alterar a prioridade. |
| Conta_usuários | Procedure | Recebe o ID de um arquivo e devolve total_usuarios, a quantidade de usuários diferentes com acesso. |
| Remover_acessos | Procedure | Recebe o ID de um arquivo e remove o acesso de todos os usuários, menos o do proprietário. |
| usr_carregar_arquivo | Procedure | Carrega arquivo para a conta MySQL conectada; não recebe ID. |
| usr_atualizar_arquivo | Procedure | Atualiza arquivo ativo do próprio usuário, localizado pelo nome; não recebe ID. |
| fn_arquivo_inativo | Função | Retorna 1 se a última alteração registrada em atividades_recentes tem mais de 100 dias; senão 0. |
| fn_arquivo_executavel | Função auxiliar | Indica se nome (última extensão) ou tipo (extensão ou MIME) correspondem a executável. |
| Safe_security | Trigger BEFORE INSERT em arquivo | Impede a inserção de executáveis. |
| Safe_security_update | Trigger BEFORE UPDATE em arquivo | Impede o mesmo desvio por renomeação ou troca de tipo. Só age quando nome ou tipo mudam. |
| Registrar_operacao | Trigger AFTER INSERT em operacao_arquivo | Cria ou atualiza ultima_versao em atividades_recentes; preserva a prioridade. |
| Atualizar_acesso | Trigger AFTER INSERT em compartilhamento | Atualiza o registro do arquivo em atividades_recentes quando um usuário ganha acesso. |
| Atualizar_acesso_update | Trigger AFTER UPDATE em compartilhamento | Mesmo efeito quando o destinatário ou o arquivo de um compartilhamento muda. |

Verificar_atividades já existia com o parâmetro p_id_arquivo, o que divergia do enunciado, que pede a atualização de toda a tabela. A correção foi feita no próprio sql/03, para não haver duas definições. Chavear foi revisada e mantida como estava, pois já alterna PRIORITARIO e NAO_PRIORITARIO conforme o enunciado.

## Interpretações adotadas

O enunciado não detalha algumas regras. As escolhas abaixo foram as mais conservadoras.

- Conta_usuários segue fn_pode_acessar: arquivo PRIVADO conta 1 usuário; COMPARTILHADO conta o proprietário mais os destinatários distintos; PUBLICO conta todos os usuários cadastrados. Arquivo inexistente ou removido é recusado.
- Remover_acessos apaga as linhas de compartilhamento do arquivo. O proprietário nunca possui linha ali, pois seu acesso vem de arquivo.id_dono. Se o arquivo era PUBLICO ou COMPARTILHADO, ele passa a PRIVADO; sem isso, terceiros continuariam com acesso. ultima_modificacao e o histórico não são alterados, pois não há tipo de operação para isso.
- fn_arquivo_inativo retorna 0 para arquivo sem registro em atividades_recentes. Sem data registrada não há como afirmar inatividade, e nenhuma outra fonte de data é usada.
- Atualizar_acesso: o enunciado não define o que são os registros de arquivo do usuário. O único registro por arquivo no projeto é atividades_recentes; portanto, um novo compartilhamento cria ou atualiza o registro do arquivo com a data do compartilhamento. A prioridade é preservada. Acesso por permissão PUBLICO não dispara o trigger, pois não existe evento por usuário.
- Registrar_operacao usa GREATEST para que a data nunca retroceda.
- Safe_security bloqueia pela última extensão (exe, com, bat, cmd, msi, msp, scr, pif, cpl, jar, vbs, vbe, wsf, wsh, ps1, sh, bash, run, apk, elf), ignorando maiúsculas, espaços e pontos finais, e pelo tipo. `relatorio.exe.txt` e `execucao.docx` são aceitos; `foto.jpg.exe` é bloqueado. O conteúdo do arquivo não é analisado.

As procedures usr_* identificam o usuário por USER() e chamam as sp_* já existentes, que continuam validando dono e cota. Elas existem porque as sp_* recebem IDs e não podem ser concedidas a usuários comuns. Nenhum privilégio é concedido neste commit.

## Como executar

1. Envie as pastas sql e docs para a raiz do repositório, mesclando as existentes.
2. Conecte como root ao banco que já possui os scripts 01 a 05, com o cliente em utf8mb4. O nome Conta_usuários tem acento. Pelo terminal: `mysql -u root -p --default-character-set=utf8mb4 < sql/06-procedures-permissoes.sql`.
3. Execute sql/06-procedures-permissoes.sql e, depois, sql/07-funcoes-triggers.sql.
4. Se o banco já executou a versão anterior do sql/03, execute `DROP PROCEDURE Verificar_atividades;` e recrie apenas o bloco dessa procedure. Em um banco novo, execute o sql/03 normalmente.

Os scripts criam cada objeto uma vez e não substituem objetos existentes. Não reexecute o modelo físico.

## Teste manual no MySQL

Como root, com dados de teste criados:

```sql
USE webdriver;
CALL Verificar_atividades();
SELECT COUNT(*) FROM atividades_recentes WHERE ultima_versao <> CURRENT_DATE();
CALL `Conta_usuários`(1);
CALL Chavear(1);
CALL Remover_acessos(1);
SELECT fn_arquivo_inativo(1);
```

Confira que a contagem de datas diferentes é 0, que total_usuarios corresponde ao dono mais os compartilhamentos, que a prioridade alterna e que Remover_acessos deixa o arquivo apenas com o proprietário. Para fn_arquivo_inativo, ajuste ultima_versao para 101 dias atrás (resultado 1), 100 dias (resultado 0) e apague o registro (resultado 0).

Para os triggers, carregue um arquivo com sp_carregar_arquivo e confira o registro em atividades_recentes. Tente carregar `programa.exe`, `foto.jpg.EXE` e um tipo `application/x-msdownload`: todos devem ser recusados com a mensagem de Safe_security. Insira uma linha em compartilhamento e confira que o registro do arquivo foi criado ou atualizado.

Execução realizada: estes objetos foram executados em um MySQL 8.0.46 em Linux, com os scripts 01 a 08 em um banco novo, e os testes automatizados do commit 3 passaram. Não foram executados no MySQL Workbench nem em outras versões do MySQL.

## Commit no GitHub

Arquivos: sql/03-procedures-atividades.sql, sql/06-procedures-permissoes.sql, sql/07-funcoes-triggers.sql e docs/pessoa4-commit1.md.

Título: `Adiciona procedures, função e triggers de atividades e segurança`

Descrição: `Corrige Verificar_atividades para atualizar toda a tabela e implementa Conta_usuários, Remover_acessos, fn_arquivo_inativo e os triggers Safe_security, Registrar_operacao e Atualizar_acesso. Inclui procedures usr_* que obtêm a identidade da conta conectada, sem receber IDs.`
