# Parte 2 — Permissões, segurança e objetos de procedural language

## Ordem de execução (como root, cliente com utf8mb4)

| # | Script | Conteúdo |
|---|---|---|
| 1–5 | `sql/01` a `sql/05` | Já existentes (modelo, `atividades_recentes`, procedures de atividades, views) |
| 6 | `sql/06-procedures-permissoes.sql` | `Conta_usuários`, `Remover_acessos`, `usr_carregar_arquivo`, `usr_atualizar_arquivo` |
| 7 | `sql/07-funcoes-triggers.sql` | `fn_arquivo_inativo`, `fn_arquivo_executavel`, triggers |
| 8 | `sql/08-roles-permissoes.sql` | Roles e GRANTs por objeto |

Divergência em relação à sugestão de nomes: o script de roles é o último (08) porque `GRANT EXECUTE` exige que as rotinas já existam.

## Privilégios

| Role | Pode | Não pode |
|---|---|---|
| PapelUsuario | `SELECT` em `vw_arquivos_autorizados` e `vw_historico_usuario`; `EXECUTE` em `usr_carregar_arquivo` e `usr_atualizar_arquivo` | Qualquer tabela, `sp_*` (recebem IDs), histórico (só leitura), `atividades_recentes` |
| PapelEmpresa | `SELECT` em `vw_empresa_usuarios` e `vw_empresa_arquivos` | Qualquer escrita, outras instituições, tabelas, rotinas |
| PapelAdm | `SELECT/INSERT/UPDATE/DELETE` em todas as tabelas **exceto** `atividades_recentes`; `SELECT` nas `vw_admin_*`; `EXECUTE` em `sp_*`, `Conta_usuários`, `Remover_acessos`, `fn_pode_acessar` | `atividades_recentes`, `Verificar_atividades`, `Chavear`, `fn_arquivo_inativo` |

Nenhum `GRANT` em `webdriver.*` ou `*.*`. `atividades_recentes`, `Verificar_atividades`, `Chavear` e `fn_arquivo_inativo` ficam exclusivos do root (as duas rotinas e a função são `SQL SECURITY INVOKER`, então não elevam privilégio). Os triggers rodam com o privilégio do definidor (root) e gravam na tabela restrita sem que as roles tenham acesso; nenhuma view a referencia.

## Identidade

- Conta MySQL individual = `usuario.login` (sem `@`, no máximo 32 caracteres no MySQL 8.0). Views e `usr_*` usam `USER()`.
- As `usr_*` **não têm parâmetro de ID**: o dono é sempre a conta conectada; o arquivo é localizado pelo nome entre os arquivos ativos do próprio usuário (erro se houver 0 ou mais de 1).
- As `sp_*` (que recebem IDs) **não** recebem `EXECUTE` de usuário/empresa.
- `Conta_usuários` e `Remover_acessos` validam, além da role, a conta autenticada (`CURRENT_USER()`): só root ou conta cujo nome é o login de alguém em `administrador`. Uma conta com `PapelAdm` fora de `administrador` é rejeitada.
- Contas anônimas (`''@host`) permitiriam falsificar `USER()`; o script 08 lista-as e elas devem ser removidas.
- Contas de aplicação não podem ter `CREATE USER`, `ROLE_ADMIN`, `FILE`, `SUPER`, `GRANT OPTION` nem acesso a `mysql.*`.
- Criar o registro em `usuario` não cria a conta MySQL. Cada conta precisa de:
  `CREATE USER`, `GRANT PapelX TO`, **`SET DEFAULT ROLE PapelX TO`** (sem isso a role não fica ativa no login).

## Decisões de interpretação

