"""Testes isolados: não abrem conexão nem simulam execução real do SQL."""
import importlib
import sys
import types
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

# Permite testar regras sem instalar o driver; nenhuma chamada real usa o substituto.
try:
    import mysql.connector
except ImportError:
    driver = types.ModuleType('mysql.connector')
    driver.connect = MagicMock()
    mysql = types.ModuleType('mysql')
    mysql.connector = driver
    with patch.dict(sys.modules, {'mysql': mysql, 'mysql.connector': driver}):
        from webdriver import conexao, repositorio, arquivos, historicos
        from webdriver.catalogo import Campo, ENTIDADES, validar_dados
else:
    from webdriver import conexao, repositorio, arquivos, historicos
    from webdriver.catalogo import Campo, ENTIDADES, validar_dados


@contextmanager
def fornecer(con):
    yield con


class Validacoes(unittest.TestCase):
    def test_inteiros_datas_e_opcionais(self):
        for valor in (-1, 0, True, 1.5, '1 OR 1=1'):
            with self.assertRaises(ValueError):
                Campo('id', 'inteiro', 100).converter(valor)
        self.assertIsNone(Campo('data_nascimento', 'data', opcional=True).converter(''))
        with self.assertRaises(ValueError):
            Campo('dia', 'data').converter('2026-02-30')
        with self.assertRaises(ValueError):
            Campo('data_nascimento', 'data').converter('9999-01-01')

    def test_senha_usa_sal_e_nao_aparece_no_select(self):
        campo = Campo('senha_hash', 'senha')
        a, b = campo.converter('SenhaTeste123'), campo.converter('SenhaTeste123')
        self.assertNotEqual(a, b)
        self.assertTrue(a.startswith('pbkdf2_sha256$600000$'))
        self.assertNotIn('SenhaTeste123', a)
        self.assertNotIn('senha_hash', ENTIDADES['usuarios'].colunas)

    def test_campo_sql_arbitrario_recusado(self):
        with self.assertRaises(ValueError):
            validar_dados(ENTIDADES['usuarios'], {'nome; DROP TABLE usuario': 'x'}, True)
        with self.assertRaises(ValueError):
            repositorio.definir('usuario; DROP TABLE plano')

    def test_arquivo_vazio_e_permissao(self):
        dados = dict(nome='a', tipo='text/plain', permissao_acesso='PRIVADO', tamanho_bytes=0, localizacao='/a', url='https://example.com/a')
        self.assertEqual(arquivos.parametros(dados)[3], 0)
        for tamanho in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                arquivos.parametros({**dados, 'tamanho_bytes': tamanho})
        with self.assertRaises(ValueError):
            arquivos.parametros({**dados, 'permissao_acesso': 'OUTRA'})


class Repositorio(unittest.TestCase):
    def setUp(self):
        self.con = MagicMock()
        self.cur = self.con.cursor.return_value
        self.patch = patch.object(repositorio, 'abrir_conexao', lambda: fornecer(self.con))
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_texto_e_parametro_nao_sql(self):
        malicioso = "teste'); DROP TABLE instituicao; --"
        repositorio.criar('instituicoes', dict(nome=malicioso, causa_social='Educação', endereco='Recife', id_plano=1, data_aquisicao='2026-11-06'))
        sql, params = self.cur.execute.call_args.args
        self.assertNotIn(malicioso, sql)
        self.assertIn(malicioso, params)
        self.cur.close.assert_called_once()

    def test_chave_composta_exige_todos_os_ids(self):
        with self.assertRaises(ValueError):
            repositorio.excluir('compartilhamentos', {'id_arquivo': 1})
        self.cur.rowcount = 1
        self.assertTrue(repositorio.excluir('compartilhamentos', {'id_arquivo': 1, 'id_compartilhado': 2}))
        sql, params = self.cur.execute.call_args.args
        self.assertIn('`id_arquivo`=%s AND `id_compartilhado`=%s', sql)
        self.assertEqual(params, (1, 2))

    def test_atualizacao_sem_mudanca_e_inexistente(self):
        self.cur.fetchone.return_value = (1,)
        self.cur.rowcount = 0
        self.assertTrue(repositorio.atualizar('administradores', {'id_administrador': 1}, {'id_usuario': 2}))
        self.cur.fetchone.return_value = None
        self.cur.reset_mock()
        self.assertFalse(repositorio.atualizar('administradores', {'id_administrador': 999}, {'id_usuario': 2}))
        self.assertEqual(self.cur.execute.call_count, 1)

    def test_paginas_e_historico_nao_entra_no_crud(self):
        repositorio.listar('usuarios', pagina=2)
        sql, params = self.cur.execute.call_args.args
        self.assertNotIn('senha_hash', sql)
        self.assertEqual(params, (100, 100))
        with self.assertRaises(ValueError):
            repositorio.excluir('versoes', {'id_versionamento': 1})


class Procedures(unittest.TestCase):
    def test_chama_procedure_com_out_id(self):
        con = MagicMock()
        cur = con.cursor.return_value
        cur.callproc.return_value = (1, 'a', 'text/plain', 'PRIVADO', 0, '/a', 'url', 42)
        with patch.object(arquivos, 'abrir_conexao', lambda: fornecer(con)):
            resultado = arquivos.criar(1, dict(nome='a', tipo='text/plain', permissao_acesso='PRIVADO', tamanho_bytes=0, localizacao='/a', url='url'))
        self.assertEqual(resultado, {'id_arquivo': 42})
        cur.callproc.assert_called_once_with('sp_carregar_arquivo', (1, 'a', 'text/plain', 'PRIVADO', 0, '/a', 'url', 0))
        cur.execute.assert_not_called()
        cur.close.assert_called_once()

    def test_remocao_logica_usa_procedure(self):
        with patch.object(arquivos, 'procedimento') as chamar:
            arquivos.excluir('1', '2')
        chamar.assert_called_once_with('sp_remover_arquivo', (1, 2))


class Transacoes(unittest.TestCase):
    def configuracao(self):
        import configparser
        config = configparser.ConfigParser(interpolation=None)
        config.read_string('[mysql]\nuser=teste\npassword=teste\n')
        return config

    def test_erro_faz_rollback_e_fecha(self):
        con = MagicMock()
        config = self.configuracao()
        with patch.object(conexao.configparser, 'ConfigParser', return_value=config), patch.object(config, 'read', return_value=['config.ini']), patch.object(conexao.mysql.connector, 'connect', return_value=con):
            with self.assertRaises(RuntimeError):
                with conexao.abrir_conexao():
                    raise RuntimeError('erro controlado')
        con.rollback.assert_called_once()
        con.commit.assert_not_called()
        con.close.assert_called_once()

    def test_sucesso_confirma_e_fecha(self):
        con = MagicMock()
        config = self.configuracao()
        with patch.object(conexao.configparser, 'ConfigParser', return_value=config), patch.object(config, 'read', return_value=['config.ini']), patch.object(conexao.mysql.connector, 'connect', return_value=con):
            with conexao.abrir_conexao():
                pass
        con.commit.assert_called_once()
        con.rollback.assert_not_called()
        con.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
