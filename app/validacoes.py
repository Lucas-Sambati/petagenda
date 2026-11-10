"""Validações de formulários e regras de negócio (RN01 a RN09).

Cada função recebe os dados enviados pelo formulário e devolve uma tupla
(dados, erros): ``dados`` contém os valores já limpos/convertidos e ``erros``
é um dicionário {campo: mensagem}. Se ``erros`` estiver vazio, os dados
podem ser gravados no banco.
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import current_app

from .extensions import db
from .models import Agendamento, Cliente, Especie, Pet, Porte, Servico

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Funções auxiliares de conversão
# ---------------------------------------------------------------------------
def somente_digitos(texto):
    return re.sub(r"\D", "", texto or "")


def texto(form, campo):
    return (form.get(campo) or "").strip()


def para_inteiro(valor):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def para_decimal(valor):
    valor = (valor or "").strip()
    if "," in valor:  # aceita o formato brasileiro: 1.234,56
        valor = valor.replace(".", "").replace(",", ".")
    try:
        return Decimal(valor).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def para_data(valor):
    try:
        return datetime.strptime((valor or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def enum_por_nome(tipo, nome):
    try:
        return tipo[nome]
    except (KeyError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Regras de negócio
# ---------------------------------------------------------------------------
def cpf_valido(cpf):
    """RN01: valida o formato e os dois dígitos verificadores do CPF."""
    cpf = somente_digitos(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11 % 10
        if digito != int(cpf[tamanho]):
            return False
    return True


def dentro_do_expediente(inicio, fim):
    """RN05: atendimento de segunda a sábado, das 08h às 18h."""
    cfg = current_app.config
    return (
        inicio.weekday() in cfg["DIAS_FUNCIONAMENTO"]
        and inicio.date() == fim.date()
        and inicio.time() >= cfg["HORA_ABERTURA"]
        and fim.time() <= cfg["HORA_FECHAMENTO"]
    )


# ---------------------------------------------------------------------------
# Validação dos formulários
# ---------------------------------------------------------------------------
def validar_cliente(form, cliente_id=None):
    dados = {
        "nome": texto(form, "nome"),
        "cpf": somente_digitos(form.get("cpf")),
        "telefone": somente_digitos(form.get("telefone")),
        "email": texto(form, "email").lower() or None,
        "endereco": texto(form, "endereco") or None,
    }
    erros = {}

    if not 3 <= len(dados["nome"]) <= 100:
        erros["nome"] = "Informe o nome completo (de 3 a 100 caracteres)."

    if not cpf_valido(dados["cpf"]):
        erros["cpf"] = "CPF inválido. Confira os números digitados."
    else:
        consulta = db.select(Cliente.id).where(Cliente.cpf == dados["cpf"])
        if cliente_id is not None:
            consulta = consulta.where(Cliente.id != cliente_id)
        if db.session.execute(consulta).first():
            erros["cpf"] = "Já existe um cliente cadastrado com este CPF."

    if len(dados["telefone"]) not in (10, 11):
        erros["telefone"] = "Informe o telefone com DDD (10 ou 11 dígitos)."

    if dados["email"] and (len(dados["email"]) > 120 or not EMAIL_RE.match(dados["email"])):
        erros["email"] = "Informe um e-mail válido."

    if dados["endereco"] and len(dados["endereco"]) > 200:
        erros["endereco"] = "O endereço deve ter no máximo 200 caracteres."

    return dados, erros


def validar_pet(form):
    dados = {
        "cliente_id": para_inteiro(form.get("cliente_id")),
        "nome": texto(form, "nome"),
        "especie": enum_por_nome(Especie, form.get("especie")),
        "raca": texto(form, "raca") or None,
        "porte": enum_por_nome(Porte, form.get("porte")),
        "data_nascimento": para_data(form.get("data_nascimento")),
        "observacoes": texto(form, "observacoes") or None,
    }
    erros = {}

    if dados["cliente_id"] is None or db.session.get(Cliente, dados["cliente_id"]) is None:
        erros["cliente_id"] = "Selecione o tutor (cliente) responsável pelo pet."

    if not 1 <= len(dados["nome"]) <= 60:
        erros["nome"] = "Informe o nome do pet (até 60 caracteres)."

    if dados["especie"] is None:
        erros["especie"] = "Selecione a espécie."

    if dados["porte"] is None:
        erros["porte"] = "Selecione o porte."

    if dados["raca"] and len(dados["raca"]) > 60:
        erros["raca"] = "A raça deve ter no máximo 60 caracteres."

    if texto(form, "data_nascimento") and dados["data_nascimento"] is None:
        erros["data_nascimento"] = "Data de nascimento inválida."
    elif dados["data_nascimento"] and dados["data_nascimento"] > date.today():
        erros["data_nascimento"] = "A data de nascimento não pode estar no futuro."

    return dados, erros


def validar_servico(form, servico_id=None):
    dados = {
        "nome": texto(form, "nome"),
        "descricao": texto(form, "descricao") or None,
        "preco": para_decimal(form.get("preco")),
        "duracao_minutos": para_inteiro(form.get("duracao_minutos")),
        "ativo": form.get("ativo") in ("on", "1", "true", "True"),
    }
    erros = {}

    if not 3 <= len(dados["nome"]) <= 80:
        erros["nome"] = "Informe o nome do serviço (de 3 a 80 caracteres)."
    else:
        consulta = db.select(Servico.id).where(db.func.lower(Servico.nome) == dados["nome"].lower())
        if servico_id is not None:
            consulta = consulta.where(Servico.id != servico_id)
        if db.session.execute(consulta).first():
            erros["nome"] = "Já existe um serviço com este nome."

    if dados["descricao"] and len(dados["descricao"]) > 255:
        erros["descricao"] = "A descrição deve ter no máximo 255 caracteres."

    if dados["preco"] is None or dados["preco"] <= 0:
        erros["preco"] = "Informe um preço maior que zero."

    duracao = dados["duracao_minutos"]
    if duracao is None or not 15 <= duracao <= 480 or duracao % 15 != 0:
        erros["duracao_minutos"] = "A duração deve ser múltipla de 15 minutos (de 15 a 480)."

    return dados, erros


def validar_agendamento(form, agendamento_id=None, agora=None):
    """Valida um agendamento aplicando as regras RN03, RN04, RN05 e RN09."""
    agora = agora or datetime.now()
    erros = {}

    pet_id = para_inteiro(form.get("pet_id"))
    pet = db.session.get(Pet, pet_id) if pet_id else None
    if pet is None:
        erros["pet_id"] = "Selecione o pet."

    servico_id = para_inteiro(form.get("servico_id"))
    servico = db.session.get(Servico, servico_id) if servico_id else None
    if servico is None:
        erros["servico_id"] = "Selecione o serviço."
    elif not servico.ativo:
        erros["servico_id"] = "Este serviço está inativo e não pode ser agendado."  # RN09

    inicio = fim = None
    try:
        inicio = datetime.strptime(f"{texto(form, 'data')} {texto(form, 'hora')}", "%Y-%m-%d %H:%M")
    except ValueError:
        erros["data"] = "Informe uma data e um horário válidos."

    if inicio and servico and "servico_id" not in erros:
        fim = Agendamento.calcular_fim(inicio, servico.duracao_minutos)
        if inicio <= agora:
            erros["data"] = "Não é possível agendar em uma data/horário que já passou."  # RN03
        elif not dentro_do_expediente(inicio, fim):
            erros["hora"] = ("Fora do horário de funcionamento: segunda a sábado, das 08h às 18h "
                             f"(este serviço termina às {fim:%H:%M}).")  # RN05
        elif Agendamento.existe_conflito(inicio, fim, ignorar_id=agendamento_id):
            erros["hora"] = "Horário indisponível: já existe um agendamento nesse período."  # RN04

    dados = {
        "pet": pet,
        "servico": servico,
        "inicio": inicio,
        "fim": fim,
        "observacoes": texto(form, "observacoes") or None,
    }
    return dados, erros
