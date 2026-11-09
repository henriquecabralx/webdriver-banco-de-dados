-- WebDriver | Parte 2 | Roles e privilegios
-- Pre-requisitos: 01 a 07 (GRANT em rotina exige que ela exista). Execute como root.
-- Reexecutavel: os privilegios das roles sao zerados e concedidos novamente.
-- NAO ha GRANT em webdriver.* nem em *.*: tudo e concedido por objeto, e atividades_recentes
-- e Verificar_atividades/Chavear/fn_arquivo_inativo nao sao concedidas a nenhuma role.
USE webdriver;

-- Identidade: views e usr_* usam USER() = usuario.login. Conta anonima ('') poderia aceitar
-- qualquer nome de login e falsificar essa identidade. O resultado abaixo deve vir VAZIO;
-- caso contrario execute DROP USER ''@'host' para cada linha.
SELECT user, host AS conta_anonima_remover FROM mysql.user WHERE user = '';

CREATE ROLE IF NOT EXISTS PapelUsuario, PapelEmpresa, PapelAdm;
REVOKE ALL PRIVILEGES, GRANT OPTION FROM PapelUsuario, PapelEmpresa, PapelAdm;

-- PapelUsuario: somente views filtradas pela conta conectada (sem IDs) e procedures que
-- derivam a identidade da conta. Sem acesso direto a tabelas e sem EXECUTE nas sp_* com IDs.
GRANT SELECT ON webdriver.vw_arquivos_autorizados TO PapelUsuario;
GRANT SELECT ON webdriver.vw_historico_usuario TO PapelUsuario;
GRANT EXECUTE ON PROCEDURE webdriver.usr_carregar_arquivo TO PapelUsuario;
GRANT EXECUTE ON PROCEDURE webdriver.usr_atualizar_arquivo TO PapelUsuario;

-- PapelEmpresa: somente leitura das views da propria instituicao.
GRANT SELECT ON webdriver.vw_empresa_usuarios TO PapelEmpresa;
GRANT SELECT ON webdriver.vw_empresa_arquivos TO PapelEmpresa;

-- PapelAdm: CRUD em todas as tabelas, exceto atividades_recentes.
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.plano TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.instituicao TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.usuario TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.administrador TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.arquivo TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.compartilhamento TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.comentario TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.operacao_arquivo TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.versionamento TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.suporte TO PapelAdm;
GRANT SELECT, INSERT, UPDATE, DELETE ON webdriver.suporte_adm TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_usuarios TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_arquivos TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_planos TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_instituicoes TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_administradores TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_compartilhamentos TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_comentarios TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_suporte TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_atendimentos TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_operacoes TO PapelAdm;
GRANT SELECT ON webdriver.vw_admin_versoes TO PapelAdm;
GRANT EXECUTE ON PROCEDURE webdriver.sp_carregar_arquivo TO PapelAdm;
GRANT EXECUTE ON PROCEDURE webdriver.sp_atualizar_arquivo TO PapelAdm;
GRANT EXECUTE ON PROCEDURE webdriver.sp_remover_arquivo TO PapelAdm;
GRANT EXECUTE ON PROCEDURE webdriver.`Conta_usuários` TO PapelAdm;
GRANT EXECUTE ON PROCEDURE webdriver.Remover_acessos TO PapelAdm;
GRANT EXECUTE ON FUNCTION webdriver.fn_pode_acessar TO PapelAdm;

-- Atribuicao a contas individuais (conta MySQL = usuario.login, sem '@' no login).
-- A role precisa estar ATIVA no login, por isso SET DEFAULT ROLE e obrigatorio:
--   CREATE USER 'maria'@'localhost' IDENTIFIED BY '...';
--   GRANT PapelUsuario TO 'maria'@'localhost';
--   SET DEFAULT ROLE PapelUsuario TO 'maria'@'localhost';
-- Nunca conceda CREATE USER, ROLE_ADMIN, FILE, SUPER, GRANT OPTION ou acesso a mysql.* a essas contas.

SHOW GRANTS FOR PapelUsuario;
SHOW GRANTS FOR PapelEmpresa;
SHOW GRANTS FOR PapelAdm;
