import json
import sys
from getpass import getpass

if sys.version_info >= (3, 15):
    raise SystemExit(
        'Python 3.15 ainda não é compatível com o MySQL Connector/Python. '
        'Use o ambiente .venv do projeto (Python 3.12) ou Python 3.10–3.14.'
    )

try:
    from mysql.connector import Error
except ImportError:
    raise SystemExit('Instale as dependências: python -m pip install -r requirements.txt')
from webdriver import (
    administracao,
    arquivos,
    empresa,
    historicos,
    perfil,
    planos,
    repositorio,
    usuario,
)
from webdriver.catalogo import ENTIDADES, Campo


def mostrar(valor):
    print(json.dumps(valor, ensure_ascii=False, indent=2, default=str))


def ler(campo):
    detalhe = ' (AAAA-MM-DD)' if campo.tipo == 'data' else ' (HH:MM:SS)' if campo.tipo == 'hora' else ''
    if campo.escolhas:
        detalhe += ' (' + '/'.join(campo.escolhas) + ')'
    if campo.opcional:
        detalhe += ' (vazio = sem valor)'
    rotulo = 'senha (mínimo 8 caracteres)' if campo.tipo == 'senha' else campo.nome
    return getpass(rotulo + ': ') if campo.tipo == 'senha' else input(rotulo + detalhe + ': ')


def dados_campos(campos, parcial=False):
    resultado = {}
    for campo in campos:
        if parcial and input(f'Alterar {campo.nome}? [s/N]: ').strip().lower() != 's':
            continue
        resultado[campo.nome] = ler(campo)
    return resultado


def confirmar():
    return input('Confirme exclusão digitando SIM: ').strip() == 'SIM'


def menu_cadastro(nome):
    e = ENTIDADES[nome]
    while True:
        print(f'\n{nome}: 1 Cadastrar | 2 Listar | 3 Buscar | 4 Atualizar | 5 Excluir | 0 Voltar')
        opcao = input('Opção: ').strip()
        if opcao == '0':
            return
        if opcao == '1':
            mostrar(repositorio.criar(nome, dados_campos(e.campos)))
        elif opcao == '2':
            mostrar(repositorio.listar(nome, pagina=int(input('Página (100 por página): ') or '1')))
        elif opcao in ('3', '4', '5'):
            chaves = {c: input(f'{c} atual: ') for c in e.chaves}
            if opcao == '3':
                registro = repositorio.buscar(nome, chaves)
                mostrar(registro) if registro else print('Registro não encontrado.')
            elif opcao == '4':
                dados = dados_campos(e.campos, parcial=True)
                if not dados:
                    print('Nenhum campo selecionado.')
                    continue
                print('Registro atualizado.' if repositorio.atualizar(nome, chaves, dados) else 'Registro não encontrado.')
            elif confirmar():
                print('Registro excluído.' if repositorio.excluir(nome, chaves) else 'Registro não encontrado.')
            else:
                print('Exclusão cancelada.')
        else:
            print('Opção inválida.')


def menu_planos():
    while True:
        print('\nPlanos: 1 Cadastrar | 2 Listar | 3 Buscar | 4 Atualizar | 5 Excluir | 0 Voltar')
        op = input('Opção: ').strip()
        if op == '0':
            return
        if op == '2':
            mostrar(planos.listar())
        elif op in ('1', '4'):
            chave = int(input('ID: ')) if op == '4' else None
            dados = (input('Nome: '), int(input('Duração em dias: ')), int(input('Espaço por usuário em bytes: ')))
            if op == '1':
                mostrar({'id_plano': planos.criar(*dados)})
            else:
                print('Plano atualizado.' if planos.atualizar(chave, *dados) else 'Plano não encontrado.')
        elif op == '3':
            mostrar(planos.buscar(int(input('ID: '))))
        elif op == '5':
            chave = int(input('ID: '))
            if confirmar():
                print('Plano excluído.' if planos.excluir(chave) else 'Plano não encontrado.')
            else:
                print('Exclusão cancelada.')
        else:
            print('Opção inválida.')


def menu_arquivos():
    while True:
        print('\nArquivos: 1 Cadastrar metadados | 2 Listar | 3 Buscar | 4 Atualizar | 5 Remover | 0 Voltar')
        op = input('Opção: ').strip()
        if op == '0':
            return
        if op == '2':
            pagina = int(input('Página: ') or '1')
            incluir = input('Incluir removidos? [s/N]: ').strip().lower() == 's'
            mostrar(arquivos.listar(pagina, incluir))
        elif op == '3':
            mostrar(arquivos.buscar(input('ID do arquivo: ')))
        elif op in ('1', '4'):
            chave = input('ID do arquivo: ') if op == '4' else None
            dono = input('ID do usuário dono: ')
            dados = dados_campos((*arquivos.CAMPOS, Campo('tamanho_bytes')))
            if op == '1':
                mostrar(arquivos.criar(dono, dados))
            else:
                arquivos.atualizar(chave, dono, dados)
                print('Arquivo atualizado; histórico registrado.')
        elif op == '5':
            chave, dono = input('ID do arquivo: '), input('ID do usuário dono: ')
            if confirmar():
                arquivos.excluir(chave, dono)
                print('Arquivo removido logicamente; histórico preservado.')
            else:
                print('Remoção cancelada.')
        else:
            print('Opção inválida.')


