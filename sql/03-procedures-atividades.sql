USE webdriver;
DELIMITER $$

CREATE PROCEDURE Verificar_atividades()
SQL SECURITY INVOKER
MODIFIES SQL DATA
BEGIN
    UPDATE atividades_recentes
    SET ultima_versao = CURRENT_DATE()
    WHERE id_arquivo > 0;
END$$

CREATE PROCEDURE Chavear(IN p_id_arquivo BIGINT UNSIGNED)
SQL SECURITY INVOKER
MODIFIES SQL DATA
BEGIN
    IF p_id_arquivo IS NULL OR p_id_arquivo = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Informe um ID de arquivo positivo';
    END IF;

    UPDATE atividades_recentes ar
    INNER JOIN arquivo a ON a.id_arquivo = ar.id_arquivo
    SET ar.acesso = CASE ar.acesso
        WHEN 'PRIORITARIO' THEN 'NAO_PRIORITARIO'
        ELSE 'PRIORITARIO'
    END
    WHERE ar.id_arquivo = p_id_arquivo AND a.excluido_em IS NULL;

    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Arquivo ativo sem registro de atividade, inexistente ou removido';
    END IF;
END$$

DELIMITER ;
