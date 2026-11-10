from .catalogo import ENTIDADES, id_campo, validar_dados
from .conexao import abrir_conexao


def definir(nome):
    if nome not in ENTIDADES:
        raise ValueError('Cadastro inválido.')
    return ENTIDADES[nome]


def filtro(entidade, chaves):
    if set(chaves) != set(entidade.chaves):
        raise ValueError('Informe todas as chaves do registro.')
    return (' AND '.join(f'`{c}`=%s' for c in entidade.chaves),
            tuple(id_campo(c).converter(chaves[c]) for c in entidade.chaves))


def listar(nome, limite=100, pagina=1):
    e = definir(nome)
    limite = id_campo('limite').converter(limite)
    pagina = id_campo('pagina').converter(pagina)
    if limite > 1000:
        raise ValueError('Limite máximo: 1000 registros por página.')
    with abrir_conexao() as con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute(f'SELECT {",".join(e.colunas)} FROM `{e.tabela}` ORDER BY {",".join(e.chaves)} LIMIT %s OFFSET %s', (limite, (pagina-1)*limite))
            return cur.fetchall()
        finally:
            cur.close()


def buscar(nome, chaves):
    e = definir(nome)
    where, parametros = filtro(e, chaves)
    with abrir_conexao() as con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute(f'SELECT {",".join(e.colunas)} FROM `{e.tabela}` WHERE {where}', parametros)
            return cur.fetchone()
        finally:
            cur.close()


def criar(nome, dados):
    e = definir(nome)
    dados = validar_dados(e, dados)
    with abrir_conexao() as con:
        cur = con.cursor()
        try:
            cur.execute(f'INSERT INTO `{e.tabela}` ({",".join(dados)}) VALUES ({",".join(["%s"]*len(dados))})', tuple(dados.values()))
            return {e.chaves[0]: cur.lastrowid} if e.automatica else {c: dados[c] for c in e.chaves}
        finally:
            cur.close()


def atualizar(nome, chaves, dados):
    e = definir(nome)
    where, parametros = filtro(e, chaves)
    dados = validar_dados(e, dados, parcial=True)
    with abrir_conexao() as con:
        cur = con.cursor()
        try:
            cur.execute(f'SELECT {",".join(e.chaves)} FROM `{e.tabela}` WHERE {where} FOR UPDATE', parametros)
            if cur.fetchone() is None:
                return False
            cur.execute(f'UPDATE `{e.tabela}` SET {",".join(f"`{c}`=%s" for c in dados)} WHERE {where}', (*dados.values(), *parametros))
            return True
        finally:
            cur.close()


def excluir(nome, chaves):
    e = definir(nome)
    where, parametros = filtro(e, chaves)
    with abrir_conexao() as con:
        cur = con.cursor()
        try:
            cur.execute(f'DELETE FROM `{e.tabela}` WHERE {where}', parametros)
            return cur.rowcount > 0
        finally:
            cur.close()