def menu_acessos():
    print('\nAcessos: 1 Contar usuários com acesso | 2 Remover acessos (mantém o proprietário) | 0 Voltar')
    op = input('Opção: ').strip()
    if op == '1':
        print('Usuários com acesso:', administracao.conta_usuarios(input('ID do arquivo: ')))
    elif op == '2':
        chave = input('ID do arquivo: ')
        if confirmar():
            administracao.remover_acessos(chave)
            print('Acessos removidos; proprietário preservado.')
        else:
            print('Operação cancelada.')


def menu_atividades():
    print('\nAtividades (somente root): 1 Verificar_atividades | 2 Chavear prioridade | 0 Voltar')
    op = input('Opção: ').strip()
    if op == '1':
        administracao.verificar_atividades()
        print('atividades_recentes atualizada com a data atual.')
    elif op == '2':
        administracao.chavear(input('ID do arquivo: '))
        print('Prioridade alternada.')


def menu_usuario():
    while True:
        print('\nMeus arquivos: 1 Listar | 2 Carregar | 3 Atualizar | 4 Histórico | 0 Sair')
        op = input('Opção: ').strip()
        if op == '0':
            return
        if op == '1':
            mostrar(usuario.listar_arquivos(int(input('Página: ') or '1')))
        elif op in ('2', '3'):
            atual = input('Nome atual do arquivo: ') if op == '3' else None
            dados = dados_campos((*arquivos.CAMPOS, Campo('tamanho_bytes')))
            usuario.carregar(dados) if op == '2' else usuario.atualizar(atual, dados)
            print('Operação concluída.')
        elif op == '4':
            mostrar(usuario.historico(int(input('Página: ') or '1')))
        else:
            print('Opção inválida.')


def menu_empresa():
    while True:
        print('\nEmpresa (somente leitura): 1 Usuários | 2 Arquivos | 0 Sair')
        op = input('Opção: ').strip()
        if op == '0':
            return
        if op in ('1', '2'):
            pagina = int(input('Página: ') or '1')
            mostrar(empresa.usuarios(pagina) if op == '1' else empresa.arquivos(pagina))
        else:
            print('Opção inválida.')


MENSAGENS = {1451: 'Registro vinculado a outros dados; exclusão bloqueada.',
             1452: 'Referência inexistente: confira os IDs informados.',
             1062: 'Registro duplicado: confira login, e-mail ou vínculo.',
             1045: 'Acesso negado: confira as credenciais.',
             1049: 'Banco inexistente: execute o modelo físico antes.',
             1146: 'Tabela inexistente: confira o modelo físico.',
             1305: 'Procedimento ou função inexistente: confira o modelo físico.',
             1142: 'Conta MySQL sem permissão para a operação.',
             1370: 'Conta MySQL sem permissão para executar a rotina.'}


def mensagem_erro(erro):
    return MENSAGENS.get(erro.errno, erro.msg if erro.errno == 1644 else f'Erro MySQL {erro.errno}: confira a configuração e os dados.')


def menu_admin(perfil_ativo):
    cadastros = list(ENTIDADES)
    opcoes = ['planos', *cadastros, 'arquivos', 'operacoes', 'versoes', 'acessos']
    if perfil_ativo == 'root':
        opcoes.append('atividades')
    while True:
        print('\n' + '\n'.join(f'{i} {nome}' for i, nome in enumerate(opcoes, 1)) + '\n0 Sair')
        try:
            op = input('Módulo: ').strip()
            if op == '0':
                return
            if not op.isdigit() or not 1 <= int(op) <= len(opcoes):
                print('Opção inválida.')
                continue
            nome = opcoes[int(op)-1]
            if nome == 'planos':
                menu_planos()
            elif nome == 'arquivos':
                menu_arquivos()
            elif nome == 'acessos':
                menu_acessos()
            elif nome == 'atividades':
                menu_atividades()
            elif nome in ('operacoes', 'versoes'):
                arquivo = input('ID do arquivo (vazio = todos): ').strip() or None
                pagina = int(input('Página: ') or '1')
                mostrar(historicos.consultar(nome, arquivo, pagina))
            else:
                menu_cadastro(nome)
        except ValueError as erro:
            print('Dados inválidos:', erro)
        except Error as erro:
            print(mensagem_erro(erro))
        except (EOFError, KeyboardInterrupt):
            print('\nEncerrado.')
            return


def menu_restrito(menu):
    try:
        menu()
    except ValueError as erro:
        print('Dados inválidos:', erro)
    except Error as erro:
        print(mensagem_erro(erro))
    except (EOFError, KeyboardInterrupt):
        print('\nEncerrado.')


def main():
    try:
        perfil_ativo = perfil.detectar()
    except (Error, ValueError) as erro:
        print(mensagem_erro(erro) if isinstance(erro, Error) else erro)
        return
    print(f'WebDriver — conta MySQL de config.ini, perfil: {perfil_ativo or "sem role ativa"}.')
    if perfil_ativo in ('admin', 'root'):
        menu_admin(perfil_ativo)
    elif perfil_ativo == 'usuario':
        menu_restrito(menu_usuario)
    elif perfil_ativo == 'empresa':
        menu_restrito(menu_empresa)
    else:
        print('Conta sem PapelUsuario, PapelEmpresa ou PapelAdm ativo (veja SET DEFAULT ROLE em sql/08-roles-permissoes.sql).')


if __name__ == '__main__':
    main()
