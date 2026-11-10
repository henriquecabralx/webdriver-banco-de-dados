import hashlib
import secrets
from dataclasses import dataclass
from datetime import date, datetime, time


@dataclass(frozen=True)
class Campo:
    nome: str
    tipo: str = 'texto'
    limite: int = 65535
    opcional: bool = False
    escolhas: tuple = ()

    def converter(self, valor):
        if valor is None or valor == '':
            if self.opcional:
                return None
            raise ValueError(f'{self.nome}: preenchimento obrigatório.')
        if self.tipo == 'inteiro':
            if isinstance(valor, bool) or not str(valor).isdigit():
                raise ValueError(f'{self.nome}: informe um inteiro positivo.')
            valor = int(valor)
            if not 1 <= valor <= self.limite:
                raise ValueError(f'{self.nome}: fora do intervalo permitido.')
            return valor
        if self.tipo == 'data':
            valor = date.fromisoformat(str(valor))
            if self.nome == 'data_nascimento' and valor > date.today():
                raise ValueError('Nascimento não pode ser futuro.')
            return valor
        if self.tipo == 'hora':
            return time.fromisoformat(str(valor))
        if self.tipo == 'instante':
            return datetime.fromisoformat(str(valor))
        if self.tipo == 'senha':
            if len(str(valor)) < 8:
                raise ValueError('Senha deve conter pelo menos 8 caracteres.')
            sal = secrets.token_bytes(16)
            resumo = hashlib.pbkdf2_hmac('sha256', str(valor).encode(), sal, 600000)
            return f'pbkdf2_sha256$600000${sal.hex()}${resumo.hex()}'
        valor = str(valor).strip()
        excedeu_bytes_text = self.limite == 65535 and len(valor.encode('utf-8')) > 65535
        if not valor or excedeu_bytes_text or len(valor) > self.limite:
            raise ValueError(f'{self.nome}: texto vazio ou acima do limite ({self.limite}).')
        if self.escolhas and valor not in self.escolhas:
            raise ValueError(f'{self.nome}: escolha entre {", ".join(self.escolhas)}.')
        if self.nome == 'email' and (valor.count('@') != 1 or not all(valor.split('@'))):
            raise ValueError('E-mail inválido.')
        return valor


def id_campo(nome):
    return Campo(nome, 'inteiro', 18446744073709551615)


@dataclass(frozen=True)
class Entidade:
    tabela: str
    chaves: tuple
    campos: tuple
    colunas: tuple
    automatica: bool = True


def entidade(tabela, chave, campos, automatica=True, extras=()):
    chaves = (chave,) if isinstance(chave, str) else chave
    colunas = tuple(dict.fromkeys((*chaves, *(c.nome for c in campos if c.tipo != 'senha'), *extras)))
    return Entidade(tabela, chaves, tuple(campos), colunas, automatica)


ENTIDADES = {
    'instituicoes': entidade('instituicao', 'id_instituicao', [Campo('nome', limite=150), Campo('causa_social'), Campo('endereco'), id_campo('id_plano'), Campo('data_aquisicao', 'data')]),
    'usuarios': entidade('usuario', 'id_usuario', [Campo('nome', limite=150), Campo('data_nascimento', 'data', opcional=True), Campo('login', limite=80), Campo('senha_hash', 'senha'), Campo('data_ingresso', 'data'), Campo('email', limite=254), id_campo('id_instituicao')]),
    'administradores': entidade('administrador', 'id_administrador', [id_campo('id_usuario')]),
    'compartilhamentos': entidade('compartilhamento', ('id_arquivo', 'id_compartilhado'), [id_campo('id_arquivo'), id_campo('id_dono'), id_campo('id_compartilhado')], False, ('data_compartilhamento',)),
    'comentarios': entidade('comentario', 'id_comentario', [id_campo('id_arquivo'), id_campo('id_usuario'), Campo('conteudo')], extras=('data_hora',)),
    'suporte': entidade('suporte', 'id_suporte', [id_campo('id_usuario'), Campo('id_arquivo', 'inteiro', 18446744073709551615, True), Campo('dia', 'data'), Campo('hora', 'hora'), Campo('descricao')]),
    'atendimentos': entidade('suporte_adm', ('id_suporte', 'id_administrador'), [id_campo('id_suporte'), id_campo('id_administrador')], False),
}


def validar_dados(entidade, dados, parcial=False):
    permitidos = {c.nome for c in entidade.campos}
    if set(dados) - permitidos:
        raise ValueError('Campo não permitido.')
    if not dados:
        raise ValueError('Informe ao menos um campo.')
    resultado = {}
    for campo in entidade.campos:
        if campo.nome not in dados and parcial:
            continue
        resultado[campo.nome] = campo.converter(dados.get(campo.nome))
    return resultado