1. **Verificar_atividades**: sem parâmetro; `UPDATE` de toda a tabela para `CURRENT_DATE()` (o `03` foi corrigido no lugar; bancos que já rodaram a versão antiga: `DROP PROCEDURE Verificar_atividades` e recriar). A prioridade não muda. Chamá-la apaga, na prática, a distinção de inatividade existente — é o que o enunciado pede.
2. **Conta_usuários**: segue `fn_pode_acessar`: PRIVADO = 1; COMPARTILHADO = dono + destinatários distintos; PUBLICO = todos os usuários cadastrados. Devolve o resultado na coluna `total_usuarios`. Erro se o arquivo não existe ou foi removido.
3. **Remover_acessos**: apaga todas as linhas de `compartilhamento` do arquivo (o dono nunca tem linha ali; seu acesso vem de `id_dono`) e, se o arquivo era PUBLICO/COMPARTILHADO, passa a PRIVADO — senão terceiros continuariam com acesso. Não altera `ultima_modificacao` nem histórico (não há tipo de operação para isso).
4. **Chavear**: mantida como estava (alterna a prioridade; erro se não há registro de atividade).
5. **fn_arquivo_inativo(id)**: `TINYINT(1)`; 1 se `DATEDIFF(CURDATE(), ultima_versao) > 100`; 0 caso contrário e **0 se não há registro** (sem data registrada não há como afirmar inatividade; não se usa outra fonte).
6. **Safe_security**: `BEFORE INSERT` em `arquivo`; bloqueia pela **última** extensão do nome (ignorando maiúsculas e espaços/pontos finais) ou por `tipo` (extensão ou MIME de executável). Lista: exe, com, bat, cmd, msi, msp, scr, pif, cpl, jar, vbs, vbe, wsf, wsh, ps1, sh, bash, run, apk, elf. `relatorio.exe.txt` e `execucao.docx` passam; `foto.jpg.exe` não. **Extra**: `Safe_security_update` impede o desvio por renomeação, e só age quando nome/tipo mudam. Limite: não analisa o conteúdo do arquivo.
7. **Registrar_operacao**: `AFTER INSERT` em `operacao_arquivo` (qualquer tipo de operação); cria o registro (prioridade padrão) ou atualiza `ultima_versao` para `GREATEST(atual, data da operação)`; a prioridade é preservada.
8. **Atualizar_acesso** (enunciado ambíguo): ao surgir uma linha em `compartilhamento` (usuário ganha acesso a um arquivo), o registro do arquivo em `atividades_recentes` é criado/atualizado com a data do compartilhamento, tratada como atividade. `Atualizar_acesso_update` cobre troca de destinatário/arquivo. Acesso por PUBLICO não dispara (não há evento por usuário).
9. **PapelUsuario "atualiza arquivos com permissão"**: interpretado de forma conservadora como arquivos **de sua propriedade** (regra já aplicada por `sp_atualizar_arquivo`); permitir edição de arquivos públicos/compartilhados por terceiros não está no modelo. Arquivo compartilhado/público é só leitura para o destinatário.
10. Usuário comum não remove arquivo e não compartilha (o enunciado lista só selecionar, inserir e atualizar); isso é feito por PapelAdm.

## Limitações conhecidas

- PapelAdm tem `INSERT/UPDATE/DELETE` direto em `arquivo` (exigido pelo enunciado), portanto pode contornar cota e auditoria das `sp_*`; `Safe_security` continua valendo. Excluir um arquivo apaga em cascata seu registro em `atividades_recentes` (FK do script 02).
- Admin também lê `usuario.senha_hash` (acesso total a tabelas). As views das demais roles não a expõem.
- `fn_pode_acessar` e as views usam login como texto: renomear `usuario.login` muda a identidade; só admin pode fazê-lo.
- Nenhum acesso a `atividades_recentes` é possível pelas roles, mas escrever em `arquivo`/`operacao_arquivo`/`compartilhamento` provoca escrita indireta pelos triggers (comportamento exigido).

## Python

`perfil.detectar()` lê `CURRENT_ROLE()`/`CURRENT_USER()` e `main.py` mostra o menu correspondente: admin/root (CRUD anterior + módulo **acessos**; root também o módulo **atividades**), usuário (`webdriver/usuario.py`) e empresa (`webdriver/empresa.py`). `webdriver/administracao.py` encapsula as procedures. O perfil não é escolhido pelo operador; a segurança continua no MySQL. O CRUD de admin (`repositorio`, `arquivos`, `planos`, `historicos`) funciona com o PapelAdm sem alterações.

## Testes

```console
python -m unittest discover -s tests -v                       # unitários (sem MySQL); integração é ignorada
WEBDRIVER_TEST_MYSQL=1 python -m unittest discover -s tests -v  # inclui tests/test_seguranca_mysql.py
```

A integração exige MySQL 8.0.16+, cliente `mysql` e conta root (variáveis `WEBDRIVER_TEST_ROOT_USER`, `WEBDRIVER_TEST_ROOT_PASSWORD`, `WEBDRIVER_TEST_SOCKET` ou `WEBDRIVER_TEST_HOST`). Cria o banco `webdriver_teste`, roles `TstPapel*` e contas `t*`, e remove tudo ao final; o banco `webdriver` não é tocado. Cobre os 14 itens da lista de validação.
