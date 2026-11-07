# Pessoa 2 — Primeiro commit

## Entrega

Cria `webdriver.atividades_recentes` conforme a Parte 2.

| Campo | Definição |
|---|---|
| id_arquivo | BIGINT UNSIGNED, PK e FK para arquivo.id_arquivo; um registro por arquivo |
| ultima_versao | DATE, data da última edição do arquivo |
| acesso | PRIORITARIO ou NAO_PRIORITARIO; padrão NAO_PRIORITARIO |

Os nomes estão em minúsculas para seguir o modelo físico existente. A escolha de ENUM representa os dois estados previstos no enunciado. Nenhum limiar de frequência foi acrescentado.

## Aplicação

1. Extraia o pacote na raiz do repositório, mesclando as pastas sql e docs existentes.
2. No Workbench, conecte como root ao banco que já possui a Parte 1.
3. Execute apenas sql/02-atividades-recentes.sql. Ele cria a nova tabela, inicialmente vazia.
4. Confira com `SHOW CREATE TABLE webdriver.atividades_recentes;` e `DESCRIBE webdriver.atividades_recentes;`.

O script é uma migração de execução única. Não reexecute se a tabela já existir; não apague tabelas para contornar esse erro. Não é necessário reexecutar o modelo físico inicial.

## Acesso exclusivo do root

Este commit não concede acesso a contas nem roles de aplicação. Isso, sozinho, não bloqueia contas que já possuem permissões sobre webdriver.* ou *.*. O integrante responsável pelas roles precisa revisar os privilégios existentes, inclusive herdados, e conceder permissões por tabela/visão, sem incluir atividades_recentes. Não conceder acesso indireto por views ou rotinas com permissões do definidor.

Validação final de permissões, após o commit das roles: o SELECT desta tabela deve funcionar para root e ser negado nas contas de usuário, empresa e administrador da aplicação. O administrador da plataforma não é a conta root do MySQL.

Referência oficial: https://dev.mysql.com/doc/refman/8.0/en/privileges-provided.html.

## Segundo commit desta pessoa

Continua reservado às procedures Verificar_atividades e Chavear. Elas ainda não estão neste pacote; deverão usar os nomes e estados definidos nesta tabela. A regra exata de atualização da data deve respeitar o enunciado e ser documentada ao implementar Verificar_atividades.

## Commit no GitHub

Arquivos: sql/02-atividades-recentes.sql e docs/pessoa2-commit1.md.

Título: `Adiciona tabela de atividades recentes da Parte 2`

Descrição: `Cria atividades_recentes com referência ao arquivo, data da última edição e classificação de prioridade. Documenta a restrição de acesso ao root e a integração com as procedures do próximo commit.`

Esta entrega foi conferida contra os tipos do modelo físico disponível. Não foi executada em servidor MySQL neste ambiente; a validação integrada e das permissões deve ocorrer no banco do grupo.
