from .catalogo import id_campo
from .conexao import abrir_conexao

TABELAS = {'operacoes': ('operacao_arquivo', 'id_operacao'), 'versoes': ('versionamento', 'id_versionamento')}


def consultar(tipo, id_arquivo=None, pagina=1):
    if tipo not in TABELAS:
        raise ValueError('Histórico inválido.')
    tabela, chave = TABELAS[tipo]
    pagina = id_campo('pagina').converter(pagina)
    parametros = []
    where = ''
    if id_arquivo is not None:
        where = 'WHERE id_arquivo=%s'
        parametros.append(id_campo('id_arquivo').converter(id_arquivo))
    parametros.append((pagina-1)*100)
    with abrir_conexao() as con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute(f'SELECT * FROM {tabela} {where} ORDER BY {chave} DESC LIMIT 100 OFFSET %s', tuple(parametros))
            return cur.fetchall()
        finally:
            cur.close()
