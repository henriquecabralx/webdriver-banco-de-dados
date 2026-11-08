-- WebDriver | Pessoa 3 | Primeiro commit | MySQL 8.0
-- Execute como root apos 01-modelo-fisico.sql.
-- Contrato: cada usuario tem conta MySQL individual com nome igual a usuario.login.
-- Nao usar conta compartilhada, conta anonima ou autenticacao por proxy.
-- Logins dessa demonstracao nao devem conter @; usar o mesmo login por pessoa
-- em todos os hosts autorizados. Nenhum usuario da aplicacao pode alterar
-- login/vinculo de outras pessoas nem criar contas MySQL.
USE webdriver;

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_arquivos_autorizados AS
SELECT
    a.nome AS nome_arquivo,
    dono.login AS proprietario,
    a.tipo,
    a.permissao_acesso,
    a.tamanho_bytes,
    a.ultima_modificacao,
    a.localizacao,
    a.url
FROM arquivo a
INNER JOIN usuario dono ON dono.id_usuario = a.id_dono
INNER JOIN usuario solicitante
    ON BINARY solicitante.login = BINARY SUBSTRING_INDEX(USER(), '@', 1)
WHERE a.excluido_em IS NULL
  AND (
      a.id_dono = solicitante.id_usuario
      OR a.permissao_acesso = 'PUBLICO'
      OR (
          a.permissao_acesso = 'COMPARTILHADO'
          AND EXISTS (
              SELECT 1 FROM compartilhamento c
              WHERE c.id_arquivo = a.id_arquivo
                AND c.id_compartilhado = solicitante.id_usuario
          )
      )
  );

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_historico_usuario AS
SELECT
    a.nome AS nome_arquivo,
    dono.login AS proprietario,
    autor.login AS usuario_operacao,
    o.tipo_operacao,
    o.data_hora,
    CASE WHEN a.excluido_em IS NULL THEN 'ATIVO' ELSE 'REMOVIDO' END AS estado_arquivo
FROM operacao_arquivo o
INNER JOIN arquivo a ON a.id_arquivo = o.id_arquivo
INNER JOIN usuario dono ON dono.id_usuario = a.id_dono
INNER JOIN usuario autor ON autor.id_usuario = o.id_usuario
WHERE BINARY autor.login = BINARY SUBSTRING_INDEX(USER(), '@', 1);

-- Historico: neste pacote o usuario consulta suas proprias operacoes,
-- inclusive a remocao de seus arquivos; nao ve operacoes de outras pessoas.
-- IDs sao usados somente nos relacionamentos, nao nas colunas expostas.
-- TEMPTABLE torna as views nao atualizaveis.
-- O definidor e a conta que executar este script e deve continuar existente.
-- Nenhum acesso a atividades_recentes e exposto.
-- Os GRANTs nas views serao adicionados pelo integrante das roles.
-- Nao conceder acesso direto as tabelas base para contornar estas views.
-- Estas sao visoes de leitura; insercao/atualizacao autorizadas exigem
-- rotinas controladas e permissões proprias no trabalho de roles/integracao.
