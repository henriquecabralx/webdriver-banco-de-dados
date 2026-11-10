CREATE DATABASE IF NOT EXISTS webdriver CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE webdriver;

CREATE TABLE plano (
 id_plano BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 nome VARCHAR(100) NOT NULL,
 duracao_dias INT UNSIGNED NOT NULL,
 espaco_por_usuario_bytes BIGINT UNSIGNED NOT NULL,
 CONSTRAINT ck_plano_duracao CHECK (duracao_dias > 0),
 CONSTRAINT ck_plano_espaco CHECK (espaco_por_usuario_bytes > 0)
) ENGINE=InnoDB;

CREATE TABLE instituicao (
 id_instituicao BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 nome VARCHAR(150) NOT NULL,
 causa_social TEXT NOT NULL,
 endereco TEXT NOT NULL,
 id_plano BIGINT UNSIGNED NOT NULL,
 data_aquisicao DATE NOT NULL,
 CONSTRAINT fk_inst_plano FOREIGN KEY (id_plano) REFERENCES plano(id_plano) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE usuario (
 id_usuario BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 nome VARCHAR(150) NOT NULL,
 data_nascimento DATE NULL,
 login VARCHAR(80) NOT NULL UNIQUE,
 senha_hash VARCHAR(255) NOT NULL,
 data_ingresso DATE NOT NULL,
 email VARCHAR(254) NOT NULL UNIQUE,
 id_instituicao BIGINT UNSIGNED NOT NULL,
 CONSTRAINT fk_usuario_inst FOREIGN KEY (id_instituicao) REFERENCES instituicao(id_instituicao) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE administrador (
 id_administrador BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 id_usuario BIGINT UNSIGNED NOT NULL UNIQUE,
 CONSTRAINT fk_admin_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE arquivo (
 id_arquivo BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 id_dono BIGINT UNSIGNED NOT NULL,
 nome VARCHAR(255) NOT NULL,
 tipo VARCHAR(120) NOT NULL,
 permissao_acesso ENUM('PRIVADO','COMPARTILHADO','PUBLICO') NOT NULL DEFAULT 'PRIVADO',
 tamanho_bytes BIGINT UNSIGNED NOT NULL,
 ultima_modificacao DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 localizacao TEXT NOT NULL,
 url TEXT NOT NULL,
 excluido_em DATETIME(6) NULL,
 UNIQUE KEY uq_arquivo_dono (id_arquivo,id_dono),
 INDEX idx_arquivo_dono_ativo (id_dono,excluido_em),
 CONSTRAINT fk_arquivo_dono FOREIGN KEY (id_dono) REFERENCES usuario(id_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE compartilhamento (
 id_arquivo BIGINT UNSIGNED NOT NULL,
 id_dono BIGINT UNSIGNED NOT NULL,
 id_compartilhado BIGINT UNSIGNED NOT NULL,
 data_compartilhamento DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 PRIMARY KEY (id_arquivo,id_compartilhado),
 INDEX idx_comp_destino (id_compartilhado),
 CONSTRAINT ck_comp_diferentes CHECK (id_dono <> id_compartilhado),
 CONSTRAINT fk_comp_arquivo_dono FOREIGN KEY (id_arquivo,id_dono) REFERENCES arquivo(id_arquivo,id_dono) ON DELETE RESTRICT,
 CONSTRAINT fk_comp_destino FOREIGN KEY (id_compartilhado) REFERENCES usuario(id_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE comentario (
 id_comentario BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 id_arquivo BIGINT UNSIGNED NOT NULL,
 id_usuario BIGINT UNSIGNED NOT NULL,
 conteudo TEXT NOT NULL,
 data_hora DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 INDEX idx_coment_arquivo (id_arquivo),
 CONSTRAINT fk_coment_arquivo FOREIGN KEY (id_arquivo) REFERENCES arquivo(id_arquivo) ON DELETE RESTRICT,
 CONSTRAINT fk_coment_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE operacao_arquivo (
 id_operacao BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 id_arquivo BIGINT UNSIGNED NOT NULL,
 id_usuario BIGINT UNSIGNED NOT NULL,
 tipo_operacao ENUM('CARREGAR','ATUALIZAR','REMOVER') NOT NULL,
 data_hora DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 INDEX idx_op_arquivo_data (id_arquivo,data_hora),
 CONSTRAINT fk_op_arquivo FOREIGN KEY (id_arquivo) REFERENCES arquivo(id_arquivo) ON DELETE RESTRICT,
 CONSTRAINT fk_op_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE versionamento (
 id_versionamento BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 id_arquivo BIGINT UNSIGNED NOT NULL,
 id_usuario BIGINT UNSIGNED NOT NULL,
 data_hora DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 operacao ENUM('CARREGAR','ATUALIZAR','REMOVER') NOT NULL,
 conteudo_mudado TEXT NOT NULL,
 INDEX idx_versao_arquivo_data (id_arquivo,data_hora),
 CONSTRAINT fk_versao_arquivo FOREIGN KEY (id_arquivo) REFERENCES arquivo(id_arquivo) ON DELETE RESTRICT,
 CONSTRAINT fk_versao_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE suporte (
 id_suporte BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 id_usuario BIGINT UNSIGNED NOT NULL,
 id_arquivo BIGINT UNSIGNED NULL,
 dia DATE NOT NULL,
 hora TIME NOT NULL,
 descricao TEXT NOT NULL,
 CONSTRAINT fk_suporte_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT,
 CONSTRAINT fk_suporte_arquivo FOREIGN KEY (id_arquivo) REFERENCES arquivo(id_arquivo) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE suporte_adm (
 id_suporte BIGINT UNSIGNED NOT NULL,
 id_administrador BIGINT UNSIGNED NOT NULL,
 PRIMARY KEY (id_suporte,id_administrador),
 CONSTRAINT fk_sa_suporte FOREIGN KEY (id_suporte) REFERENCES suporte(id_suporte) ON DELETE CASCADE,
 CONSTRAINT fk_sa_admin FOREIGN KEY (id_administrador) REFERENCES administrador(id_administrador) ON DELETE RESTRICT
) ENGINE=InnoDB;

DELIMITER $$
CREATE FUNCTION fn_pode_acessar(p_usuario BIGINT UNSIGNED, p_arquivo BIGINT UNSIGNED)
RETURNS TINYINT READS SQL DATA
BEGIN
 DECLARE v_ok INT DEFAULT 0;
 SELECT COUNT(*) INTO v_ok FROM arquivo a
 WHERE a.id_arquivo=p_arquivo AND a.excluido_em IS NULL AND
 (a.id_dono=p_usuario OR a.permissao_acesso='PUBLICO' OR
  (a.permissao_acesso='COMPARTILHADO' AND EXISTS
   (SELECT 1 FROM compartilhamento c WHERE c.id_arquivo=a.id_arquivo AND c.id_compartilhado=p_usuario)));
 RETURN IF(v_ok>0,1,0);
END$$

CREATE TRIGGER trg_comp_bi BEFORE INSERT ON compartilhamento FOR EACH ROW
BEGIN
 IF NOT EXISTS (SELECT 1 FROM arquivo WHERE id_arquivo=NEW.id_arquivo AND id_dono=NEW.id_dono AND excluido_em IS NULL) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Compartilhamento: arquivo inexistente, excluido ou dono incorreto';
 END IF;
END$$
CREATE TRIGGER trg_comp_bu BEFORE UPDATE ON compartilhamento FOR EACH ROW
BEGIN
 IF NOT EXISTS (SELECT 1 FROM arquivo WHERE id_arquivo=NEW.id_arquivo AND id_dono=NEW.id_dono AND excluido_em IS NULL) THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Compartilhamento invalido';
 END IF;
END$$
CREATE TRIGGER trg_coment_bi BEFORE INSERT ON comentario FOR EACH ROW
BEGIN
 IF fn_pode_acessar(NEW.id_usuario,NEW.id_arquivo)=0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Comentario: usuario sem acesso ao arquivo';
 END IF;
END$$
CREATE TRIGGER trg_coment_bu BEFORE UPDATE ON comentario FOR EACH ROW
BEGIN
 IF fn_pode_acessar(NEW.id_usuario,NEW.id_arquivo)=0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Comentario: usuario sem acesso ao arquivo';
 END IF;
END$$
CREATE TRIGGER trg_suporte_bi BEFORE INSERT ON suporte FOR EACH ROW
BEGIN
 IF NEW.id_arquivo IS NOT NULL AND fn_pode_acessar(NEW.id_usuario,NEW.id_arquivo)=0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Suporte: solicitante sem acesso ao arquivo';
 END IF;
END$$
CREATE TRIGGER trg_suporte_bu BEFORE UPDATE ON suporte FOR EACH ROW
BEGIN
 IF NEW.id_arquivo IS NOT NULL AND fn_pode_acessar(NEW.id_usuario,NEW.id_arquivo)=0 THEN
  SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Suporte: solicitante sem acesso ao arquivo';
 END IF;
END$$

CREATE TRIGGER trg_plano_bu BEFORE UPDATE ON plano FOR EACH ROW
BEGIN
 IF NEW.espaco_por_usuario_bytes < OLD.espaco_por_usuario_bytes AND EXISTS (
   SELECT 1 FROM instituicao i JOIN usuario u ON u.id_instituicao=i.id_instituicao
   JOIN arquivo a ON a.id_dono=u.id_usuario AND a.excluido_em IS NULL
   WHERE i.id_plano=OLD.id_plano GROUP BY u.id_usuario
   HAVING SUM(a.tamanho_bytes)>NEW.espaco_por_usuario_bytes
 ) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reducao de plano excede armazenamento de usuario'; END IF;
END$$
CREATE TRIGGER trg_instituicao_bu BEFORE UPDATE ON instituicao FOR EACH ROW
BEGIN
 IF NEW.id_plano<>OLD.id_plano AND EXISTS (
   SELECT 1 FROM usuario u JOIN arquivo a ON a.id_dono=u.id_usuario AND a.excluido_em IS NULL
   JOIN plano p ON p.id_plano=NEW.id_plano
   WHERE u.id_instituicao=OLD.id_instituicao GROUP BY u.id_usuario,p.espaco_por_usuario_bytes
   HAVING SUM(a.tamanho_bytes)>p.espaco_por_usuario_bytes
 ) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Novo plano insuficiente para arquivos existentes'; END IF;
END$$
CREATE TRIGGER trg_usuario_bu BEFORE UPDATE ON usuario FOR EACH ROW
BEGIN
 IF NEW.id_instituicao<>OLD.id_instituicao AND
 (SELECT COALESCE(SUM(tamanho_bytes),0) FROM arquivo WHERE id_dono=OLD.id_usuario AND excluido_em IS NULL) >
 (SELECT p.espaco_por_usuario_bytes FROM instituicao i JOIN plano p ON p.id_plano=i.id_plano WHERE i.id_instituicao=NEW.id_instituicao)
 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Instituicao destino nao comporta os arquivos'; END IF;
END$$

CREATE PROCEDURE sp_carregar_arquivo(
 IN p_dono BIGINT UNSIGNED, IN p_nome VARCHAR(255), IN p_tipo VARCHAR(120),
 IN p_permissao VARCHAR(20), IN p_tamanho BIGINT UNSIGNED,
 IN p_localizacao TEXT, IN p_url TEXT, OUT p_id BIGINT UNSIGNED)
BEGIN
 DECLARE v_limite BIGINT UNSIGNED DEFAULT NULL;
 DECLARE v_usado DECIMAL(30,0);
 DECLARE v_instituicao BIGINT UNSIGNED DEFAULT NULL;
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 SELECT id_instituicao INTO v_instituicao FROM usuario WHERE id_usuario=p_dono FOR UPDATE;
 IF v_instituicao IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Usuario inexistente'; END IF;
 SELECT p.espaco_por_usuario_bytes INTO v_limite FROM instituicao i JOIN plano p ON p.id_plano=i.id_plano WHERE i.id_instituicao=v_instituicao;
 SELECT COALESCE(SUM(tamanho_bytes),0) INTO v_usado FROM arquivo WHERE id_dono=p_dono AND excluido_em IS NULL;
 IF v_limite IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Plano inexistente'; END IF;
 IF v_usado+p_tamanho>v_limite THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Limite de armazenamento excedido'; END IF;
 INSERT INTO arquivo(id_dono,nome,tipo,permissao_acesso,tamanho_bytes,localizacao,url)
 VALUES(p_dono,p_nome,p_tipo,p_permissao,p_tamanho,p_localizacao,p_url);
 SET p_id=LAST_INSERT_ID();
 INSERT INTO operacao_arquivo(id_arquivo,id_usuario,tipo_operacao) VALUES(p_id,p_dono,'CARREGAR');
 INSERT INTO versionamento(id_arquivo,id_usuario,operacao,conteudo_mudado)
 VALUES(p_id,p_dono,'CARREGAR',CAST(JSON_OBJECT('depois',JSON_OBJECT('nome',p_nome,'tipo',p_tipo,'permissao',p_permissao,'tamanho_bytes',p_tamanho,'localizacao',p_localizacao,'url',p_url)) AS CHAR));
 COMMIT;
END$$

CREATE PROCEDURE sp_atualizar_arquivo(
 IN p_id BIGINT UNSIGNED, IN p_usuario BIGINT UNSIGNED,
 IN p_nome VARCHAR(255), IN p_tipo VARCHAR(120),
 IN p_permissao VARCHAR(20), IN p_tamanho BIGINT UNSIGNED,
 IN p_localizacao TEXT, IN p_url TEXT)
BEGIN
 DECLARE v_dono BIGINT UNSIGNED DEFAULT NULL;
 DECLARE v_antigo BIGINT UNSIGNED DEFAULT NULL;
 DECLARE v_antes LONGTEXT;
 DECLARE v_limite BIGINT UNSIGNED DEFAULT NULL;
 DECLARE v_usado DECIMAL(30,0);
 DECLARE v_instituicao BIGINT UNSIGNED DEFAULT NULL;
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 SELECT id_instituicao INTO v_instituicao FROM usuario WHERE id_usuario=p_usuario FOR UPDATE;
 SELECT id_dono,tamanho_bytes,CAST(JSON_OBJECT('nome',nome,'tipo',tipo,'permissao',permissao_acesso,'tamanho_bytes',tamanho_bytes,'localizacao',localizacao,'url',url) AS CHAR) INTO v_dono,v_antigo,v_antes FROM arquivo WHERE id_arquivo=p_id AND excluido_em IS NULL FOR UPDATE;
 IF v_dono IS NULL OR v_dono<>p_usuario THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Somente o dono pode atualizar arquivo ativo'; END IF;
 SELECT p.espaco_por_usuario_bytes INTO v_limite FROM instituicao i JOIN plano p ON p.id_plano=i.id_plano WHERE i.id_instituicao=v_instituicao;
 SELECT COALESCE(SUM(tamanho_bytes),0) INTO v_usado FROM arquivo WHERE id_dono=p_usuario AND excluido_em IS NULL;
 IF v_limite IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Plano inexistente'; END IF;
 IF v_usado-v_antigo+p_tamanho>v_limite THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Limite de armazenamento excedido'; END IF;
 UPDATE arquivo SET nome=p_nome,tipo=p_tipo,permissao_acesso=p_permissao,tamanho_bytes=p_tamanho,
 localizacao=p_localizacao,url=p_url,ultima_modificacao=CURRENT_TIMESTAMP(6) WHERE id_arquivo=p_id;
 INSERT INTO operacao_arquivo(id_arquivo,id_usuario,tipo_operacao) VALUES(p_id,p_usuario,'ATUALIZAR');
 INSERT INTO versionamento(id_arquivo,id_usuario,operacao,conteudo_mudado)
 VALUES(p_id,p_usuario,'ATUALIZAR',CAST(JSON_OBJECT('antes',JSON_EXTRACT(v_antes,'$'),'depois',JSON_OBJECT('nome',p_nome,'tipo',p_tipo,'permissao',p_permissao,'tamanho_bytes',p_tamanho,'localizacao',p_localizacao,'url',p_url)) AS CHAR));
 COMMIT;
END$$

CREATE PROCEDURE sp_remover_arquivo(IN p_id BIGINT UNSIGNED, IN p_usuario BIGINT UNSIGNED)
BEGIN
 DECLARE v_dono BIGINT UNSIGNED DEFAULT NULL;
 DECLARE v_antes LONGTEXT;
 DECLARE v_instituicao BIGINT UNSIGNED DEFAULT NULL;
 DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;
 START TRANSACTION;
 SELECT id_instituicao INTO v_instituicao FROM usuario WHERE id_usuario=p_usuario FOR UPDATE;
 SELECT id_dono,CAST(JSON_OBJECT('nome',nome,'tipo',tipo,'permissao',permissao_acesso,'tamanho_bytes',tamanho_bytes,'localizacao',localizacao,'url',url) AS CHAR) INTO v_dono,v_antes FROM arquivo WHERE id_arquivo=p_id AND excluido_em IS NULL FOR UPDATE;
 IF v_dono IS NULL OR v_dono<>p_usuario THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Somente o dono pode remover arquivo ativo'; END IF;
 UPDATE arquivo SET excluido_em=CURRENT_TIMESTAMP(6),ultima_modificacao=CURRENT_TIMESTAMP(6) WHERE id_arquivo=p_id;
 INSERT INTO operacao_arquivo(id_arquivo,id_usuario,tipo_operacao) VALUES(p_id,p_usuario,'REMOVER');
 INSERT INTO versionamento(id_arquivo,id_usuario,operacao,conteudo_mudado)
 VALUES(p_id,p_usuario,'REMOVER',CAST(JSON_OBJECT('antes',JSON_EXTRACT(v_antes,'$'),'exclusao','logica') AS CHAR));
 COMMIT;
END$$
DELIMITER ;
