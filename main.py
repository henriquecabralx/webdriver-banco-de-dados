"""Interface de terminal da primeira entrega: planos."""
import json
from mysql.connector import Error
from webdriver import planos


def dados():
    return (input("Nome: "), int(input("Duração em dias: ")),
            int(input("Espaço por usuário em bytes (1 MiB = 1048576): ")))


def main():
    while True:
        print("\nWebDriver — Planos\n1 Cadastrar\n2 Listar\n3 Buscar por ID\n4 Atualizar\n5 Excluir\n0 Sair")
        try:
            opcao = input("Opção: ").strip()
            if opcao == "0":
                break
            if opcao == "1":
                print("Plano criado. ID:", planos.criar(*dados()))
            elif opcao == "2":
                print(json.dumps(planos.listar(), ensure_ascii=False, indent=2))
            elif opcao == "3":
                registro = planos.buscar(int(input("ID: ")))
                print(json.dumps(registro, ensure_ascii=False, indent=2) if registro else "Plano não encontrado.")
            elif opcao == "4":
                identificador = int(input("ID: "))
                print("Plano atualizado." if planos.atualizar(identificador, *dados()) else "Plano não encontrado.")
            elif opcao == "5":
                identificador = int(input("ID: "))
                if input("Confirmar exclusão? Digite SIM: ").strip() == "SIM":
                    print("Plano excluído." if planos.excluir(identificador) else "Plano não encontrado.")
                else:
                    print("Exclusão cancelada.")
            else:
                print("Opção inválida.")
        except ValueError as erro:
            print("Dados inválidos:", erro)
        except Error as erro:
            if erro.errno == 1451:
                print("Não é possível excluir: o plano está vinculado a uma instituição.")
            elif erro.errno == 1644:
                print("Operação recusada:", erro.msg)
            elif erro.errno == 1045:
                print("Acesso negado. Confira usuário, senha e permissões.")
            elif erro.errno == 1049:
                print("Banco não encontrado. Execute primeiro o modelo físico no Workbench.")
            else:
                print(f"Falha no MySQL (código {erro.errno}). Confira a conexão, a estrutura e as permissões.")
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrado.")
            break


if __name__ == "__main__":
    main()
