"""Testes de integracao da Parte 2 em MySQL REAL (permissoes, procedures, funcao, triggers).

Nao rodam por padrao. Exigem MySQL 8.0.16+ , o cliente `mysql` no PATH e uma conta root:
    WEBDRIVER_TEST_MYSQL=1 [WEBDRIVER_TEST_ROOT_USER=root] [WEBDRIVER_TEST_ROOT_PASSWORD=...]
    [WEBDRIVER_TEST_SOCKET=/var/run/mysqld/mysqld.sock | WEBDRIVER_TEST_HOST=127.0.0.1]
    python -m unittest tests.test_seguranca_mysql -v
Os scripts 01-08 sao carregados em um banco descartavel (webdriver_teste) com roles de nome
TstPapel*; contas t* sao criadas e removidas. O banco `webdriver` e as roles reais nao sao tocados.
"""
import os
import re
import shutil
import subprocess
import unittest
import warnings
from pathlib import Path

try:
    import mysql.connector
    from mysql.connector import errors
except ImportError:  # pragma: no cover
    mysql = None

warnings.filterwarnings('ignore', category=DeprecationWarning, module='tests')
RAIZ = Path(__file__).resolve().parent.parent
DB = 'webdriver_teste'
SENHA = 'Senha#Teste1'
ROOT_USER = os.environ.get('WEBDRIVER_TEST_ROOT_USER', 'root')
ROOT_PASS = os.environ.get('WEBDRIVER_TEST_ROOT_PASSWORD', '')
HOST = os.environ.get('WEBDRIVER_TEST_HOST')
SOCKET = os.environ.get('WEBDRIVER_TEST_SOCKET', '/var/run/mysqld/mysqld.sock')
ATIVO = os.environ.get('WEBDRIVER_TEST_MYSQL') == '1' and mysql is not None and shutil.which('mysql')
ROLES = {'PapelUsuario': 'TstPapelUsuario', 'PapelEmpresa': 'TstPapelEmpresa', 'PapelAdm': 'TstPapelAdm'}
# login: (instituicao, role, administrador?)
CONTAS = {'tana': ('A', 'PapelUsuario', False), 'tbia': ('A', 'PapelUsuario', False),
          'tcarlos': ('B', 'PapelUsuario', False), 'tdani': ('A', 'PapelAdm', True),
          'tempa': ('A', 'PapelEmpresa', False), 'tempb': ('B', 'PapelEmpresa', False),
          'tfalso': ('A', 'PapelAdm', False)}  # tem a role de admin mas NAO esta em administrador


def conectar(user=ROOT_USER, senha=ROOT_PASS, db=None):
    args = dict(user=user, password=senha, autocommit=True, charset='utf8mb4')
    args.update({'host': HOST} if HOST else {'unix_socket': SOCKET})
    if db:
        args['database'] = db
    return mysql.connector.connect(**args)


def cli(sql, extra=()):
    cmd = ['mysql', '-u', ROOT_USER, '--default-character-set=utf8mb4', *extra]
    cmd += ['-h', HOST] if HOST else ['-S', SOCKET]
    subprocess.run(cmd, input=sql.encode('utf-8'), check=True, stdout=subprocess.DEVNULL, env={**os.environ, 'MYSQL_PWD': ROOT_PASS})


def adaptar(sql):
    sql = re.sub(r'\bwebdriver\b', DB, sql)
    for real, teste in ROLES.items():
        sql = sql.replace(real, teste)
    return sql


