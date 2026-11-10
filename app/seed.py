"""Dados de exemplo para demonstração do sistema.

São inseridos automaticamente na primeira execução (banco vazio) ou com o
comando ``flask --app run reset-db``. As datas dos agendamentos são
calculadas a partir do dia atual, para que a agenda sempre tenha dados.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from .extensions import db
from .models import (Agendamento, Cliente, Especie, Perfil, Pet, Porte, Servico,
                     StatusAgendamento, Usuario)


def dia_util(base, deslocamento):
    """Retorna o n-ésimo dia de funcionamento (segunda a sábado) a partir de ``base``."""
    passo = 1 if deslocamento >= 0 else -1
    dia, restantes = base, abs(deslocamento)
    while restantes:
        dia += timedelta(days=passo)
        if dia.weekday() != 6:  # domingo: pet shop fechado
            restantes -= 1
    return dia


def _agendar(pet, servico, usuario, dia, hora, minuto=0, status=StatusAgendamento.AGENDADO):
    inicio = datetime.combine(dia, time(hora, minuto))
    return Agendamento(pet=pet, servico=servico, usuario=usuario,
                       data_hora_inicio=inicio,
                       data_hora_fim=Agendamento.calcular_fim(inicio, servico.duracao_minutos),
                       valor=servico.preco, status=status)


def popular_banco(forcar=False):
    """Insere usuários, serviços, clientes, pets e agendamentos de exemplo."""
    if not forcar and db.session.scalar(db.select(db.func.count(Usuario.id))):
        return False

    admin = Usuario(nome="Administrador", email="admin@petagenda.com", perfil=Perfil.ADMIN)
    admin.definir_senha("admin123")
    atendente = Usuario(nome="Ana Lima", email="atendente@petagenda.com", perfil=Perfil.ATENDENTE)
    atendente.definir_senha("atendente123")

    banho = Servico(nome="Banho", descricao="Banho com shampoo neutro, secagem e escovação.",
                    preco=Decimal("60.00"), duracao_minutos=60)
    tosa = Servico(nome="Tosa higiênica", descricao="Aparo dos pelos das patas, rosto e região íntima.",
                   preco=Decimal("45.00"), duracao_minutos=30)
    completo = Servico(nome="Banho e tosa completa", descricao="Banho completo com tosa na máquina ou tesoura.",
                       preco=Decimal("120.00"), duracao_minutos=120)
    hidratacao = Servico(nome="Hidratação de pelos", descricao="Máscara hidratante para pelos ressecados.",
                         preco=Decimal("50.00"), duracao_minutos=30)
    unhas = Servico(nome="Corte de unhas", descricao="Corte e lixamento das unhas.",
                    preco=Decimal("20.00"), duracao_minutos=15)

    mariana = Cliente(nome="Mariana Souza", cpf="52998224725", telefone="43991234567",
                      email="mariana.souza@example.com", endereco="Rua das Flores, 120 - Londrina/PR")
    carlos = Cliente(nome="Carlos Oliveira", cpf="11144477735", telefone="43998765432",
                     email="carlos.oliveira@example.com", endereco="Av. Higienópolis, 1500 - Londrina/PR")
    juliana = Cliente(nome="Juliana Pereira", cpf="39053344705", telefone="4333221100",
                      endereco="Rua Sergipe, 45 - Londrina/PR")

    thor = Pet(cliente=mariana, nome="Thor", especie=Especie.CAO, raca="Golden Retriever",
               porte=Porte.GRANDE, data_nascimento=date(2021, 3, 15),
               observacoes="Dócil, mas tem medo de secador.")
    bob = Pet(cliente=mariana, nome="Bob", especie=Especie.CAO, raca="Poodle",
              porte=Porte.MEDIO, data_nascimento=date(2019, 8, 2))
    mel = Pet(cliente=carlos, nome="Mel", especie=Especie.GATO, raca="SRD (sem raça definida)",
              porte=Porte.PEQUENO, data_nascimento=date(2022, 1, 10))
    luna = Pet(cliente=juliana, nome="Luna", especie=Especie.CAO, raca="Shih-tzu",
               porte=Porte.PEQUENO, data_nascimento=date(2023, 6, 20),
               observacoes="Alergia a shampoo perfumado.")

    hoje = date.today()
    ontem_util, amanha_util, depois_util = dia_util(hoje, -1), dia_util(hoje, 1), dia_util(hoje, 2)
    agendamentos = [
        _agendar(thor, banho, atendente, ontem_util, 10, status=StatusAgendamento.CONCLUIDO),
        _agendar(mel, unhas, atendente, ontem_util, 15, status=StatusAgendamento.CANCELADO),
        _agendar(luna, completo, atendente, amanha_util, 9),
        _agendar(mel, unhas, atendente, amanha_util, 11),
        _agendar(bob, banho, admin, amanha_util, 14),
        _agendar(thor, hidratacao, atendente, depois_util, 10, 30),
    ]
    if hoje.weekday() != 6:  # se hoje o pet shop abre, a agenda do dia também tem dados
        agendamentos += [
            _agendar(luna, tosa, atendente, hoje, 8, status=StatusAgendamento.CONCLUIDO),
            _agendar(bob, unhas, atendente, hoje, 17, 30),
        ]

    db.session.add_all([admin, atendente, banho, tosa, completo, hidratacao, unhas,
                        mariana, carlos, juliana, thor, bob, mel, luna, *agendamentos])
    db.session.commit()
    return True
