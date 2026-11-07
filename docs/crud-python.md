# CRUD em Python — Parte 1

Complemento do commit de conexão e planos já integrado na main. Copie o conteúdo deste ZIP para a raiz do repositório; substitua main.py e adicione os novos módulos, preservando docs, README, SQL e qualquer config.ini local. O pacote inclui cópias da conexão e de planos compatíveis com a versão lida da main.

## Instalação

Python 3.10 ou superior. Execute o SQL existente `sql/01-modelo-fisico.sql` no MySQL Workbench, em banco novo, se ainda não o executou. Não reexecute esse script em banco populado.

```console
python -m venv .venv
```

Ative no PowerShell com `.venv\Scripts\Activate.ps1`, ou no Linux/macOS com `source .venv/bin/activate`.

```console
python -m pip install -r requirements.txt
```

Copie config.example.ini para config.ini, preencha a conexão e execute:

```console
python main.py
```

Não publique config.ini nem a pasta .venv. Todos os integrantes precisam configurar suas próprias credenciais locais.

## Cobertura

| Módulo | Operações |
|---|---|
| Planos | Criar, listar, buscar, atualizar e excluir |
| Instituições | Criar, listar, buscar, atualizar e excluir |
| Usuários | Criar, listar, buscar, atualizar e excluir; senha gravada como hash PBKDF2 com sal aleatório |
| Administradores | Criar, listar, buscar, atualizar e excluir o vínculo com usuário |
| Arquivos | Criar/consultar/atualizar metadados e remover logicamente via procedures existentes |
| Compartilhamentos | Criar, listar, buscar por chave composta, atualizar vínculo e excluir |
| Comentários | Criar, listar, buscar, atualizar conteúdo e excluir |
| Suporte | Criar, listar, buscar, atualizar e excluir |
| Atendimento | Vincular, listar, buscar por chave composta, alterar e desvincular administradores |
| Operações e versões | Consultar todos ou por arquivo, em páginas de 100 registros; gerados pelas operações de arquivos |

Atualizações de cadastros permitem selecionar os campos individualmente. Em campos opcionais, vazio limpa o valor. Em arquivos, a atualização exige todos os metadados. Exclusões exigem confirmação SIM. As FKs bloqueiam a exclusão de cadastros que ainda têm dependentes; não é feita limpeza automática desses dependentes.

## Compatibilidade e limites

Usa as tabelas, triggers e procedimentos do modelo físico atual, sem alterar seu SQL. As ações em arquivos passam por sp_carregar_arquivo, sp_atualizar_arquivo e sp_remover_arquivo, preservando cota e auditoria. As procedures controlam suas próprias transações; cada chamada usa conexão própria. Não envolva essas funções em uma transação externa.

Este é um console de administração local para a Parte 1. Os IDs de usuário são referências fornecidas pelo operador, não autenticação. A conta MySQL configurada define o acesso efetivo. Login de assinantes, views e roles da Parte 2 não estão implementados aqui. As triggers existentes fazem as verificações de acesso previstas no modelo físico para comentários e suporte.

O cadastro de arquivo opera metadados: não envia nem copia o conteúdo binário. Informe localização, URL e tamanho correspondentes ao arquivo armazenado. Restaurar uma versão exige conservar o conteúdo antigo fora do banco. A busca administrativa permite consultar metadados de arquivos removidos; a listagem padrão os oculta.

Permissões da conta de desenvolvimento: CRUD nos cadastros e vínculos, SELECT em arquivo e históricos e EXECUTE nas três procedures e funções necessárias. A configuração de contas e privilégios continua sob responsabilidade do grupo. A documentação de Parte 2 determina as permissões finais.

## Testes

```console
python -m unittest discover -s tests -v
```

Testes automatizados isolados cobrem validação, ausência de hash nas consultas, SQL parametrizado, chaves compostas, atualização sem alteração, restrição dos históricos e chamada dos procedimentos de arquivos. Não substituem execução em MySQL.

Roteiro no MySQL do grupo:

1. Cadastre plano, instituição, dois usuários e um administrador, nessa ordem.
2. Liste e busque cada registro; altere dados e confira valores persistidos.
3. Cadastre arquivo PRIVADO para o primeiro usuário; teste tamanho zero e tamanho acima da cota.
4. Atualize o arquivo para COMPARTILHADO, crie o compartilhamento com o segundo usuário e consulte pela chave composta.
5. Cadastre comentário e suporte do segundo usuário nesse arquivo; associe o administrador ao chamado.
6. Altere comentário, suporte e vínculo; exclua comentário e vínculo de teste.
7. Remova arquivo pelo dono e confira excluido_em, operações e versões. Tente nova atualização: deve ser recusada.
8. Teste login/e-mail duplicados, FK inexistente, exclusão de plano em uso e comentário sem acesso: todos devem ser recusados.
9. Cadastre e exclua dados sem dependentes para conferir o DELETE dos demais cadastros.

Validação nesta entrega: 12 testes isolados aprovados e sintaxe Python verificada. Sem servidor MySQL disponível neste ambiente, o roteiro integrado está pendente.

## Segundo commit da pessoa responsável pelo CRUD

Mensagem: `Completa CRUD Python e integra menu administrativo do WebDriver`.

Envie main.py, os módulos novos em webdriver, docs/crud-python.md e tests/test_crud.py. Arquivos de conexão, dependências e exemplo de configuração já existentes podem permanecer como estão. Não publique este ZIP inteiro como um arquivo no repositório; publique o conteúdo extraído.

Referências do conector: https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-execute.html e https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-callproc.html.
