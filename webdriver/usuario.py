from . import arquivos
from .catalogo import id_campo
from .conexao import abrir_conexao


def _listar(view, pagina):
    pagina = id_campo('pagina').converter(pagina)
    with abrir_conexao() as con:
        cur = con.cursor(dictionary=True)
        try:
            cur.execute(f'SELECT * FROM {view} LIMIT 100 OFFSET %s', ((pagina - 1) * 100,))
            return cur.fetchall()
        finally:
            cur.close()


def listar_arquivos(pagina=1):
    return _listar('vw_arquivos_autorizados', pagina)


def historico(pagina=1):
    return _listar('vw_historico_usuario', pagina)


def carregar(dados):
    arquivos.procedimento('usr_carregar_arquivo', arquivos.parametros(dados))


def atualizar(nome_atual, dados):
    arquivos.procedimento('usr_atualizar_arquivo', (arquivos.Campo('nome', limite=255).converter(nome_atual), *arquivos.parametros(dados)))
