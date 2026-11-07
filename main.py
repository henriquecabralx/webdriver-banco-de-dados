"""Console administrativo acadêmico: CRUD da Parte 1."""
import json
from getpass import getpass
try:
    from mysql.connector import Error
except ImportError:
    raise SystemExit('Instale as dependências: python -m pip install -r requirements.txt')
from webdriver import planos, repositorio, arquivos, historicos
from webdriver.catalogo import ENTIDADES, Campo, id_campo


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


def main():
    cadastros = list(ENTIDADES)
    opcoes = ['planos', *cadastros, 'arquivos', 'operacoes', 'versoes']
    print('WebDriver — console administrativo local, usando a conta MySQL de config.ini.')
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
            elif nome in ('operacoes', 'versoes'):
                arquivo = input('ID do arquivo (vazio = todos): ').strip() or None
                pagina = int(input('Página: ') or '1')
                mostrar(historicos.consultar(nome, arquivo, pagina))
            else:
                menu_cadastro(nome)
        except ValueError as erro:
            print('Dados inválidos:', erro)
        except Error as erro:
            mensagens = {1451: 'Registro vinculado a outros dados; exclusão bloqueada.',
                         1452: 'Referência inexistente: confira os IDs informados.',
                         1062: 'Registro duplicado: confira login, e-mail ou vínculo.',
                         1045: 'Acesso negado: confira as credenciais.',
                         1049: 'Banco inexistente: execute o modelo físico antes.',
                         1146: 'Tabela inexistente: confira o modelo físico.',
                         1305: 'Procedimento ou função inexistente: confira o modelo físico.',
                         1142: 'Conta MySQL sem permissão para a operação.',
                         1370: 'Conta MySQL sem permissão para executar a rotina.'}
            print(mensagens.get(erro.errno, erro.msg if erro.errno == 1644 else f'Erro MySQL {erro.errno}: confira a configuração e os dados.'))
        except (EOFError, KeyboardInterrupt):
            print('\nEncerrado.')
            return


if __name__ == '__main__':
    main()
