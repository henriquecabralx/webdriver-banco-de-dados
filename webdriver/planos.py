"""CRUD da tabela plano, com os campos do modelo físico enviado."""
from .conexao import abrir_conexao


def inteiro_positivo(valor, campo, limite=18446744073709551615):
    if isinstance(valor, bool) or not isinstance(valor, int) or not 0 < valor <= limite:
        raise ValueError(f"{campo} deve ser um inteiro entre 1 e {limite}.")
    return valor


def validar(nome, duracao_dias, espaco_por_usuario_bytes):
    if not isinstance(nome, str) or not nome.strip() or len(nome.strip()) > 100:
        raise ValueError("Nome deve conter entre 1 e 100 caracteres.")
    inteiro_positivo(duracao_dias, "Duração", 4294967295)
    inteiro_positivo(espaco_por_usuario_bytes, "Espaço em bytes")
    return nome.strip()


def executar(sql, parametros=(), consulta=False, insercao=False):
    with abrir_conexao() as conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute(sql, parametros)
            if consulta:
                return cursor.fetchall()
            return cursor.lastrowid if insercao else cursor.rowcount
        finally:
            cursor.close()


def criar(nome, duracao_dias, espaco_por_usuario_bytes):
    nome = validar(nome, duracao_dias, espaco_por_usuario_bytes)
    return executar(
        "INSERT INTO plano (nome, duracao_dias, espaco_por_usuario_bytes) VALUES (%s, %s, %s)",
        (nome, duracao_dias, espaco_por_usuario_bytes), insercao=True,
    )


def listar():
    return executar("SELECT id_plano, nome, duracao_dias, espaco_por_usuario_bytes FROM plano ORDER BY id_plano", consulta=True)


def buscar(id_plano):
    inteiro_positivo(id_plano, "ID")
    registros = executar("SELECT id_plano, nome, duracao_dias, espaco_por_usuario_bytes FROM plano WHERE id_plano = %s", (id_plano,), consulta=True)
    return registros[0] if registros else None


def atualizar(id_plano, nome, duracao_dias, espaco_por_usuario_bytes):
    inteiro_positivo(id_plano, "ID")
    nome = validar(nome, duracao_dias, espaco_por_usuario_bytes)
    # A consulta bloqueada distingue registro inexistente de atualização sem mudança.
    with abrir_conexao() as conexao:
        cursor = conexao.cursor()
        try:
            cursor.execute("SELECT id_plano FROM plano WHERE id_plano = %s FOR UPDATE", (id_plano,))
            if cursor.fetchone() is None:
                return False
            cursor.execute("UPDATE plano SET nome=%s, duracao_dias=%s, espaco_por_usuario_bytes=%s WHERE id_plano=%s", (nome, duracao_dias, espaco_por_usuario_bytes, id_plano))
            return True
        finally:
            cursor.close()


def excluir(id_plano):
    inteiro_positivo(id_plano, "ID")
    # A FK existente impede excluir planos vinculados a instituições.
    return executar("DELETE FROM plano WHERE id_plano = %s", (id_plano,)) > 0
