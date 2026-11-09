-- WebDriver | Parte 2 | Funcoes e triggers
-- Pre-requisitos: 01 a 06. Execute como root. Os triggers executam com os privilegios do
-- definidor (root), por isso gravam em atividades_recentes sem que nenhuma role tenha acesso a ela.
USE webdriver;
DELIMITER $$

-- Funcao do enunciado: TRUE (1) se a ultima alteracao registrada em atividades_recentes
-- ocorreu ha MAIS de 100 dias; FALSE (0) caso contrario. Arquivo sem registro de atividade
-- retorna FALSE: nao ha data para afirmar inatividade (nao se usa outra fonte de data).
-- SQL SECURITY INVOKER: quem nao tem acesso a atividades_recentes nao consegue usa-la como atalho.
CREATE FUNCTION fn_arquivo_inativo(p_id_arquivo BIGINT UNSIGNED)
RETURNS TINYINT(1)
NOT DETERMINISTIC
READS SQL DATA
SQL SECURITY INVOKER
BEGIN
    DECLARE v_ultima DATE DEFAULT NULL;
    SELECT ultima_versao INTO v_ultima FROM atividades_recentes WHERE id_arquivo = p_id_arquivo;
    IF v_ultima IS NULL THEN
        RETURN 0;
    END IF;
    RETURN IF(DATEDIFF(CURRENT_DATE(), v_ultima) > 100, 1, 0);
END$$

-- Auxiliar de Safe_security: 1 se nome (ultima extensao) ou tipo (extensao ou MIME) indicam executavel.
-- Usa a ULTIMA extensao, entao "relatorio.exe.txt" passa e "foto.jpg.exe" e bloqueado.
CREATE FUNCTION fn_arquivo_executavel(p_nome VARCHAR(255), p_tipo VARCHAR(120))
RETURNS TINYINT(1)
DETERMINISTIC
NO SQL
BEGIN
    DECLARE v_nome VARCHAR(255);
    DECLARE v_ext VARCHAR(255) DEFAULT '';
    DECLARE v_tipo VARCHAR(120);
    DECLARE v_exts VARCHAR(400) DEFAULT 'exe,com,bat,cmd,msi,msp,scr,pif,cpl,jar,vbs,vbe,wsf,wsh,ps1,sh,bash,run,apk,elf';
    DECLARE v_mimes VARCHAR(800) DEFAULT 'application/x-msdownload,application/x-msdos-program,application/x-dosexec,application/vnd.microsoft.portable-executable,application/x-executable,application/x-elf,application/x-sh,application/x-shellscript,application/x-bat,application/x-msi,application/java-archive,application/vnd.android.package-archive';

    -- Windows ignora espacos e pontos finais: "a.exe. " continua sendo .exe.
    SET v_nome = REGEXP_REPLACE(LOWER(COALESCE(p_nome, '')), '[[:space:].]+$', '');
    IF LOCATE('.', v_nome) > 0 THEN
        SET v_ext = SUBSTRING_INDEX(v_nome, '.', -1);
        IF LOCATE(',', v_ext) = 0 AND FIND_IN_SET(v_ext, v_exts) > 0 THEN
            RETURN 1;
        END IF;
    END IF;

    SET v_tipo = TRIM(LOWER(SUBSTRING_INDEX(COALESCE(p_tipo, ''), ';', 1)));
    IF LEFT(v_tipo, 1) = '.' THEN
        SET v_tipo = SUBSTRING(v_tipo, 2);
    END IF;
    IF LOCATE(',', v_tipo) = 0 AND v_tipo <> '' AND
       (FIND_IN_SET(v_tipo, v_exts) > 0 OR FIND_IN_SET(v_tipo, v_mimes) > 0) THEN
        RETURN 1;
    END IF;
    RETURN 0;
END$$

-- Safe_security: bloqueia a insercao de executaveis. Safe_security_update fecha o desvio por
-- UPDATE (renomear/retipar um arquivo valido); so age quando nome ou tipo mudam, para nao
-- impedir a remocao logica de eventual executavel ja existente.
CREATE TRIGGER Safe_security BEFORE INSERT ON arquivo FOR EACH ROW
BEGIN
    IF fn_arquivo_executavel(NEW.nome, NEW.tipo) = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Safe_security: arquivos executaveis nao podem ser inseridos no drive';
    END IF;
END$$

CREATE TRIGGER Safe_security_update BEFORE UPDATE ON arquivo FOR EACH ROW
BEGIN
    IF (NEW.nome <> OLD.nome OR NEW.tipo <> OLD.tipo) AND fn_arquivo_executavel(NEW.nome, NEW.tipo) = 1 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Safe_security: arquivos executaveis nao podem ser inseridos no drive';
    END IF;
END$$

-- Registrar_operacao: cada operacao (CARREGAR, ATUALIZAR, REMOVER) atualiza a data em
-- atividades_recentes. Cria o registro se nao existir (prioridade padrao); se existir, a
-- prioridade (acesso) e preservada e a data nunca retrocede.
CREATE TRIGGER Registrar_operacao AFTER INSERT ON operacao_arquivo FOR EACH ROW
BEGIN
    INSERT INTO atividades_recentes (id_arquivo, ultima_versao)
    VALUES (NEW.id_arquivo, DATE(NEW.data_hora))
    ON DUPLICATE KEY UPDATE ultima_versao = GREATEST(ultima_versao, DATE(NEW.data_hora));
END$$

-- Atualizar_acesso (interpretacao tecnica): o enunciado nao detalha "registros de arquivo".
-- O unico registro por arquivo do projeto e atividades_recentes; quando um usuario ganha acesso
-- a um arquivo (nova linha em compartilhamento), o registro desse arquivo e criado/atualizado
-- com a data do compartilhamento, tratada como atividade recente. A prioridade (acesso) e preservada.
-- Acesso por PUBLICO nao dispara: nao ha evento por usuario. A versao _update cobre troca de
-- destinatario/arquivo em compartilhamento existente.
CREATE TRIGGER Atualizar_acesso AFTER INSERT ON compartilhamento FOR EACH ROW
BEGIN
    INSERT INTO atividades_recentes (id_arquivo, ultima_versao)
    VALUES (NEW.id_arquivo, DATE(NEW.data_compartilhamento))
    ON DUPLICATE KEY UPDATE ultima_versao = GREATEST(ultima_versao, DATE(NEW.data_compartilhamento));
END$$

CREATE TRIGGER Atualizar_acesso_update AFTER UPDATE ON compartilhamento FOR EACH ROW
BEGIN
    IF NEW.id_compartilhado <> OLD.id_compartilhado OR NEW.id_arquivo <> OLD.id_arquivo THEN
        INSERT INTO atividades_recentes (id_arquivo, ultima_versao)
        VALUES (NEW.id_arquivo, DATE(NEW.data_compartilhamento))
        ON DUPLICATE KEY UPDATE ultima_versao = GREATEST(ultima_versao, DATE(NEW.data_compartilhamento));
    END IF;
END$$

DELIMITER ;
