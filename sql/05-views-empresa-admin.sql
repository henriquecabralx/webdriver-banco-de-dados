USE webdriver;

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_empresa_usuarios AS
SELECT u.nome, u.login, u.email, u.data_ingresso, i.nome AS instituicao
FROM usuario u INNER JOIN instituicao i ON i.id_instituicao=u.id_instituicao
WHERE EXISTS (SELECT 1 FROM usuario identidade
WHERE identidade.id_instituicao=u.id_instituicao AND BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_empresa_arquivos AS
SELECT a.nome AS nome_arquivo, u.login AS proprietario, i.nome AS instituicao,
a.tipo, a.permissao_acesso, a.tamanho_bytes, a.ultima_modificacao, a.localizacao, a.url
FROM arquivo a INNER JOIN usuario u ON u.id_usuario=a.id_dono
INNER JOIN instituicao i ON i.id_instituicao=u.id_instituicao
WHERE a.excluido_em IS NULL AND EXISTS (SELECT 1 FROM usuario identidade
WHERE identidade.id_instituicao=u.id_instituicao AND BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_usuarios AS
SELECT nome,login,email,data_ingresso,data_nascimento FROM usuario
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_arquivos AS
SELECT nome,tipo,permissao_acesso,tamanho_bytes,ultima_modificacao,localizacao,url,excluido_em FROM arquivo
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_planos AS
SELECT nome,duracao_dias,espaco_por_usuario_bytes FROM plano
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_instituicoes AS
SELECT nome,causa_social,endereco,data_aquisicao FROM instituicao
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_administradores AS
SELECT u.nome,u.login,u.email FROM administrador adm JOIN usuario u ON u.id_usuario=adm.id_usuario
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_compartilhamentos AS
SELECT a.nome AS arquivo,d.login AS dono,u.login AS destinatario,c.data_compartilhamento FROM compartilhamento c JOIN arquivo a ON a.id_arquivo=c.id_arquivo JOIN usuario d ON d.id_usuario=c.id_dono JOIN usuario u ON u.id_usuario=c.id_compartilhado
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_comentarios AS
SELECT a.nome AS arquivo,u.login AS autor,c.conteudo,c.data_hora FROM comentario c JOIN arquivo a ON a.id_arquivo=c.id_arquivo JOIN usuario u ON u.id_usuario=c.id_usuario
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_suporte AS
SELECT u.login AS solicitante,a.nome AS arquivo,s.dia,s.hora,s.descricao FROM suporte s JOIN usuario u ON u.id_usuario=s.id_usuario LEFT JOIN arquivo a ON a.id_arquivo=s.id_arquivo
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_atendimentos AS
SELECT s.descricao AS chamado,s.dia,s.hora,u.login AS administrador FROM suporte_adm sa JOIN suporte s ON s.id_suporte=sa.id_suporte JOIN administrador adm ON adm.id_administrador=sa.id_administrador JOIN usuario u ON u.id_usuario=adm.id_usuario
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_operacoes AS
SELECT a.nome AS arquivo,u.login AS autor,o.tipo_operacao,o.data_hora FROM operacao_arquivo o JOIN arquivo a ON a.id_arquivo=o.id_arquivo JOIN usuario u ON u.id_usuario=o.id_usuario
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

CREATE ALGORITHM = TEMPTABLE
SQL SECURITY DEFINER
VIEW vw_admin_versoes AS
SELECT a.nome AS arquivo,u.login AS autor,v.data_hora,v.operacao FROM versionamento v JOIN arquivo a ON a.id_arquivo=v.id_arquivo JOIN usuario u ON u.id_usuario=v.id_usuario
WHERE EXISTS (SELECT 1 FROM administrador adm INNER JOIN usuario identidade ON identidade.id_usuario = adm.id_usuario WHERE BINARY identidade.login = BINARY SUBSTRING_INDEX(USER(), '@', 1));

