from .usuario import _listar


def usuarios(pagina=1):
    return _listar('vw_empresa_usuarios', pagina)


def arquivos(pagina=1):
    return _listar('vw_empresa_arquivos', pagina)
