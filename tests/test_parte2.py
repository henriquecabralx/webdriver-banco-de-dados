"""Testes isolados (sem MySQL) da integração Python da Parte 2.
As regras de banco são verificadas em tests/test_seguranca_mysql.py."""
import sys
import types
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

try:
    import mysql.connector  # noqa: F401
except ImportError:
    driver = types.ModuleType('mysql.connector')
    driver.connect = MagicMock()
    pacote = types.ModuleType('mysql')
    pacote.connector = driver
    sys.modules.update({'mysql': pacote, 'mysql.connector': driver})

from webdriver import perfil, usuario, empresa, administracao, arquivos  # noqa: E402


@contextmanager
def fornecer(con):
    yield con


def conexao_falsa():
    con = MagicMock()
    cur = con.cursor.return_value
    cur.fetchall.return_value = []
    return con, cur


class Perfil(unittest.TestCase):
    def test_perfil_vem_da_role_e_da_conta(self):
        self.assertEqual(perfil.interpretar('`PapelUsuario`@`%`', 'ana@localhost'), 'usuario')
        self.assertEqual(perfil.interpretar('`PapelEmpresa`@`%`', 'e@localhost'), 'empresa')
        self.assertEqual(perfil.interpretar('`PapelUsuario`@`%`,`PapelAdm`@`%`', 'x@h'), 'admin')
        self.assertEqual(perfil.interpretar('NONE', 'root@localhost'), 'root')
        self.assertIsNone(perfil.interpretar('NONE', 'ana@localhost'))
        self.assertIsNone(perfil.interpretar('`OutraRole`@`%`', 'ana@localhost'))


class Usuario(unittest.TestCase):
    DADOS = {'nome': 'a.txt', 'tipo': 'text/plain', 'permissao_acesso': 'PRIVADO', 'localizacao': '/a', 'url': 'u', 'tamanho_bytes': '5'}

    def test_carregar_e_atualizar_nao_enviam_ids(self):
        con, cur = conexao_falsa()
        with patch.object(arquivos, 'abrir_conexao', lambda: fornecer(con)):
            usuario.carregar(self.DADOS)
            usuario.atualizar('a.txt', {**self.DADOS, 'nome': 'b.txt'})
        (n1, a1), (n2, a2) = [c.args for c in cur.callproc.call_args_list]
        self.assertEqual((n1, a1), ('usr_carregar_arquivo', ('a.txt', 'text/plain', 'PRIVADO', 5, '/a', 'u')))
        self.assertEqual((n2, a2[:2]), ('usr_atualizar_arquivo', ('a.txt', 'b.txt')))
        self.assertEqual(len(a2), 7)

    def test_dados_invalidos_nao_chegam_ao_banco(self):
        con, cur = conexao_falsa()
        with patch.object(arquivos, 'abrir_conexao', lambda: fornecer(con)):
            with self.assertRaises(ValueError):
                usuario.carregar({**self.DADOS, 'permissao_acesso': 'ADMIN'})
            with self.assertRaises(ValueError):
                usuario.carregar({**self.DADOS, 'id_dono': 1})
        cur.callproc.assert_not_called()

    def test_listagens_usam_somente_views(self):
        con, cur = conexao_falsa()
        with patch.object(usuario, 'abrir_conexao', lambda: fornecer(con)):
            usuario.listar_arquivos(2)
            usuario.historico()
            empresa.usuarios()
            empresa.arquivos()
        sqls = [c.args[0] for c in cur.execute.call_args_list]
        self.assertEqual([s.split()[3] for s in sqls], ['vw_arquivos_autorizados', 'vw_historico_usuario', 'vw_empresa_usuarios', 'vw_empresa_arquivos'])
        self.assertEqual(cur.execute.call_args_list[0].args[1], (100,))
        self.assertTrue(all('atividades_recentes' not in s for s in sqls))


class Administracao(unittest.TestCase):
    def test_chamadas_de_procedures(self):
        con, cur = conexao_falsa()
        cur.stored_results.return_value = [MagicMock(fetchall=MagicMock(return_value=[(3,)]))]
        with patch.object(administracao, 'abrir_conexao', lambda: fornecer(con)):
            self.assertEqual(administracao.conta_usuarios('7'), 3)
            administracao.remover_acessos(7)
            administracao.verificar_atividades()
            administracao.chavear(7)
        chamadas = [c.args for c in cur.callproc.call_args_list]
        self.assertEqual(chamadas, [('Conta_usuários', (7,)), ('Remover_acessos', (7,)), ('Verificar_atividades', ()), ('Chavear', (7,))])

    def test_id_invalido(self):
        for f in (administracao.conta_usuarios, administracao.remover_acessos, administracao.chavear):
            for ruim in ('0', '-1', '1 OR 1=1', ''):
                with self.assertRaises(ValueError):
                    f(ruim)


if __name__ == '__main__':
    unittest.main()
