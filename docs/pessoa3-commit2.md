# Pessoa 3 — Segundo commit

## Views de empresa

- vw_empresa_usuarios: usuários da mesma instituição do representante conectado.
- vw_empresa_arquivos: arquivos ativos pertencentes a esses usuários, conforme o acesso institucional solicitado no enunciado.

A conta da empresa deve corresponder ao login de um usuário representante da instituição. Esse vínculo usa usuario.id_instituicao já existente; não se cria um cadastro paralelo. Só conceder SELECT nessas views a PapelEmpresa. O filtro institucional sozinho não distingue funcionário de representante: a atribuição de role é obrigatória. Alterações no vínculo institucional ou no login do representante devem ser restritas ao administrador autorizado.

## Views de administrador

Inclui vw_admin_usuarios, vw_admin_arquivos, vw_admin_planos, vw_admin_instituicoes, vw_admin_administradores, vw_admin_compartilhamentos, vw_admin_comentarios, vw_admin_suporte, vw_admin_atendimentos, vw_admin_operacoes e vw_admin_versoes.

A conexão deve corresponder a um usuario.login que esteja vinculado à tabela administrador. Caso contrário, essas views retornam zero linhas. Ainda é preciso conceder SELECT exclusivamente à role administrativa.

Nenhuma view projeta colunas de ID ou hash de senha. O conteúdo livre de versionamento foi omitido da view de versões para evitar expor referências internas contidas em JSON/texto. Campos de texto livre cadastrados por pessoas não são higienizados por esta entrega. Nomes podem se repetir: estas views são para consulta, não usam nomes como chave para edição.

Todas são de leitura (ALGORITHM TEMPTABLE). As permissões de escrita de PapelAdm continuam na entrega de roles/rotinas, respeitando a auditoria. A tabela atividades_recentes continua fora das views, em razão da exceção de acesso exclusivo ao root.

## Identidade e permissões

Mantém o contrato do primeiro pacote: uma conta MySQL por pessoa, com nome exatamente igual a usuario.login, comparação sensível a maiúsculas/minúsculas, sem @ no nome, sem usuários anônimos, autenticação por proxy ou conta compartilhada. Contas homônimas em hosts diferentes devem pertencer à mesma pessoa. O Python administrativo atual não implementa autenticação individual; teste essas views por conexões individuais no Workbench.

As views usam SQL SECURITY DEFINER: o criador deve possuir os privilégios de leitura necessários e continuar existindo. USER() identifica a conexão. Não usar @id_usuario para controlar o acesso. O responsável pelas roles não deve conceder SELECT direto nas bases a usuários/empresas nem acesso às views administrativas para as outras roles.

## Como enviar

Envie as pastas sql e docs para a raiz do repositório, mesclando as existentes. Execute sql/05-views-empresa-admin.sql como root no banco de desenvolvimento. Não reexecute o modelo físico. O script cria views uma vez e não substitui objetos existentes.

## Validação no banco do grupo

Após criar as contas e atribuir as roles:

1. Conecte como representante da instituição A: veja somente usuários e arquivos da instituição A nas views de empresa.
2. Conecte como representante da B: não veja dados da A.
3. Conecte como funcionário sem PapelEmpresa: o SELECT das views de empresa deve ser negado.
4. Conecte como administrador cadastrado: confira as 11 views administrativas e a ausência de IDs/senhas.
5. Como usuário comum, SELECT nas views administrativas deve ser negado. Como conta com SELECT mas sem vínculo em administrador, as views administrativas devem retornar zero linhas.
6. UPDATE/INSERT/DELETE nas views devem falhar; atividades_recentes deve continuar inacessível a contas não root.
7. Confira IS_UPDATABLE = NO em information_schema.VIEWS para cada view criada.

Conferência estática realizada; ainda não executado em servidor MySQL nesta preparação. As permissões dependem do próximo integrante, e não foram concedidas por este script.

## Commit

Título: `Adiciona views de consulta para empresa e administrador`

Descrição: `Inclui consultas institucionais e administrativas sem IDs ou senhas, preservando a restrição de atividades_recentes ao root. Documenta identidade das contas, dependências de roles e testes.`
