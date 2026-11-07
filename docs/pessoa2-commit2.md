# Pessoa 2 — Segundo commit

## Entrega

Procedures da tabela atividades_recentes, compatíveis com o primeiro commit.

| Procedure | Parâmetro | Comportamento |
|---|---|---|
| Verificar_atividades | p_id_arquivo | Registra CURRENT_DATE() em ultima_versao. Se ainda não houver atividade, insere o registro com a prioridade padrão da tabela. Se já existir, preserva sua prioridade. |
| Chavear | p_id_arquivo | Alterna PRIORITARIO e NAO_PRIORITARIO, sem alterar ultima_versao. |

O enunciado não define uma assinatura para essas duas procedures. Foi adotado um ID de arquivo por chamada para direcionar a operação. Não foi inventado um prazo para classificar prioridade automaticamente.

Verificar_atividades segue o pedido expresso de usar a data atual. Para preservar o significado do campo como última edição, deve ser chamada após uma edição, não quando alguém apenas consultar o arquivo. Uma sincronização de arquivos históricos usando sua data original seria uma operação diferente e não é executada por esta procedure.

## Como adicionar e executar

1. Envie as pastas sql e docs deste pacote para a raiz do repositório, mesclando as pastas existentes.
2. No banco de desenvolvimento, confirme que o modelo físico e sql/02-atividades-recentes.sql já foram executados.
3. Conecte como root no Workbench e execute sql/03-procedures-atividades.sql.

O script cria as duas procedures uma vez; não apaga rotinas já existentes nem reexecuta a criação das tabelas.

Verificar_atividades controla sua própria transação e faz rollback se falhar. Execute-a como operação independente, sem uma transação externa pendente. Chavear usa uma atualização atômica e segue a transação/autocommit da sessão; confirme a transação no Workbench se o autocommit estiver desligado.

As rotinas não são chamadas automaticamente pelo CRUD Python neste commit. O grupo deverá conectá-las ao fluxo escolhido, preservando o acesso exclusivo do root. Não é concedido EXECUTE às contas da aplicação aqui.

## Teste manual no MySQL

Use um arquivo ativo de teste que tenha sido editado hoje. Substitua 1 pelo seu ID real:

```sql
USE webdriver;
CALL Verificar_atividades(1);
SELECT id_arquivo, ultima_versao, acesso
FROM atividades_recentes WHERE id_arquivo = 1;
```

Confira que ultima_versao é CURRENT_DATE(). Se for a primeira atividade, acesso deve ser NAO_PRIORITARIO.

```sql
CALL Chavear(1);
SELECT acesso FROM atividades_recentes WHERE id_arquivo = 1;
CALL Chavear(1);
SELECT acesso FROM atividades_recentes WHERE id_arquivo = 1;
```

Confira que o estado mudou e depois voltou ao original, sem mudar ultima_versao. Se autocommit estiver desligado, execute COMMIT.

Execute Verificar_atividades novamente após colocar prioridade em PRIORITARIO: ela deve preservar esse estado. Rodar a procedure duas vezes no mesmo dia deve funcionar e manter só uma linha por arquivo.

Teste separadamente chamadas com NULL, zero, ID inexistente e arquivo removido: devem ser recusadas. Chavear também deve recusar um arquivo sem registro em atividades_recentes; primeiro registre a atividade.

Após configurar as roles, a conta root deve conseguir executar as rotinas. Contas comuns não devem ter acesso à tabela nem execução dessas rotinas. SQL SECURITY INVOKER impede que as rotinas emprestem as permissões do criador; as permissões efetivas ainda precisam ser configuradas pelo integrante responsável.

## Commit

Título: `Adiciona procedures de verificação de atividades e prioridade`

Descrição: `Implementa Verificar_atividades por arquivo, registrando a data atual sem sobrescrever a prioridade, e Chavear para alternar a prioridade. Recusa arquivos inexistentes ou removidos e utiliza permissões do invocador.`

Esta entrega foi conferida estaticamente contra o script da tabela. Não foi executada em servidor MySQL neste ambiente; os testes acima estão pendentes no banco do grupo.
