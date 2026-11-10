from .catalogo import id_campo
from .conexao import abrir_conexao


def _chamar(nome, args=()):
    with abrir_conexao() as con:
        cur = con.cursor()
        try:
            cur.callproc(nome, args)
            return [linhas for r in cur.stored_results() for linhas in r.fetchall()]
        finally:
            cur.close()


def conta_usuarios(id_arquivo):
    return _chamar('Conta_usuários', (id_campo('id_arquivo').converter(id_arquivo),))[0][0]


def remover_acessos(id_arquivo):
    _chamar('Remover_acessos', (id_campo('id_arquivo').converter(id_arquivo),))


def verificar_atividades():
    _chamar('Verificar_atividades')


def chavear(id_arquivo):
    _chamar('Chavear', (id_campo('id_arquivo').converter(id_arquivo),))
