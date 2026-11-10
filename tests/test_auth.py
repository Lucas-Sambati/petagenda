"""Testes do UC01 - Autenticar usuário."""
from app.extensions import db
from app.models import Usuario
from conftest import texto


def test_login_com_credenciais_validas(login):
    resposta = login("admin@teste.com", "senha123")
    assert resposta.status_code == 200
    assert "Bem-vindo(a), Admin Teste!" in texto(resposta)


def test_login_com_senha_incorreta(client, login):
    resposta = login("admin@teste.com", "senha-errada")
    assert "E-mail ou senha inválidos." in texto(resposta)
    with client.session_transaction() as sessao:
        assert "usuario_id" not in sessao


def test_rotas_protegidas_exigem_login(client):
    for url in ["/", "/clientes/", "/pets/", "/servicos/", "/agendamentos/"]:
        resposta = client.get(url)
        assert resposta.status_code == 302
        assert "/login" in resposta.headers["Location"]


def test_logout_encerra_a_sessao(client, login):
    login()
    assert client.get("/").status_code == 200
    client.post("/logout")
    assert client.get("/").status_code == 302


def test_senha_armazenada_somente_como_hash(app):
    usuario = db.session.scalar(db.select(Usuario).where(Usuario.email == "admin@teste.com"))
    assert usuario.senha_hash != "senha123"
    assert usuario.verificar_senha("senha123")
    assert not usuario.verificar_senha("outra-senha")


def test_usuario_inativo_nao_consegue_entrar(app, login):
    usuario = db.session.scalar(db.select(Usuario).where(Usuario.email == "atendente@teste.com"))
    usuario.ativo = False
    db.session.commit()
    assert "E-mail ou senha inválidos." in texto(login("atendente@teste.com", "senha123"))
