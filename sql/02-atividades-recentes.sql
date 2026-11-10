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