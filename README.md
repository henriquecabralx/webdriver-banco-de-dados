# WebDriver — Banco de Dados

Projeto de modelagem e implementação de um banco de dados para gerenciamento de arquivos, usuários e instituições, com compartilhamento, comentários, suporte e histórico de operações.

## Modelos

### Modelo conceitual

![Modelo conceitual](docs/modelo-conceitual/modelo-conceitual.png)

### Modelo lógico

![Modelo lógico](docs/modelo-logico/modelo-logico.png)

### Modelo físico

O script [01-modelo-fisico.sql](sql/01-modelo-fisico.sql) implementa a estrutura em MySQL 8.0.16 ou superior.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `docs/modelo-conceitual/` | Diagrama conceitual |
| `docs/modelo-logico/` | Diagrama lógico |
| `sql/` | Implementação física, Parte 2 (scripts 02–08) |
| `webdriver/`, `main.py` | Aplicação Python (CRUD e perfis usuário/empresa/admin) |
| `tests/` | Testes unitários e de integração (MySQL) |

## Recursos implementados no script

- Instituições e planos com limite de armazenamento por usuário.
- Usuários e administradores.
- Arquivos e compartilhamentos.
- Comentários e chamados de suporte com múltiplos administradores.
- Histórico de operações e metadados de versões.
- Exclusão lógica de arquivos.
- Procedimentos para carregar, atualizar e remover arquivos.
- Triggers para validações de acesso e cotas.

## Como executar

Pré-requisitos: Python 3.10 a 3.14 (Python 3.12 recomendado) e MySQL 8.0.16 ou superior. O MySQL Connector/Python ainda não oferece suporte ao Python 3.15.

1. Crie e ative o ambiente virtual com uma versão compatível:

   ```console
   python3.12 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. Abra o MySQL Workbench e conecte-se a uma instância de desenvolvimento.
3. Abra `sql/01-modelo-fisico.sql`.
4. Execute o script em um banco novo. Ele cria e seleciona o banco `webdriver`.
5. Copie `config.example.ini` para `config.ini`, configure a conexão e execute `python main.py`.

Reexecutar o script após criar as tabelas causará erros de objetos existentes.

## Regras e limites

Cada instituição possui um plano atual. Um chamado pode ser associado a vários administradores. As alterações em arquivos devem passar pelos procedimentos para aplicar cotas e registrar histórico. Autenticação, hash de senha e permissões da conta do banco precisam ser configurados pela aplicação e pelo responsável pelo ambiente. O histórico de metadados não substitui a preservação dos arquivos de versões anteriores.

## Parte 2 — instalação e permissões

Como root, nesta ordem (cliente com utf8mb4, p.ex. `mysql -u root -p --default-character-set=utf8mb4 < arquivo.sql`):

1. `sql/01-modelo-fisico.sql` a `sql/05-views-empresa-admin.sql`
2. `sql/06-procedures-permissoes.sql` (`Conta_usuários`, `Remover_acessos`, `usr_*`)
3. `sql/07-funcoes-triggers.sql` (`fn_arquivo_inativo`, `Safe_security`, `Registrar_operacao`, `Atualizar_acesso`)
4. `sql/08-roles-permissoes.sql` (`PapelUsuario`, `PapelEmpresa`, `PapelAdm`)

Pré-requisitos: MySQL 8.0.16+, sem contas anônimas, uma conta MySQL por usuário com nome igual a `usuario.login`, e `SET DEFAULT ROLE` para cada conta. `atividades_recentes` é acessível apenas ao root. Detalhes, decisões de interpretação e limitações: [docs/parte2-permissoes.md](docs/parte2-permissoes.md).

Testes: `python -m unittest discover -s tests -v` (unitários); com `WEBDRIVER_TEST_MYSQL=1` também roda os de integração em MySQL real. A suíte completa foi validada com Python 3.12 e MySQL 8.4.

## Arquivos editáveis dos diagramas

- [Modelo conceitual no Drive](https://drive.google.com/file/d/1purrhiVyhfNTFOg3Qon34gkXQpi7SYsP/view)
- [Modelo lógico no Drive](https://drive.google.com/file/d/1WD-crls5wBHvUXtBlZt8xxZJQfTUF5Bc/view)

Os arquivos `.drawio` não estão incluídos neste pacote. Os links foram fornecidos pelo autor e podem apontar para versões anteriores às imagens.