@unittest.skipUnless(ATIVO, 'defina WEBDRIVER_TEST_MYSQL=1 com MySQL e cliente mysql disponiveis')
class SegurancaMySQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.limpar_servidor()
        for n in sorted((RAIZ / 'sql').glob('0[1-8]-*.sql')):
            cli(adaptar(n.read_text(encoding='utf-8')))
        root = conectar()
        c = root.cursor()
        for login, (_, role, _) in CONTAS.items():
            c.execute(f"CREATE USER '{login}'@'localhost' IDENTIFIED BY '{SENHA}'")
            c.execute(f"GRANT {ROLES[role]} TO '{login}'@'localhost'")
            c.execute(f"SET DEFAULT ROLE {ROLES[role]} TO '{login}'@'localhost'")
        root.close()

    @classmethod
    def limpar_servidor(cls):
        root = conectar()
        c = root.cursor()
        c.execute(f'DROP DATABASE IF EXISTS {DB}')
        for login in CONTAS:
            c.execute(f"DROP USER IF EXISTS '{login}'@'localhost'")
        for r in ROLES.values():
            c.execute(f'DROP ROLE IF EXISTS {r}')
        root.close()

    @classmethod
    def tearDownClass(cls):
        cls.limpar_servidor()

    def setUp(self):
        self.root = conectar(db=DB)
        c = self.root.cursor()
        c.execute('SET FOREIGN_KEY_CHECKS=0')
        for t in ('atividades_recentes', 'suporte_adm', 'suporte', 'versionamento', 'operacao_arquivo', 'comentario',
                  'compartilhamento', 'arquivo', 'administrador', 'usuario', 'instituicao', 'plano'):
            c.execute(f'TRUNCATE TABLE {t}')
        c.execute('SET FOREIGN_KEY_CHECKS=1')
        c.execute("INSERT INTO plano(nome,duracao_dias,espaco_por_usuario_bytes) VALUES('p',30,1000000000)")
        c.execute("INSERT INTO instituicao(nome,causa_social,endereco,id_plano,data_aquisicao) VALUES('A','x','x',1,CURDATE()),('B','x','x',1,CURDATE())")
        for login, (inst, _, adm) in CONTAS.items():
            c.execute("INSERT INTO usuario(nome,login,senha_hash,data_ingresso,email,id_instituicao) VALUES(%s,%s,'h',CURDATE(),%s,%s)",
                      (login, login, login + '@x.com', 1 if inst == 'A' else 2))
            if adm:
                c.execute('INSERT INTO administrador(id_usuario) VALUES(LAST_INSERT_ID())')
        self.con = {}
        self.addCleanup(self.fechar)
        self.carregar('tana', 'ana_priv.txt', 'PRIVADO')
        self.carregar('tana', 'ana_comp.txt', 'COMPARTILHADO')
        self.carregar('tana', 'ana_pub.txt', 'PUBLICO')
        self.carregar('tbia', 'bia_priv.txt', 'PRIVADO')
        self.carregar('tcarlos', 'carlos_doc.txt', 'PRIVADO')
        self.comp = self.id_arquivo('ana_comp.txt')
        c.execute('INSERT INTO compartilhamento(id_arquivo,id_dono,id_compartilhado) SELECT %s,id_usuario,(SELECT id_usuario FROM usuario WHERE login=%s) FROM usuario WHERE login=%s',
                  (self.comp, 'tbia', 'tana'))

    def fechar(self):
        for x in list(self.con.values()) + [self.root]:
            x.close()

    def como(self, login):
        if login not in self.con:
            self.con[login] = conectar(login, SENHA, DB)
        return self.con[login]

    def carregar(self, login, nome, perm='PRIVADO', tipo='text/plain'):
        self.chamar(login, 'usr_carregar_arquivo', (nome, tipo, perm, 10, '/' + nome, 'http://x/' + nome))

    def chamar(self, login, proc, args=()):
        c = self.como(login).cursor()
        c.callproc(proc, args)
        return [r.fetchall() for r in c.stored_results()]

    def consultar(self, login, sql, args=()):
        c = self.como(login).cursor()
        c.execute(sql, args)
        return c.fetchall()

    def raiz(self, sql, args=()):
        c = self.root.cursor()
        c.execute(sql, args)
        return c.fetchall() if c.with_rows else None

    def proc_raiz(self, proc, args=()):
        c = self.root.cursor()
        c.callproc(proc, args)
        return [r.fetchall() for r in c.stored_results()][0][0][0]

    def id_arquivo(self, nome):
        return self.raiz('SELECT id_arquivo FROM arquivo WHERE nome=%s', (nome,))[0][0]

    def nomes(self, login):
        return {r[0] for r in self.consultar(login, 'SELECT nome_arquivo FROM vw_arquivos_autorizados')}

    def nega(self, login, sql, args=(), proc=False):
        with self.assertRaises(errors.Error) as e:
            (self.chamar(login, sql, args) if proc else self.consultar(login, sql, args))
        return e.exception

    # 1-3
    def test_usuario_nao_ve_privado_de_outro_e_ve_proprios_e_compartilhados(self):
        self.assertNotIn('bia_priv.txt', self.nomes('tana'))
        self.assertIn('ana_priv.txt', self.nomes('tana'))
        bia = self.nomes('tbia')
        self.assertTrue({'bia_priv.txt', 'ana_comp.txt', 'ana_pub.txt'} <= bia)
        self.assertNotIn('ana_priv.txt', bia)
        carlos = self.nomes('tcarlos')
        self.assertNotIn('ana_comp.txt', carlos)
        self.assertNotIn('bia_priv.txt', carlos)

    # 4 + identidade
    def test_usuario_nao_altera_sem_autorizacao_nem_assume_identidade(self):
        args = ('ana_comp.txt', 'x.txt', 'text/plain', 'PRIVADO', 1, '/x', 'http://x')
        self.assertEqual(self.nega('tbia', 'usr_atualizar_arquivo', args, True).errno, 1644)  # compartilhado, nao dono
        self.nega('tbia', 'UPDATE arquivo SET nome=%s', ('hack',))
        self.assertEqual(self.nega('tbia', 'sp_atualizar_arquivo', (self.comp, 1, 'x', 'text/plain', 'PRIVADO', 1, '/x', 'u'), True).errno, 1370)
        self.assertEqual(self.nega('tbia', 'sp_carregar_arquivo', (1, 'a', 'text/plain', 'PRIVADO', 1, '/a', 'u', 0), True).errno, 1370)
        # dono e sempre a conta conectada
        self.assertEqual(self.raiz("SELECT u.login FROM arquivo a JOIN usuario u ON u.id_usuario=a.id_dono WHERE a.nome='bia_priv.txt'")[0][0], 'tbia')
        # as procedures de usuario nao recebem ID algum
        ids = self.raiz("SELECT parameter_name FROM information_schema.parameters WHERE specific_schema=%s AND specific_name LIKE 'usr\\_%%' AND parameter_name LIKE '%%id%%'", (DB,))
        self.assertEqual(ids, [])
        # o proprio dono atualiza
        self.chamar('tana', 'usr_atualizar_arquivo', ('ana_priv.txt', 'ana_novo.txt', 'text/plain', 'PRIVADO', 20, '/n', 'http://n'))
        self.assertIn('ana_novo.txt', self.nomes('tana'))

    # 5-6
    def test_empresa_isolada_e_somente_leitura(self):
        a = {r[0] for r in self.consultar('tempa', 'SELECT login FROM vw_empresa_usuarios')}
        b = {r[0] for r in self.consultar('tempb', 'SELECT login FROM vw_empresa_usuarios')}
        self.assertTrue({'tana', 'tbia', 'tdani'} <= a and not ({'tcarlos', 'tempb'} & a))
        self.assertTrue({'tcarlos', 'tempb'} <= b and not ({'tana', 'tbia'} & b))
        fa = {r[0] for r in self.consultar('tempa', 'SELECT nome_arquivo FROM vw_empresa_arquivos')}
        self.assertTrue('ana_priv.txt' in fa and 'carlos_doc.txt' not in fa)
        for sql in ('INSERT INTO usuario(nome) VALUES(1)', 'UPDATE arquivo SET nome=1', 'DELETE FROM arquivo',
                    'UPDATE vw_empresa_arquivos SET tipo=1', 'DELETE FROM vw_empresa_usuarios', 'SELECT * FROM usuario'):
            self.assertEqual(self.nega('tempa', sql).errno, 1142, sql)
        self.assertEqual(self.nega('tempa', 'Remover_acessos', (self.comp,), True).errno, 1370)

    # 7-8
    def test_admin_opera_e_usuario_comum_nao(self):
        adm = self.como('tdani').cursor()
        adm.execute("INSERT INTO plano(nome,duracao_dias,espaco_por_usuario_bytes) VALUES('novo',1,1)")
        adm.execute("UPDATE plano SET nome='novo2' WHERE nome='novo'")
        adm.execute("DELETE FROM plano WHERE nome='novo2'")
        self.assertGreater(len(self.consultar('tdani', 'SELECT * FROM usuario')), 0)
        self.assertGreater(len(self.consultar('tdani', 'SELECT * FROM vw_admin_arquivos')), 0)
        self.assertEqual(self.chamar('tdani', 'Conta_usuários', (self.comp,))[0][0][0], 2)
        self.chamar('tdani', 'Remover_acessos', (self.comp,))
        self.assertEqual(self.raiz('SELECT COUNT(*) FROM compartilhamento')[0][0], 0)
        for login in ('tana', 'tempa'):
            self.assertEqual(self.nega(login, 'Remover_acessos', (self.comp,), True).errno, 1370)
            self.assertEqual(self.nega(login, 'Conta_usuários', (self.comp,), True).errno, 1370)
            self.assertEqual(self.nega(login, 'INSERT INTO plano(nome,duracao_dias,espaco_por_usuario_bytes) VALUES(1,1,1)').errno, 1142)
            self.nega(login, "CREATE USER 'hacker'@'%'")
        # role de admin concedida a conta que nao esta em administrador: a procedure valida a conta
        e = self.nega('tfalso', 'Remover_acessos', (self.comp,), True)
        self.assertIn('administradores', e.msg)
        self.assertIn('administradores', self.nega('tfalso', 'Conta_usuários', (self.comp,), True).msg)

    # 9
    def test_nenhuma_role_acessa_atividades_recentes(self):
        self.carregar('tana', 'recente.txt')
        for login in ('tana', 'tempa', 'tdani', 'tfalso'):
            for sql in ('SELECT * FROM atividades_recentes', 'UPDATE atividades_recentes SET acesso=1',
                        'DELETE FROM atividades_recentes', 'INSERT INTO atividades_recentes(id_arquivo,ultima_versao) VALUES(1,CURDATE())',
                        f'SELECT * FROM {DB}.atividades_recentes', 'SELECT fn_arquivo_inativo(1)'):
                self.assertIn(self.nega(login, sql).errno, (1142, 1370, 1143), (login, sql))
            for proc in ('Verificar_atividades', 'Chavear'):
                self.assertEqual(self.nega(login, proc, (1,) if proc == 'Chavear' else (), True).errno, 1370)
        # nenhum grant (direto ou herdado) das roles menciona a tabela ou rotinas restritas
        for r in ROLES.values():
            texto = ' '.join(x[0] for x in self.raiz(f'SHOW GRANTS FOR {r}'))
            for proibido in ('atividades_recentes', 'Verificar_atividades', 'Chavear', 'fn_arquivo_inativo', '`*`.*', ' ON *.*'):
                self.assertNotIn(proibido, texto.replace('ON *.* TO', '') if proibido == ' ON *.*' else texto)
        self.assertEqual(self.raiz(f"SELECT view_name FROM information_schema.view_table_usage WHERE view_schema='{DB}' AND table_name='atividades_recentes'"), [])
        self.assertEqual(self.raiz("SELECT user FROM mysql.user WHERE user=''"), [])

    # 10
    def test_historico_somente_leitura(self):
        self.assertGreaterEqual(len(self.consultar('tana', 'SELECT * FROM vw_historico_usuario')), 3)
        self.assertEqual({r[2] for r in self.consultar('tana', 'SELECT * FROM vw_historico_usuario')}, {'tana'})
        for sql in ('INSERT INTO operacao_arquivo(id_arquivo,id_usuario,tipo_operacao) VALUES(1,1,1)',
                    'UPDATE operacao_arquivo SET tipo_operacao=1', 'DELETE FROM operacao_arquivo',
                    'DELETE FROM vw_historico_usuario', 'UPDATE vw_historico_usuario SET nome_arquivo=1',
                    'SELECT * FROM operacao_arquivo'):
            self.assertEqual(self.nega('tana', sql).errno, 1142, sql)

    # 11
    def test_executaveis_bloqueados(self):
        for nome, tipo in (('x.exe', 'text/plain'), ('foto.jpg.EXE ', 'image/jpeg'), ('a.bat.', 'text/plain'),
                           ('setup', 'application/x-msdownload'), ('run.sh', 'text/plain'), ('semext', '.exe')):
            e = self.nega('tana', 'usr_carregar_arquivo', (nome, tipo, 'PRIVADO', 1, '/x', 'u'), True)
            self.assertIn('Safe_security', e.msg, nome)
        for nome, tipo in (('relatorio.exe.txt', 'text/plain'), ('exe', 'application/pdf'), ('docs.pdf', 'application/pdf'), ('execucao.docx', 'x')):
            self.carregar('tana', nome, tipo=tipo)
        # desvio por UPDATE (renomear) e insercao direta pelo admin tambem sao barrados
        with self.assertRaises(errors.Error) as e:
            self.chamar('tana', 'usr_atualizar_arquivo', ('ana_priv.txt', 'ana.exe', 'text/plain', 'PRIVADO', 1, '/x', 'u'))
        self.assertIn('Safe_security', e.exception.msg)
        with self.assertRaises(errors.Error):
            self.como('tdani').cursor().execute("INSERT INTO arquivo(id_dono,nome,tipo,tamanho_bytes,localizacao,url) VALUES(1,'v.msi','a',1,'/','u')")

    # 12
    def test_procedures_e_funcao(self):
        fid = self.id_arquivo('ana_priv.txt')
        self.raiz("UPDATE atividades_recentes SET ultima_versao='2000-01-01'")
        self.root.cursor().callproc('Verificar_atividades')
        self.assertEqual(self.raiz('SELECT COUNT(*) FROM atividades_recentes WHERE ultima_versao<>CURDATE()')[0][0], 0)
        self.assertGreater(self.raiz('SELECT COUNT(*) FROM atividades_recentes')[0][0], 0)
        total_usuarios = self.raiz('SELECT COUNT(*) FROM usuario')[0][0]
        self.assertEqual(self.proc_raiz('Conta_usuários', (fid,)), 1)
        self.assertEqual(self.proc_raiz('Conta_usuários', (self.comp,)), 2)
        self.assertEqual(self.proc_raiz('Conta_usuários', (self.id_arquivo('ana_pub.txt'),)), total_usuarios)
        with self.assertRaises(errors.Error):
            self.proc_raiz('Conta_usuários', (999999,))
        self.assertEqual(self.raiz('SELECT acesso FROM atividades_recentes WHERE id_arquivo=%s', (fid,)), [('NAO_PRIORITARIO',)])
        self.root.cursor().callproc('Chavear', (fid,))
        self.assertEqual(self.raiz('SELECT acesso FROM atividades_recentes WHERE id_arquivo=%s', (fid,)), [('PRIORITARIO',)])
        self.root.cursor().callproc('Chavear', (fid,))
        self.assertEqual(self.raiz('SELECT acesso FROM atividades_recentes WHERE id_arquivo=%s', (fid,)), [('NAO_PRIORITARIO',)])
        # Remover_acessos preserva o dono
        self.root.cursor().callproc('Remover_acessos', (self.comp,))
        self.assertEqual(self.raiz('SELECT COUNT(*) FROM compartilhamento')[0][0], 0)
        self.assertIn('ana_comp.txt', self.nomes('tana'))
        self.assertNotIn('ana_comp.txt', self.nomes('tbia'))
        self.assertEqual(self.raiz('SELECT permissao_acesso FROM arquivo WHERE id_arquivo=%s', (self.comp,)), [('PRIVADO',)])
        # funcao: >100 dias
        for dias, esperado in ((101, 1), (100, 0), (0, 0)):
            self.raiz('UPDATE atividades_recentes SET ultima_versao=DATE_SUB(CURDATE(),INTERVAL %s DAY) WHERE id_arquivo=%s', (dias, fid))
            self.assertEqual(self.raiz('SELECT fn_arquivo_inativo(%s)', (fid,)), [(esperado,)], dias)
        self.raiz('DELETE FROM atividades_recentes WHERE id_arquivo=%s', (fid,))
        self.assertEqual(self.raiz('SELECT fn_arquivo_inativo(%s)', (fid,)), [(0,)])

    # 13
    def test_triggers(self):
        fid = self.id_arquivo('ana_priv.txt')
        self.assertEqual(self.raiz('SELECT ultima_versao=CURDATE() FROM atividades_recentes WHERE id_arquivo=%s', (fid,)), [(1,)])
        self.raiz("UPDATE atividades_recentes SET acesso='PRIORITARIO', ultima_versao='2000-01-01' WHERE id_arquivo=%s", (fid,))
        self.chamar('tana', 'usr_atualizar_arquivo', ('ana_priv.txt', 'ana_priv.txt', 'text/plain', 'PRIVADO', 11, '/n', 'u'))
        self.assertEqual(self.raiz('SELECT acesso, ultima_versao=CURDATE() FROM atividades_recentes WHERE id_arquivo=%s', (fid,)), [('PRIORITARIO', 1)])
        # Atualizar_acesso
        self.raiz('DELETE FROM atividades_recentes WHERE id_arquivo=%s', (self.comp,))
        self.raiz('DELETE FROM compartilhamento')
        self.raiz('INSERT INTO compartilhamento(id_arquivo,id_dono,id_compartilhado) SELECT %s,u.id_usuario,(SELECT id_usuario FROM usuario WHERE login=%s) FROM usuario u WHERE u.login=%s',
                  (self.comp, 'tcarlos', 'tana'))
        self.assertEqual(self.raiz('SELECT acesso, ultima_versao=CURDATE() FROM atividades_recentes WHERE id_arquivo=%s', (self.comp,)), [('NAO_PRIORITARIO', 1)])
        self.assertIn('ana_comp.txt', self.nomes('tcarlos'))

    # 14
    def test_views_sem_ids_nem_senhas(self):
        cols = self.raiz("SELECT table_name,column_name FROM information_schema.columns WHERE table_schema=%s AND table_name LIKE 'vw\\_%%'", (DB,))
        self.assertGreater(len(cols), 30)
        for tabela, coluna in cols:
            self.assertFalse(re.match(r'(?i)^id(_|$)|_id$|senha', coluna), (tabela, coluna))


if __name__ == '__main__':
    unittest.main()
