USE webdriver;
SELECT user, host AS conta_anonima_remover FROM mysql.user WHERE user = '';

CREATE ROLE IF NOT EXISTS PapelUsuario, PapelEmpresa, PapelAdm;
REVOKE ALL PRIVILEGES, GRANT OPTION FROM PapelUsuario, PapelEmpresa, PapelAdm;
GRANT SELECT ON webdriver.vw_arquivos_autorizados TO PapelUsuario;
GRANT SELECT ON webdriver.vw_historico_usuario TO PapelUsuario;
GRANT EXECUTE ON PROCEDURE webdriver.usr_carregar_arquivo TO PapelUsuario;
GRANT EXECUTE ON PROCEDURE webdriver.usr_atualizar_arquivo TO PapelUsuario;

GRANT SELECT ON webdriver.vw_empresa_usuarios TO PapelEmpresa;
GRANT SELECT ON webdriver.vw_empresa_arquivos TO PapelEmpresa;

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

SHOW GRANTS FOR PapelUsuario;
SHOW GRANTS FOR PapelEmpresa;
SHOW GRANTS FOR PapelAdm;
