# Pessoa 4 — Terceiro commit: integração Python, testes e documentação

## Entrega

| Arquivo | Conteúdo |
|---|---|
| webdriver/perfil.py | Detecta o perfil pela role ativa (CURRENT_ROLE) e pela conta (CURRENT_USER). O operador não escolhe o perfil. |
| webdriver/usuario.py | PapelUsuario: lista arquivos e histórico pelas views; carrega e atualiza pelas procedures usr_*. Sem IDs. |
| webdriver/empresa.py | PapelEmpresa: consulta usuários e arquivos pelas views da instituição. |
| webdriver/administracao.py | Chama Conta_usuários e Remover_acessos (PapelAdm e root) e Verificar_atividades e Chavear (somente root). |
| main.py | Mostra o menu conforme o perfil: admin ou root (CRUD anterior mais o módulo acessos; root também o módulo atividades), usuário ou empresa. |
| tests/test_parte2.py | Testes unitários isolados, sem MySQL. |
| tests/test_seguranca_mysql.py | Testes de integração em MySQL real. |
| docs/parte2-permissoes.md | Documentação técnica da Parte 2: ordem dos scripts, privilégios, identidade, interpretações e limites. |
| README.md | Atualizado com a sequência de instalação da Parte 2. |

O CRUD anterior (repositorio, arquivos, planos, historicos) não foi alterado e funciona com o PapelAdm. A segurança continua no MySQL: o menu apenas acompanha o que a conta pode fazer. Conta sem nenhuma das três roles ativas recebe uma mensagem e o programa termina.

## Como executar

1. Envie as pastas docs, tests e webdriver, além de main.py e README.md, para a raiz do repositório, mesclando as existentes.
2. Confirme que os scripts SQL 01 a 08 já foram executados.
3. Configure config.ini com uma conta que tenha uma das roles ativas (SET DEFAULT ROLE) e execute `python main.py`.
4. Para o perfil root, o módulo atividades exige uma conta root com senha, e não auth_socket.

Não publique config.ini nem a pasta .venv.

## Testes

```console
python -m unittest discover -s tests -v
```

Roda os testes unitários. Os de integração são ignorados por padrão. Para executá-los, é necessário MySQL 8.0.16 ou superior, o cliente `mysql` no PATH e uma conta root:

```console
WEBDRIVER_TEST_MYSQL=1 python -m unittest discover -s tests -v
```

Variáveis opcionais: WEBDRIVER_TEST_ROOT_USER, WEBDRIVER_TEST_ROOT_PASSWORD, WEBDRIVER_TEST_SOCKET e WEBDRIVER_TEST_HOST. No PowerShell, defina com `$env:WEBDRIVER_TEST_MYSQL='1'`.

Os testes de integração carregam os scripts 01 a 08 em um banco descartável (webdriver_teste), com roles TstPapel* e contas t*, e removem tudo ao final. O banco webdriver e as roles reais não são tocados. Cobrem: isolamento de arquivos privados, acesso a próprios e compartilhados, bloqueio de atualização sem autorização, isolamento entre empresas, empresa somente leitura, operações do administrador, bloqueio de operações administrativas ao usuário comum, ausência de acesso a atividades_recentes, histórico somente leitura, bloqueio de executáveis, procedures, função, triggers e ausência de IDs nas views.

Execução realizada: 28 testes (18 unitários e 10 de integração) passaram em Python 3.12 com MySQL 8.0.46 em Linux. Os módulos Python também foram exercitados manualmente com contas de usuário, administrador e root. Não foram executados no MySQL Workbench, em Windows nem em outras versões do MySQL.

## Commit no GitHub

Arquivos: webdriver/perfil.py, webdriver/usuario.py, webdriver/empresa.py, webdriver/administracao.py, main.py, tests/test_parte2.py, tests/test_seguranca_mysql.py, docs/parte2-permissoes.md, README.md e docs/pessoa4-commit3.md.

Título: `Integra permissões da Parte 2 à aplicação e adiciona testes`

Descrição: `Detecta o perfil pela role ativa e oferece menus de usuário, empresa e administração sem uso de IDs informados livremente. Adiciona testes unitários e de integração das permissões, procedures, função e triggers, além da documentação técnica e do README.`
