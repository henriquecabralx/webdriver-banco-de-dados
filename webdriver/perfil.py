"""Perfil efetivo da conexão, lido do MySQL (CURRENT_ROLE/CURRENT_USER); nunca informado pelo operador."""
import re
from .conexao import abrir_conexao

ROLES = {'PapelAdm': 'admin', 'PapelEmpresa': 'empresa', 'PapelUsuario': 'usuario'}


def interpretar(current_role, current_user):
    """root tem perfil próprio; demais contas seguem a role ativa de maior privilégio."""
    if current_user.split('@', 1)[0] == 'root':
        return 'root'
    ativas = set(re.findall(r'`([^`]+)`', current_role or ''))
    for role, perfil in ROLES.items():  # ordem = prioridade
        if role in ativas:
            return perfil
    return None


def detectar():
    with abrir_conexao() as con:
        cur = con.cursor()
        try:
            cur.execute('SELECT CURRENT_ROLE(), CURRENT_USER()')
            return interpretar(*cur.fetchone())
        finally:
            cur.close()
