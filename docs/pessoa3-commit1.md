# Pessoa 3 — Primeiro commit: views do usuário

## Entrega

| View | Conteúdo |
|---|---|
| vw_arquivos_autorizados | Arquivos ativos próprios, públicos ou compartilhados com o usuário conectado |
| vw_historico_usuario | Operações realizadas pelo próprio usuário, inclusive de arquivos removidos |

Nenhuma das views expõe IDs nem senhas. A interpretação de histórico adotada é a das próprias operações do usuário, evitando expor a atividade de terceiros. As views são de consulta e não alteram o CRUD Python nesta entrega.

## Identificação do usuário: configuração necessária

O schema atual não associa a conexão MySQL à identidade do aplicativo. Para esta demonstração de permissões no banco, adotamos uma conta MySQL individual por usuário, com nome exatamente igual a usuario.login. As views leem o nome da conexão por USER(); não usam variáveis de sessão editáveis como @id_usuario nem CURRENT_USER(), que em view DEFINER identificaria o criador.

Exemplo: usuario.login = ana precisa ser consultado pela conta MySQL ana, com autenticação própria. Não basta inserir ana na tabela usuario. Os logins dessa demonstração não devem conter @; contas com o mesmo nome em hosts diferentes devem representar a mesma pessoa. A comparação de login é sensível a maiúsculas/minúsculas.

Não usar contas MySQL anônimas, proxy nem conta compartilhada por todos. O responsável pelas contas/roles deve validar essas condições antes de liberar as views. USER() representa o nome de conexão e não substitui uma política de autenticação bem configurada. Um login sem correspondência na tabela usuario retorna zero registros.

O Python atual usa uma conta compartilhada de administração configurada em config.ini; este commit não o transforma em aplicação com login. É possível testar as views no Workbench usando conexões individuais. A integração do aplicativo com autenticação e operações autorizadas permanece necessária para usar esses filtros no fluxo Python.

## Instalação

1. Envie as pastas sql e docs deste pacote para a raiz do repositório, mesclando as existentes.
2. Conecte como root no Workbench ao banco onde o modelo físico já foi executado.
3. Execute apenas sql/04-views-usuario.sql.

O script cria as views uma vez; não substitui views já existentes. O definidor será a conta criadora. Os privilégios nas tabelas base são usados pelo definidor; o usuário receberá apenas SELECT nas views na etapa de roles.

## Permissões e escrita

ALGORITHM TEMPTABLE torna as duas views não atualizáveis. Os GRANTs devem conceder apenas SELECT nelas, sem expor as tabelas base. Isso resolve esta entrega de consulta; não concede ainda os direitos de inserção/atualização previstos para PapelUsuario. Essas operações precisam de rotinas com validação de identidade, além da configuração das roles. Não liberar INSERT/UPDATE/SELECT genérico em arquivo para contornar o filtro: permissões diretas não herdam o filtro da view.

As procedures atuais de arquivos recebem IDs por parâmetro e não autenticam quem os informa. Portanto, não basta conceder EXECUTE dessas procedures a contas comuns para afirmar que a autorização da Parte 2 está completa. O integrante responsável por permissões deverá resolver essa integração.

## Verificação no MySQL

Como root:

```sql
SHOW COLUMNS FROM webdriver.vw_arquivos_autorizados;
SHOW COLUMNS FROM webdriver.vw_historico_usuario;
SELECT TABLE_NAME, IS_UPDATABLE
FROM information_schema.VIEWS
WHERE TABLE_SCHEMA='webdriver'
  AND TABLE_NAME IN ('vw_arquivos_autorizados','vw_historico_usuario');
```

Confirme ausência de IDs e IS_UPDATABLE = NO nas duas views.

Após configurar contas e conceder SELECT nas views, crie dados de teste por root: dois usuários, um arquivo privado de cada um, um público e um compartilhado com convite para apenas um deles. Conecte com cada usuário e consulte:

```sql
SELECT USER();
SELECT * FROM webdriver.vw_arquivos_autorizados;
SELECT * FROM webdriver.vw_historico_usuario;
```

Confirme: não aparece o privado do outro usuário; arquivo compartilhado exige convite; público aparece; removido não aparece na view de arquivos; histórico só mostra operações próprias. Remova o convite como root e consulte novamente: o acesso compartilhado deve desaparecer. Uma conta sem usuário correspondente deve retornar zero linhas. UPDATE/INSERT/DELETE nas views e SELECT direto nas bases devem ser recusados.

Testes integrados ainda não executados: não há servidor MySQL disponível nesta preparação. O SQL foi conferido estaticamente contra os campos do modelo físico.

## Commit

Título: `Adiciona views de arquivos autorizados e histórico do usuário`

Descrição: `Cria duas views de consulta sem IDs, filtradas pela conta MySQL individual. Inclui regras de acesso a arquivos e histórico próprio, requisitos de identificação e roteiro de teste.`

Referências oficiais:

- https://dev.mysql.com/doc/refman/8.0/en/create-view.html
- https://dev.mysql.com/doc/refman/8.0/en/information-functions.html
- https://dev.mysql.com/doc/refman/8.0/en/view-updatability.html
