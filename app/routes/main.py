"""Painel inicial com o resumo do dia (RF20)."""
from datetime import date, datetime, time, timedelta

from flask import Blueprint, render_template

from ..extensions import db
from ..models import Agendamento, Cliente, Pet, Servico, StatusAgendamento
from ..seguranca import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def painel():
    inicio_hoje = datetime.combine(date.today(), time.min)
    fim_hoje = inicio_hoje + timedelta(days=1)

    agenda_hoje = db.session.scalars(
        db.select(Agendamento)
        .where(Agendamento.data_hora_inicio >= inicio_hoje,
               Agendamento.data_hora_inicio < fim_hoje)
        .order_by(Agendamento.data_hora_inicio)
    ).all()

    proximos = db.session.scalars(
        db.select(Agendamento)
        .where(Agendamento.status == StatusAgendamento.AGENDADO,
               Agendamento.data_hora_inicio >= fim_hoje)
        .order_by(Agendamento.data_hora_inicio)
        .limit(5)
    ).all()

    totais = {
        "clientes": db.session.scalar(db.select(db.func.count(Cliente.id))),
        "pets": db.session.scalar(db.select(db.func.count(Pet.id))),
        "servicos": db.session.scalar(db.select(db.func.count(Servico.id)).where(Servico.ativo.is_(True))),
        "hoje": len(agenda_hoje),
    }
    return render_template("painel.html", totais=totais, agenda_hoje=agenda_hoje, proximos=proximos)
