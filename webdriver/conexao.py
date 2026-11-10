import configparser
from contextlib import contextmanager
from pathlib import Path

import mysql.connector


@contextmanager
def abrir_conexao():
    caminho = Path(__file__).resolve().parent.parent / "config.ini"
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(caminho, encoding="utf-8") or "mysql" not in config:
        raise ValueError("Copie config.example.ini para config.ini e configure o MySQL.")
    secao = config["mysql"]
    if not secao.get("user"):
        raise ValueError("Preencha user em config.ini.")
    conexao = mysql.connector.connect(
        host=secao.get("host", "localhost"),
        port=secao.getint("port", 3306),
        user=secao["user"], password=secao.get("password", ""),
        database=secao.get("database", "webdriver"),
        connection_timeout=10, autocommit=False,
    )
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()
