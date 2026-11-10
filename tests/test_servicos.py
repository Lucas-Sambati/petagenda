"""Testes do UC04 - Manter serviços."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import Agendamento, Servico
from conftest import texto

NOVO_SERVICO = {"nome": "Tosa na tesoura", "descricao": "Tosa artesanal", "preco": "95,50",
                "duracao_minutos": "90", "ativo": "on"}


def test_admin_cadastra_servico(admin):
    resposta = admin.post("/servicos/novo", data=NOVO_SERVICO, follow_redirects=True)
    assert "cadastrado com sucesso" in texto(resposta)
    servico = db.session.scalar(db.select(Servico).where(Servico.nome == "Tosa na tesoura"))
    assert servico.preco == Decimal("95.50")
    assert servico.duracao_minutos == 90 and servico.ativo


def test_atendente_consulta_mas_nao_altera_servicos(atendente, dados):
    assert atendente.get("/servicos/").status_code == 200
    assert atendente.get("/servicos/novo").status_code == 403
    assert atendente.post("/servicos/novo", data=NOVO_SERVICO).status_code == 403
    assert atendente.post(f"/servicos/{dados['servico'].id}/excluir").status_code == 403


def test_validacao_de_preco_e_duracao(admin):
    resposta = admin.post("/servicos/novo", data={**NOVO_SERVICO, "preco": "0", "duracao_minutos": "20"})
    pagina = texto(resposta)
    assert "Informe um preço maior que zero." in pagina
    assert "múltipla de 15 minutos" in pagina


def test_nome_de_servico_unico(admin, dados):
    resposta = admin.post("/servicos/novo", data={**NOVO_SERVICO, "nome": "banho"})
    assert "Já existe um serviço com este nome." in texto(resposta)


def test_alterar_servico(admin, dados):
    servico_id = dados["servico"].id
    admin.post(f"/servicos/{servico_id}/editar",
               data={"nome": "Banho", "preco": "65.00", "duracao_minutos": "45", "descricao": ""})
    db.session.expire_all()
    servico = db.session.get(Servico, servico_id)
    assert servico.preco == Decimal("65.00")
    assert servico.duracao_minutos == 45
    assert servico.ativo is False  # checkbox desmarcado = inativo


def test_excluir_servico_sem_agendamentos(admin, dados):
    resposta = admin.post(f"/servicos/{dados['servico'].id}/excluir", follow_redirects=True)
    assert "excluído com sucesso" in texto(resposta)
    assert db.session.scalar(db.select(db.func.count(Servico.id))) == 0


def test_nao_exclui_servico_usado_em_agendamentos(admin, dados):
    inicio = datetime.combine(date.today() - timedelta(days=1), time(9, 0))
    db.session.add(Agendamento(pet=dados["pet"], servico=dados["servico"], usuario_id=1,
                               data_hora_inicio=inicio, data_hora_fim=inicio + timedelta(hours=1),
                               valor=dados["servico"].preco))
    db.session.commit()
    resposta = admin.post(f"/servicos/{dados['servico'].id}/excluir", follow_redirects=True)
    assert "já foi usado em agendamentos" in texto(resposta)
    assert db.session.scalar(db.select(db.func.count(Servico.id))) == 1
