"""Entidades do domínio (camada Model do MVC).

Cada classe corresponde a uma tabela do banco de dados (ver o DER e o
Diagrama de Classes na documentação): Usuario, Cliente, Pet, Servico e
Agendamento.
"""
import enum
from datetime import date, datetime, timedelta

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


# ---------------------------------------------------------------------------
# Enumerações: o NOME é gravado no banco e o VALOR é o rótulo exibido na tela.
# ---------------------------------------------------------------------------
class Perfil(enum.Enum):
    ADMIN = "Administrador"
    ATENDENTE = "Atendente"


class Especie(enum.Enum):
    CAO = "Cão"
    GATO = "Gato"
    OUTRO = "Outro"


class Porte(enum.Enum):
    PEQUENO = "Pequeno"
    MEDIO = "Médio"
    GRANDE = "Grande"


class StatusAgendamento(enum.Enum):
    AGENDADO = "Agendado"
    CONCLUIDO = "Concluído"
    CANCELADO = "Cancelado"


def _coluna_enum(tipo):
    """Enum gravado como texto (VARCHAR) com restrição CHECK no banco."""
    return db.Enum(tipo, native_enum=False, create_constraint=True,
                   length=20, validate_strings=True)


# ---------------------------------------------------------------------------
# Entidades
# ---------------------------------------------------------------------------
class Usuario(db.Model):
    """Funcionário que acessa o sistema (Atendente ou Administrador)."""

    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(_coluna_enum(Perfil), nullable=False, default=Perfil.ATENDENTE)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    agendamentos = db.relationship("Agendamento", back_populates="usuario",
                                   passive_deletes="all")

    def definir_senha(self, senha):
        """Armazena somente o hash da senha, nunca o texto puro (RNF01)."""
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_admin(self):
        return self.perfil == Perfil.ADMIN

    def __repr__(self):
        return f"<Usuario {self.email}>"


class Cliente(db.Model):
    """Tutor (dono) dos pets atendidos pelo pet shop."""

    __tablename__ = "cliente"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), nullable=False, unique=True)
    telefone = db.Column(db.String(11), nullable=False)
    email = db.Column(db.String(120))
    endereco = db.Column(db.String(200))
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    pets = db.relationship("Pet", back_populates="cliente", order_by="Pet.nome",
                           passive_deletes="all")

    @property
    def cpf_formatado(self):
        c = self.cpf or ""
        return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}" if len(c) == 11 else c

    @property
    def telefone_formatado(self):
        t = self.telefone or ""
        if len(t) == 11:
            return f"({t[:2]}) {t[2:7]}-{t[7:]}"
        if len(t) == 10:
            return f"({t[:2]}) {t[2:6]}-{t[6:]}"
        return t

    def possui_pets(self):
        return len(self.pets) > 0

    def __repr__(self):
        return f"<Cliente {self.nome}>"


class Pet(db.Model):
    """Animal de estimação vinculado a um cliente (RN02)."""

    __tablename__ = "pet"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id", ondelete="RESTRICT"),
                           nullable=False, index=True)
    nome = db.Column(db.String(60), nullable=False)
    especie = db.Column(_coluna_enum(Especie), nullable=False)
    raca = db.Column(db.String(60))
    porte = db.Column(_coluna_enum(Porte), nullable=False)
    data_nascimento = db.Column(db.Date)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    cliente = db.relationship("Cliente", back_populates="pets")
    agendamentos = db.relationship("Agendamento", back_populates="pet",
                                   passive_deletes="all")

    def idade(self, hoje=None):
        """Idade em anos completos (ou None se a data de nascimento não foi informada)."""
        if not self.data_nascimento:
            return None
        hoje = hoje or date.today()
        nasc = self.data_nascimento
        return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))

    @property
    def idade_texto(self):
        anos = self.idade()
        if anos is None:
            return "—"
        if anos >= 1:
            return f"{anos} ano" if anos == 1 else f"{anos} anos"
        hoje, nasc = date.today(), self.data_nascimento
        meses = (hoje.year - nasc.year) * 12 + hoje.month - nasc.month - (hoje.day < nasc.day)
        return f"{max(meses, 0)} {'mês' if meses == 1 else 'meses'}"

    def possui_agendamentos(self):
        return len(self.agendamentos) > 0

    def __repr__(self):
        return f"<Pet {self.nome}>"


class Servico(db.Model):
    """Serviço oferecido pelo pet shop (banho, tosa etc.)."""

    __tablename__ = "servico"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    duracao_minutos = db.Column(db.Integer, nullable=False)
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    agendamentos = db.relationship("Agendamento", back_populates="servico",
                                   passive_deletes="all")

    def possui_agendamentos(self):
        return len(self.agendamentos) > 0

    def __repr__(self):
        return f"<Servico {self.nome}>"


class Agendamento(db.Model):
    """Reserva de um serviço para um pet em uma data e horário."""

    __tablename__ = "agendamento"

    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey("pet.id", ondelete="RESTRICT"),
                       nullable=False, index=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servico.id", ondelete="RESTRICT"),
                           nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id", ondelete="RESTRICT"),
                           nullable=False, index=True)
    data_hora_inicio = db.Column(db.DateTime, nullable=False, index=True)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(_coluna_enum(StatusAgendamento), nullable=False,
                       default=StatusAgendamento.AGENDADO)
    observacoes = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.now)

    pet = db.relationship("Pet", back_populates="agendamentos")
    servico = db.relationship("Servico", back_populates="agendamentos")
    usuario = db.relationship("Usuario", back_populates="agendamentos")

    @staticmethod
    def calcular_fim(inicio, duracao_minutos):
        """RN06: o término é calculado pela duração do serviço."""
        return inicio + timedelta(minutes=duracao_minutos)

    @classmethod
    def existe_conflito(cls, inicio, fim, ignorar_id=None):
        """RN04: há outro agendamento ativo que se sobrepõe ao período?"""
        consulta = db.select(cls.id).where(
            cls.status == StatusAgendamento.AGENDADO,
            cls.data_hora_inicio < fim,
            cls.data_hora_fim > inicio,
        )
        if ignorar_id is not None:
            consulta = consulta.where(cls.id != ignorar_id)
        return db.session.execute(consulta.limit(1)).first() is not None

    def pode_alterar(self):
        """RN07: somente agendamentos com status Agendado podem ser alterados."""
        return self.status == StatusAgendamento.AGENDADO

    def concluir(self):
        self._mudar_status(StatusAgendamento.CONCLUIDO)

    def cancelar(self):
        self._mudar_status(StatusAgendamento.CANCELADO)

    def _mudar_status(self, novo_status):
        if not self.pode_alterar():
            raise ValueError("Somente agendamentos com status Agendado podem ser alterados.")
        self.status = novo_status

    def __repr__(self):
        return f"<Agendamento {self.id} {self.data_hora_inicio:%d/%m/%Y %H:%M}>"
