-- WebDriver | Parte 2 | Procedures de autorizacao
-- Pre-requisitos: 01 a 05. Execute como root (cliente com utf8mb4: o nome Conta_usuários tem acento).
-- Verificar_atividades e Chavear (03) permanecem restritas ao root.
USE webdriver;
DELIMITER $$

-- ADMINISTRATIVAS (SQL SECURITY INVOKER: usam os privilegios de quem chama).
-- Alem da role, validam a conta efetivamente autenticada (CURRENT_USER(), nao falsificavel):
-- root, ou conta cujo nome coincide com o login de um usuario presente em administrador.

CREATE PROCEDURE `Conta_usuários`(IN p_id_arquivo BIGINT UNSIGNED)
SQL SECURITY INVOKER
READS SQL DATA
BEGIN
    DECLARE v_permissao VARCHAR(20) DEFAULT NULL;
    DECLARE v_total BIGINT UNSIGNED DEFAULT 0;

    IF NOT (SUBSTRING_INDEX(CURRENT_USER(), '@', 1) = 'root' OR EXISTS (
        SELECT 1 FROM administrador adm INNER JOIN usuario u ON u.id_usuario = adm.id_usuario
        WHERE BINARY u.login = BINARY SUBSTRING_INDEX(CURRENT_USER(), '@', 1))) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Operacao restrita a administradores';
    END IF;
    IF p_id_arquivo IS NULL OR p_id_arquivo = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Informe um ID de arquivo positivo';
    END IF;

    SELECT permissao_acesso INTO v_permissao FROM arquivo
    WHERE id_arquivo = p_id_arquivo AND excluido_em IS NULL;
    IF v_permissao IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Arquivo inexistente ou removido';
    END IF;

    -- Mesmas regras de fn_pode_acessar: PUBLICO = todos os usuarios; COMPARTILHADO = dono +
    -- destinatarios distintos (dono nunca consta em compartilhamento: CHECK id_dono<>id_compartilhado);
    -- PRIVADO = somente o dono.
    IF v_permissao = 'PUBLICO' THEN
        SELECT COUNT(*) INTO v_total FROM usuario;
    ELSEIF v_permissao = 'COMPARTILHADO' THEN
        SELECT 1 + COUNT(DISTINCT id_compartilhado) INTO v_total FROM compartilhamento WHERE id_arquivo = p_id_arquivo;
    ELSE
        SET v_total = 1;
    END IF;
    SELECT v_total AS total_usuarios;
END$$

CREATE PROCEDURE Remover_acessos(IN p_id_arquivo BIGINT UNSIGNED)
SQL SECURITY INVOKER
MODIFIES SQL DATA
BEGIN
    DECLARE v_id BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_permissao VARCHAR(20) DEFAULT NULL;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;

    IF NOT (SUBSTRING_INDEX(CURRENT_USER(), '@', 1) = 'root' OR EXISTS (
        SELECT 1 FROM administrador adm INNER JOIN usuario u ON u.id_usuario = adm.id_usuario
        WHERE BINARY u.login = BINARY SUBSTRING_INDEX(CURRENT_USER(), '@', 1))) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Operacao restrita a administradores';
    END IF;
    IF p_id_arquivo IS NULL OR p_id_arquivo = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Informe um ID de arquivo positivo';
    END IF;

    START TRANSACTION;
    SELECT id_arquivo, permissao_acesso INTO v_id, v_permissao FROM arquivo
    WHERE id_arquivo = p_id_arquivo FOR UPDATE;
    IF v_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Arquivo inexistente';
    END IF;

    -- O dono nao possui linha em compartilhamento: seu acesso e preservado (arquivo.id_dono).
    DELETE FROM compartilhamento WHERE id_arquivo = p_id_arquivo;
    -- Arquivo PUBLICO/COMPARTILHADO continuaria acessivel a terceiros: passa a PRIVADO.
    -- ultima_modificacao, historico e versionamento nao sao alterados (nao ha tipo de operacao para isso).
    IF v_permissao <> 'PRIVADO' THEN
        UPDATE arquivo SET permissao_acesso = 'PRIVADO' WHERE id_arquivo = p_id_arquivo;
    END IF;
    COMMIT;
END$$

-- USUARIO COMUM (SQL SECURITY DEFINER). A identidade vem da conta MySQL conectada
-- (USER() = usuario.login); nao existe parametro de ID de usuario nem de arquivo.
-- O arquivo e localizado pelo nome entre os arquivos ATIVOS do proprio usuario.
-- As procedures sp_* continuam sem EXECUTE para as roles.

CREATE PROCEDURE usr_carregar_arquivo(
    IN p_nome VARCHAR(255), IN p_tipo VARCHAR(120), IN p_permissao VARCHAR(20),
    IN p_tamanho BIGINT UNSIGNED, IN p_localizacao TEXT, IN p_url TEXT)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_usuario BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_id BIGINT UNSIGNED DEFAULT NULL;
    SELECT id_usuario INTO v_usuario FROM usuario
    WHERE BINARY login = BINARY SUBSTRING_INDEX(USER(), '@', 1);
    IF v_usuario IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Conta MySQL sem usuario WebDriver correspondente';
    END IF;
    CALL sp_carregar_arquivo(v_usuario, p_nome, p_tipo, p_permissao, p_tamanho, p_localizacao, p_url, v_id);
END$$

CREATE PROCEDURE usr_atualizar_arquivo(
    IN p_nome_atual VARCHAR(255), IN p_nome VARCHAR(255), IN p_tipo VARCHAR(120),
    IN p_permissao VARCHAR(20), IN p_tamanho BIGINT UNSIGNED, IN p_localizacao TEXT, IN p_url TEXT)
SQL SECURITY DEFINER
MODIFIES SQL DATA
BEGIN
    DECLARE v_usuario BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_arquivo BIGINT UNSIGNED DEFAULT NULL;
    DECLARE v_qtd INT DEFAULT 0;
    SELECT id_usuario INTO v_usuario FROM usuario
    WHERE BINARY login = BINARY SUBSTRING_INDEX(USER(), '@', 1);
    IF v_usuario IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Conta MySQL sem usuario WebDriver correspondente';
    END IF;
    SELECT COUNT(*), MIN(id_arquivo) INTO v_qtd, v_arquivo FROM arquivo
    WHERE id_dono = v_usuario AND excluido_em IS NULL AND BINARY nome = BINARY p_nome_atual;
    IF v_qtd = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Arquivo inexistente ou sem permissao para atualizar';
    ELSEIF v_qtd > 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mais de um arquivo com esse nome; renomeie para identifica-lo';
    END IF;
    -- sp_atualizar_arquivo revalida dono, cota e grava operacao/versionamento.
    CALL sp_atualizar_arquivo(v_arquivo, v_usuario, p_nome, p_tipo, p_permissao, p_tamanho, p_localizacao, p_url);
END$$

DELIMITER ;
