-- WebDriver | Parte 2 | Pessoa 2 | Segundo commit
-- Pre-requisitos: 01-modelo-fisico.sql e 02-atividades-recentes.sql.
-- Execute como root no MySQL Workbench.
-- Parte 2 (revisao): Verificar_atividades passou a atualizar toda a tabela, sem parametro,
-- conforme o enunciado. Banco que ja executou a versao anterior: DROP PROCEDURE Verificar_atividades;
-- e reexecutar somente o bloco desse procedimento. Nao concede privilegios a outras contas.
USE webdriver;
DELIMITER $$

CREATE PROCEDURE Verificar_atividades()
SQL SECURITY INVOKER
MODIFIES SQL DATA
BEGIN
    -- Enunciado: atualizar TODA a tabela atividades_recentes com a data atual.
    -- Nao recebe parametros. A prioridade (acesso) nao e alterada.
    -- WHERE sobre a chave primaria evita o erro 1175 com sql_safe_updates ativo.
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

    -- Uma unica instrucao alterna o estado atomicamente.
    -- Nao altera a data da ultima edicao.
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

-- Nao executar automaticamente: exemplos de chamadas (troque 1 por ID real).
-- CALL Verificar_atividades();
-- CALL Chavear(1);
-- SELECT * FROM atividades_recentes WHERE id_arquivo = 1;

-- SQL SECURITY INVOKER faz as rotinas usarem as permissoes de quem chama.
-- Portanto elas nao elevam privilegios para acessar a tabela restrita.
-- O integrante das roles deve manter a tabela e estas rotinas fora dos GRANTs
-- de usuarios/empresa/admin da aplicacao e revisar privilegios herdados.
