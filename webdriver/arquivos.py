"""Metadados de arquivos via procedimentos existentes; sem gravar histórico à mão."""
from .conexao import abrir_conexao
from .catalogo import Campo, id_campo

COLUNAS = 'id_arquivo,id_dono,nome,tipo,permissao_acesso,tamanho_bytes,ultima_modificacao,localizacao,url,excluido_em'
CAMPOS = (Campo('nome', limite=255), Campo('tipo', limite=120), Campo('permissao_acesso', escolhas=('PRIVADO','COMPARTILHADO','PUBLICO')), Campo('localizacao'), Campo('url'))


def parametros(dados):
    esperado = {c.nome for c in CAMPOS} | {'tamanho_bytes'}
    if set(dados) != esperado:
        raise ValueError('Informe nome, tipo, permissao_acesso, tamanho_bytes, localizacao e url.')
    valores = {c.nome: c.converter(dados[c.nome]) for c in CAMPOS}
    tamanho = dados['tamanho_bytes']
    if isinstance(tamanho, bool) or not str(tamanho).isdigit() or not 0 <= int(tamanho) <= 18446744073709551615:
        raise ValueError('Tamanho deve ser um inteiro não negativo em bytes.')
    return (valores['nome'], valores['tipo'], valores['permissao_acesso'], int(tamanho), valores['localizacao'], valores['url'])


def procedimento(nome, args):
    with abrir_conexao() as con:
        cur = con.cursor()
        try:
            return cur.callproc(nome, args)
        finally:
            cur.close()


def criar(id_dono, dados):
    dono = id_campo('id_dono').converter(id_dono)
    resultado = procedimento('sp_carregar_arquivo', (dono, *parametros(dados), 0))
    return {'id_arquivo': resultado[-1]}


def atualizar(id_arquivo, id_usuario, dados):
    procedimento('sp_atualizar_arquivo', (id_campo('id_arquivo').converter(id_arquivo), id_campo('id_usuario').converter(id_usuario), *parametros(dados)))


def excluir(id_arquivo, id_usuario):
    procedimento('sp_remover_arquivo', (id_campo('id_arquivo').converter(id_arquivo), id_campo('id_usuario').converter(id_usuario)))


def listar(pagina=1, incluir_excluidos=False):
    pagina = id_campo('pagina').converter(pagina)
    with abrir_conexao() as con:
        cur = con.cursor(dictionary=True)
        try:
            where = '' if incluir_excluidos else 'WHERE excluido_em IS NULL'
            cur.execute(f'SELECT {COLUNAS} FROM arquivo {where} ORDER BY id_arquivo LIMIT 100 OFFSET %s', ((pagina-1)*100,))
            return cur.fetchall()
        finally:
            cur.close()


def buscar(id_arquivo):
    with abrir_conexao() as con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute(f'SELECT {COLUNAS} FROM arquivo WHERE id_arquivo=%s', (id_campo('id_arquivo').converter(id_arquivo),))
            return cur.fetchone()
        finally:
            cur.close()
