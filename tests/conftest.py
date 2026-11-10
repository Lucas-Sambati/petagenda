"""Configuração compartilhada dos testes automatizados (pytest)."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import Cliente, Especie, Perfil, Pet, Porte, Servico, Usuario
from config import TestConfig


@pytest.fixture
def app():
    """Aplicação com banco SQLite em memória e dois usuários de teste."""
    app = create_app(TestConfig)
    with app.app_context():
        admin = Usuario(nome="Admin Teste", email="admin@teste.com", perfil=Perfil.ADMIN)
        admin.definir_senha("senha123")
        atendente = Usuario(nome="Atendente Teste", email="atendente@teste.com", perfil=Perfil.ATENDENTE)
        atendente.definir_senha("senha123")
        db.session.add_all([admin, atendente])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    def _login(email="admin@teste.com", senha="senha123"):
        return client.post("/login", data={"email": email, "senha": senha}, follow_redirects=True)
    return _login


@pytest.fixture
def admin(client, login):
    """Cliente HTTP autenticado como Administrador."""
    login("admin@teste.com")
    return client


@pytest.fixture
def atendente(client, login):
    """Cliente HTTP autenticado como Atendente."""
    login("atendente@teste.com")
    return client


@pytest.fixture
def dados(app):
    """Um cliente com um pet e um serviço já cadastrados."""
    cliente = Cliente(nome="Maria Teste", cpf="52998224725", telefone="43999990000")
    pet = Pet(cliente=cliente, nome="Rex", especie=Especie.CAO, porte=Porte.MEDIO)
    servico = Servico(nome="Banho", preco=Decimal("60.00"), duracao_minutos=60)
    db.session.add_all([cliente, pet, servico])
    db.session.commit()
    return {"cliente": cliente, "pet": pet, "servico": servico}


@pytest.fixture
def dia_util():
    """Retorna o n-ésimo próximo dia de funcionamento (segunda a sábado)."""
    def _dia_util(n=1):
        dia = date.today()
        while n:
            dia += timedelta(days=1)
            if dia.weekday() != 6:
                n -= 1
        return dia
    return _dia_util


def texto(resposta):
    return resposta.get_data(as_text=True)
