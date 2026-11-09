# Pessoa 4 — Segundo commit: roles e permissões

## Entrega

`sql/08-roles-permissoes.sql` cria PapelUsuario, PapelEmpresa e PapelAdm e concede os privilégios por objeto.

| Role | Concedido | Negado |
|---|---|---|
| PapelUsuario | SELECT em vw_arquivos_autorizados e vw_historico_usuario; EXECUTE em usr_carregar_arquivo e usr_atualizar_arquivo | Tabelas, procedures sp_* (recebem IDs), alteração do histórico, atividades_recentes |
| PapelEmpresa | SELECT em vw_empresa_usuarios e vw_empresa_arquivos | Qualquer escrita, outras instituições, tabelas, rotinas |
| PapelAdm | SELECT, INSERT, UPDATE e DELETE em todas as tabelas, exceto atividades_recentes; SELECT nas 11 views vw_admin_*; EXECUTE em sp_*, Conta_usuários, Remover_acessos e fn_pode_acessar | atividades_recentes, Verificar_atividades, Chavear, fn_arquivo_inativo |

Não há GRANT em webdriver.* nem em *.*. A tabela atividades_recentes e as rotinas que a usam permanecem exclusivas do root. Verificar_atividades, Chavear e fn_arquivo_inativo são SQL SECURITY INVOKER e não emprestam privilégios. Os triggers executam com o privilégio do definidor e gravam na tabela sem que as roles tenham acesso. Nenhuma view a referencia.

O script zera os privilégios das roles antes de concedê-los, e pode ser reexecutado. Ele também lista contas anônimas do servidor; o resultado deve vir vazio.

## Segurança da identidade

- As views e as procedures usr_* usam USER(), que é o nome de conta MySQL individual igual a usuario.login. Uma conta anônima poderia falsificar esse nome; por isso deve ser removida com `DROP USER ''@'host'`.
- Conta_usuários e Remover_acessos validam também a conta autenticada (CURRENT_USER()), além da role: só root ou uma conta cujo nome é o login de alguém em administrador. Uma conta com PapelAdm fora da tabela administrador é recusada.
- Contas da aplicação não podem ter CREATE USER, ROLE_ADMIN, FILE, SUPER, GRANT OPTION nem acesso ao schema mysql.
- PapelUsuario atualiza apenas arquivos de sua propriedade, regra já aplicada por sp_atualizar_arquivo. Arquivos públicos ou compartilhados são somente leitura para o destinatário. O usuário não remove arquivos nem cria compartilhamentos, pois o enunciado lista apenas selecionar, inserir e atualizar.

## Como executar

1. Envie as pastas sql e docs para a raiz do repositório, mesclando as existentes.
2. Confirme que os scripts 01 a 07 já foram executados.
3. Conecte como root e execute sql/08-roles-permissoes.sql.
4. Para cada pessoa, crie a conta e ative a role. Sem SET DEFAULT ROLE a role não fica ativa no login:

```sql
CREATE USER 'maria'@'localhost' IDENTIFIED BY 'senha-forte';
GRANT PapelUsuario TO 'maria'@'localhost';
SET DEFAULT ROLE PapelUsuario TO 'maria'@'localhost';
```

O nome da conta deve ser igual a usuario.login, sem @ e com no máximo 32 caracteres (limite do MySQL 8.0). Criar a linha em usuario não cria a conta MySQL.

## Verificação no MySQL

Como root:

```sql
SHOW GRANTS FOR PapelUsuario;
SHOW GRANTS FOR PapelEmpresa;
SHOW GRANTS FOR PapelAdm;
```

Confira que nenhum grant menciona atividades_recentes, Verificar_atividades, Chavear ou fn_arquivo_inativo e que não há privilégio em *.*.

Com contas individuais, confira: o usuário A não vê o arquivo privado do usuário B; vê os próprios e os compartilhados com ele; recebe erro ao fazer UPDATE direto em arquivo ou ao chamar sp_atualizar_arquivo; não altera o histórico. A empresa A não vê dados da B e recebe erro em qualquer escrita. O administrador cadastrado insere, atualiza, exclui e executa Conta_usuários e Remover_acessos; o usuário comum recebe erro nelas. Em todas as contas, `SELECT * FROM atividades_recentes` deve ser negado.

Execução realizada: estas verificações foram automatizadas em tests/test_seguranca_mysql.py (commit 3) e passaram em MySQL 8.0.46. Não foram executadas no MySQL Workbench.

## Limites conhecidos

PapelAdm possui escrita direta em arquivo, exigida pelo enunciado, e por isso pode contornar a cota e a auditoria das sp_*. Safe_security continua valendo. Excluir um arquivo apaga em cascata seu registro em atividades_recentes (FK do commit anterior da Pessoa 2). O administrador também lê usuario.senha_hash, por ter acesso à tabela; as views das demais roles não a expõem.

## Commit no GitHub

Arquivos: sql/08-roles-permissoes.sql e docs/pessoa4-commit2.md.

Título: `Adiciona roles PapelUsuario, PapelEmpresa e PapelAdm`

Descrição: `Concede privilégios por objeto às três roles, sem GRANT amplo, mantendo atividades_recentes exclusiva do root. Usuários e empresas acessam apenas views e procedures que identificam a conta conectada. Documenta a criação de contas e SET DEFAULT ROLE.`
