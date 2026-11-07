-- WebDriver | Parte 2 | Pessoa 2 | Primeiro commit
-- Execute como root apos o modelo fisico existente.
-- Nao recria nem altera as tabelas da Parte 1.
USE webdriver;

CREATE TABLE atividades_recentes (
    id_arquivo BIGINT UNSIGNED NOT NULL,
    ultima_versao DATE NOT NULL,
    acesso ENUM('PRIORITARIO', 'NAO_PRIORITARIO') NOT NULL
        DEFAULT 'NAO_PRIORITARIO',
    PRIMARY KEY (id_arquivo),
    CONSTRAINT fk_atividades_recentes_arquivo
        FOREIGN KEY (id_arquivo) REFERENCES arquivo(id_arquivo)
        ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- Um registro por arquivo; id_arquivo e PK e FK.
-- ultima_versao representa a data da ultima edicao, nao a data de uma consulta.
-- Verificar_atividades e Chavear serao adicionadas no segundo commit.
-- Tabela inicialmente vazia: este script nao inventa atividades nem prioridades.
-- A exclusao logica de arquivo nao aciona ON DELETE CASCADE.
-- Nenhum privilegio e concedido aqui a usuarios ou roles da aplicacao.
-- IMPORTANTE: criar a tabela nao torna o acesso exclusivo do root se outras
-- contas/roles ja possuem privilegios amplos em webdriver.* ou *.*.
-- O responsavel pelas roles deve revisar esses privilegios e conceder acesso
-- por objeto, excluindo esta tabela e rotinas/views que a exponham.
-- Nao use GRANT ALL ON webdriver.* para os papeis da aplicacao.
