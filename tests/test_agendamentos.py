"""Testes do UC05 - Manter agendamentos (regras RN03 a RN07 e RN09)."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import Agendamento, Servico, StatusAgendamento
from conftest import texto


def _form(dados, dia, hora="10:00", **extra):
    return {"pet_id": dados["pet"].id, "servico_id": dados["servico"].id,
            "data": dia.isoformat(), "hora": hora, "observacoes": "", **extra}


def _agendamentos():
    db.session.expire_all()
    return db.session.scalars(db.select(Agendamento).order_by(Agendamento.id)).all()


def test_cadastrar_agendamento_calcula_termino_e_valor(admin, dados, dia_util):
    dia = dia_util(1)
    resposta = admin.post("/agendamentos/novo", data=_form(dados, dia, "10:00"), follow_redirects=True)
    assert "Agendamento confirmado" in texto(resposta)
    [agendamento] = _agendamentos()
    assert agendamento.data_hora_fim == datetime.combine(dia, time(11, 0))  # RN06
    assert agendamento.valor == Decimal("60.00")
    assert agendamento.status == StatusAgendamento.AGENDADO
    assert agendamento.usuario.email == "admin@teste.com"


def test_nao_agenda_em_data_passada(admin, dados):
    ontem = date.today() - timedelta(days=1)
    resposta = admin.post("/agendamentos/novo", data=_form(dados, ontem))
    assert "já passou" in texto(resposta)  # RN03
    assert _agendamentos() == []


def test_nao_agenda_fora_do_horario_de_funcionamento(admin, dados, dia_util):
    dia = dia_util(1)
    domingo = next(date.today() + timedelta(days=i) for i in range(1, 8)
                   if (date.today() + timedelta(days=i)).weekday() == 6)
    for data_teste, hora in [(dia, "07:30"), (dia, "17:30"), (domingo, "10:00")]:
        resposta = admin.post("/agendamentos/novo", data=_form(dados, data_teste, hora))
        assert "Fora do horário de funcionamento" in texto(resposta)  # RN05
    assert _agendamentos() == []


def test_nao_agenda_com_conflito_de_horario(admin, dados, dia_util):
    dia = dia_util(1)
    admin.post("/agendamentos/novo", data=_form(dados, dia, "10:00"))
    resposta = admin.post("/agendamentos/novo", data=_form(dados, dia, "10:30"))
    assert "Horário indisponível" in texto(resposta)  # RN04
    resposta = admin.post("/agendamentos/novo", data=_form(dados, dia, "11:00"), follow_redirects=True)
    assert "Agendamento confirmado" in texto(resposta)  # começa quando o anterior termina
    assert len(_agendamentos()) == 2


def test_cancelamento_libera_o_horario(admin, dados, dia_util):
    dia = dia_util(1)
    admin.post("/agendamentos/novo", data=_form(dados, dia, "14:00"))
    [agendamento] = _agendamentos()
    resposta = admin.post(f"/agendamentos/{agendamento.id}/status", data={"acao": "cancelar"}, follow_redirects=True)
    assert "cancelado" in texto(resposta)
    resposta = admin.post("/agendamentos/novo", data=_form(dados, dia, "14:00"), follow_redirects=True)
    assert "Agendamento confirmado" in texto(resposta)


def test_remarcar_agendamento(admin, dados, dia_util):
    dia = dia_util(2)
    admin.post("/agendamentos/novo", data=_form(dados, dia, "09:00"))
    [agendamento] = _agendamentos()
    # mantém o mesmo período (não pode conflitar consigo mesmo) e depois remarca
    resposta = admin.post(f"/agendamentos/{agendamento.id}/editar", data=_form(dados, dia, "09:00"), follow_redirects=True)
    assert "alterado com sucesso" in texto(resposta)
    admin.post(f"/agendamentos/{agendamento.id}/editar", data=_form(dados, dia, "15:15", observacoes="Remarcado"))
    [agendamento] = _agendamentos()
    assert agendamento.data_hora_inicio == datetime.combine(dia, time(15, 15))
    assert agendamento.data_hora_fim == datetime.combine(dia, time(16, 15))
    assert agendamento.observacoes == "Remarcado"


def test_concluir_agendamento_e_bloquear_alteracoes(admin, dados, dia_util):
    admin.post("/agendamentos/novo", data=_form(dados, dia_util(1), "10:00"))
    [agendamento] = _agendamentos()
    admin.post(f"/agendamentos/{agendamento.id}/status", data={"acao": "concluir"})
    [agendamento] = _agendamentos()
    assert agendamento.status == StatusAgendamento.CONCLUIDO
    # RN07: concluído não pode ser cancelado nem editado
    resposta = admin.post(f"/agendamentos/{agendamento.id}/status", data={"acao": "cancelar"}, follow_redirects=True)
    assert "Somente agendamentos com status Agendado" in texto(resposta)
    resposta = admin.get(f"/agendamentos/{agendamento.id}/editar", follow_redirects=True)
    assert "Somente agendamentos com status Agendado" in texto(resposta)
    assert _agendamentos()[0].status == StatusAgendamento.CONCLUIDO


def test_excluir_agendamento(admin, dados, dia_util):
    admin.post("/agendamentos/novo", data=_form(dados, dia_util(1), "10:00"))
    [agendamento] = _agendamentos()
    resposta = admin.post(f"/agendamentos/{agendamento.id}/excluir", follow_redirects=True)
    assert "excluído com sucesso" in texto(resposta)
    assert _agendamentos() == []


def test_valor_nao_muda_quando_o_preco_do_servico_muda(admin, dados, dia_util):
    admin.post("/agendamentos/novo", data=_form(dados, dia_util(1), "10:00"))
    admin.post(f"/servicos/{dados['servico'].id}/editar",
               data={"nome": "Banho", "preco": "80.00", "duracao_minutos": "60", "ativo": "on"})
    [agendamento] = _agendamentos()
    assert agendamento.servico.preco == Decimal("80.00")
    assert agendamento.valor == Decimal("60.00")  # RN06: preço do momento do agendamento


def test_servico_inativo_nao_pode_ser_agendado(admin, dados, dia_util):
    servico = db.session.get(Servico, dados["servico"].id)
    servico.ativo = False
    db.session.commit()
    resposta = admin.post("/agendamentos/novo", data=_form(dados, dia_util(1), "10:00"))
    assert "inativo" in texto(resposta)  # RN09
    assert _agendamentos() == []


def test_filtrar_agenda_por_data_e_status(admin, dados, dia_util):
    dia1, dia2 = dia_util(1), dia_util(2)
    admin.post("/agendamentos/novo", data=_form(dados, dia1, "10:00", observacoes="primeiro"))
    admin.post("/agendamentos/novo", data=_form(dados, dia2, "10:00"))
    primeiro, segundo = _agendamentos()
    admin.post(f"/agendamentos/{segundo.id}/status", data={"acao": "cancelar"})

    pagina_dia1 = texto(admin.get(f"/agendamentos/?data={dia1.isoformat()}"))
    assert dia1.strftime("%d/%m/%Y") in pagina_dia1
    assert dia2.strftime("%d/%m/%Y") not in pagina_dia1.split("<tbody>")[1]

    pagina_cancelados = texto(admin.get("/agendamentos/?status=CANCELADO"))
    corpo = pagina_cancelados.split("<tbody>")[1]
    assert dia2.strftime("%d/%m/%Y") in corpo and dia1.strftime("%d/%m/%Y") not in corpo
